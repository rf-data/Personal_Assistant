# C26-CS50P-NATIVE-ADMISSION: Vertrag und Grenzen

Reviewkandidat, Gesamtstatus HOLD bis Review/Integration und Hostabnahme. Keine
C26-Produktionsfreigabe. Der bisherige v1/v2-Gatevertrag bleibt erhalten.

## Entscheidung

Der vorhandene C16-Controller unterstützt lokale Aufrufe und feste Offline-
Workflows, aber kein SSH-Identitätsmodell und keine einzelne zeitgebundene native
Freigabe. C26-v2 setzt deploymentbezogene UI/API/Worker-/Containerbelege voraus.
`execution_enabled=true` oder ein C26-Testkoordinator würden diesen Bedarf nicht
sicher erfüllen. Deshalb eigener expliziter Scope `c26-native-v1`, mit weiterhin
mandatory `deployment_gate_required=true`. Kein bestehender v2-Workspace wird
migriert oder als nativer Workspace übernommen.

`Settings` validiert für diesen Scope: eine reale unprivilegierte UID, keine
Bearer-Identitäten, CS50P (`cs50_python`) und ausschließlich versiegelte HTML/PDF-
Workflowkataloge, maximal drei Katalogeinträge, eine parallele/queued Ausführung,
keine Index-/Importjobs, keine separaten PDF-APIjobs und keinen Testkoordinator.
`native_mode=ssh-runtime` lehnt synthetischen Workflowursprung ab.
`offline-test` ist ein ausdrücklich anderer Scope; der normale CLI-/systemd-Start
verlangt ssh-runtime, synthetischer Start benötigt zusätzlich --offline-test; dessen Konfiguration, Queue und
Freigaben dürfen nicht auf den Host kopiert werden. Testgrants, Dummy-Witnesses und
Testtoken sind keine Runtime-Admission.

## Identität und Vertrauen

Der tatsächliche Prozess benötigt `getuid()==geteuid()==native_uid>0` und einen
lokalen passwd-Eintrag. Sein C16-Subject ist deterministisch `uid_<UID>`, Rolle
operator, Kurs ausschließlich CS50P. Die Authentifizierung erfolgt durch den
vorgelagerten VPN-/OpenSSH-Schlüssellogin des einzigen Betreibers und die enge
sudo-Regel zur dedizierten Dienst-UID. Die Anwendung behauptet keinen SSH-Nachweis
aus einer Umgebungsvariable. Die UID wird bei Installation mit `id -u cs50p`
gebunden; Beispiel-UID 1000 ist kein Runtime-Identitätsbeleg.

Vertrauensgrenze sind Linux-Account/root, installierter Code und private Specs/
Daten. Ein Angreifer mit Schreibrecht als derselbe Betreiber kann Code, Freigaben
und Daten ändern; das ist keine Sicherheitsgrenze gegen bösartigen Betreiber/root.
Andere lokale Benutzer erhalten keine Schreibrechte. Quellenfreigaben sind
Betreibererklärungen, kein kryptographischer Nachweis von Herkunft/Urheberrechten.
Der Host darf keine frei zugängliche sudo-Shell oder geteilte Dienst-UID anbieten.

## Ablauf und Bindung

1. Download nutzt unverändert den eingeschränkten MVP-Downloader, ohne öffentliche
   API: Quellenallowlist, TLS/DNS-Pinning, Transferlimits, Prüfsummen und Reports.
2. `cs50_batch seal` erstellt einen neuen Katalog mit Rohdaten, Downloadreceipt,
   Quellenfreigabe und Discovery-/Workflowdateien. Native Policy prüft deren
   Hashes, konkrete Quellen-/Prozessfreigabe und zulässige HTML/PDF-Quellen erneut.
3. `init --confirm` bindet Code-unabhängige Specs und Limits in einem **leeren**
   privaten Workspace; bestehende Queue, Fremddateien oder Gates werden abgelehnt.
   Die Initialisierung erteilt keinerlei Jobfreigabe.
4. `review` prüft echte Katalogbytes und vorherigen Workflowstatus und liefert eine
   kanonische review_id. `approve --review-id ... --confirm` prüft sie erneut und
   erstellt über `Controller.create(start=False)` genau einen C16-Job und einen
   exklusiv neu geschriebenen Grant. Er bindet kanonischen Preview/Parameter,
   OS-UID, Job-ID, Zufallsnonce, volle Settings und die **Dateibytes** von Config/
   Limits, Kataloghashes und installierte Python-Quellen in src/ und scripts/.
   Auch reine JSON-Whitespaceänderungen an Specs machen den Grant ungültig.
   TTL 1–600 s, Standard 300 s; UTC-Zeit vor approved_at/ab expires_at ist ungültig.
5. `run --job-id ...` prüft alles, schreibt den fsync-gesicherten exklusiven
   Verbrauchsbeleg **vor** jedem Executorstart und startet `CapacityExecutor`.
   Nur dieser Scope darf `Controller.start`/Store-Queueübergang auslösen. Normale
   APIaufrufe oder nackte Store-/Executoraufrufe besitzen diese Authority nicht.
6. Executor, Queue, Guardian, fester Offlineadapter und Workflowengine bleiben
   C16. Native Dispatch prüft Grant/Settings/Inputs erneut und lässt nur die
   freigegebene Job-ID zu. Der Guardian verlangt den passenden Verbrauchsbeleg,
   seinen tatsächlichen Elternprozess und den aktiven C16-Workerlock, bevor er
   den Adapter startet. Ein Protokolldowngrade wird anhand des Workspace-Markers
   ebenfalls abgewiesen. Native/v2-/Testkoordinatorartefakte dürfen nicht mischen.

Freigabe und Verbrauch sind getrennte persistente Dateien unter native-grants/;
C16-Jobs und Events bleiben in jobs.sqlite3. Ein Crash zwischen Queueanlage und
Grantpublikation hinterlässt einen blockierenden created-Job; ein Crash nach
Verbrauch erlaubt keinen Wiederanlauf dieses Grants. Unvollständige Dateien und
unbekannte Daten werden erhalten, niemals als Freigabe übernommen.

## Lebensdauer, Parallelität und Abbruch

Der native Admissionlock serialisiert neue Freigaben. Alle nichtterminalen Jobs,
auch created, blockieren weitere Freigaben. Der bestehende exklusive worker.lock
und max_parallel=1 verhindern parallele Worker. Ein Dienstaufruf verarbeitet
höchstens genau den genehmigten Job und endet anschließend. Kein Pollingscheduler,
Timer, Restart oder automatischer Rebootstart wird installiert.

Grantablauf, fehlende/ungültige Specs oder geänderte Rohdaten verhindern Dispatch;
bei Verlust während der Ausführung schließt der Supervisor den Guardian und
unterbricht den Job. C16 beendet/reapt Prozessgruppen vor terminaler Bestätigung.
`cancel` verwendet C16-Cancel bzw. die C16-Übergänge eines undispatchten created-
Jobs. Ein expired Grant blockiert die kontrollierte Abbruchanforderung nicht.
`recover --confirm` ist eine manuelle Reconciliation für beendete Worker: exklusiver
Workerlock, vorhandener Guardian-Lifecyclelock (bis 8 s warten), niemals gespeicherte
PIDs signalisieren. Unbekannter Jobordner ohne Lifecyclebeleg oder Quarantäne
bleiben HOLD. Betriebssystem-/systemd-Stop bleibt der Rückweg bei beschädigten Specs.

Resume verlangt neuen Review, neuen Grant und neue Job-ID mit previous_run_id;
terminal completed wird nicht erneut freigegeben. C16 validiert den Vorgänger und
vorhandene Stufenergebnisse. Abgebrochene/unterbrochene Jobs werden nie automatisch
wiederholt. Ein anderer Katalog/andere Specs benötigen einen neuen leeren Scope;
keine Änderung der Enrollmentdatei als „Reparatur“.

## Ressourcen und Ergebnisse

Limits: >=5 GiB freie Reserve, <=512 MiB Jobs, <=128 MiB Katalogbudget, <=64 MiB
Archivbudget, <=3 Materialien. Das sind konservative Prüfungen, keine Diskquotas.
Der native Dienst begrenzt CPU auf 100%, RAM 1 GiB, Swap 0, Tasks 128, temporären
Speicher 128 MiB und Laufzeit 120 s, ohne Netzwerk. Der C16-Workflowadapter besitzt
zusätzlich feste CPU/Adressraum/Datei/FD/NPROC-Limits und eine 90-s-Timeoutgrenze.
Ein direkter foreground-CLI-Test ersetzt keine Host-/cgroup-Abnahme.

Grants, Verbrauchsbelege, Queueevents, Workflowzustand und Ergebnisse bleiben
privat erhalten. `result` prüft den C16-Ergebnisdigest und alle im Workflowreport
referenzierten Ergebnisdateien. Quarantäne oder beschädigte Ergebnisse blockieren
Abruf. `preflight` öffnet keine SQLite-Verbindung; es prüft nur Specs, Katalog und
Queueheader. Status/Review/Result verwenden read-only SQLite-Verbindungen; SQLite
kann dafür flüchtige WAL/SHM-Dateien anlegen. Sie ändern keine Jobs oder Heartbeats.

Keine Freigabe für LLM-/Audio-/Vision-/Knowledgeverarbeitung. Keine Streamlit-/OIDC-
Abhängigkeit, kein öffentlicher Listener und keine vollständige C26-Freigabe.
