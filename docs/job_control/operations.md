# Lokaler Betrieb, Schutz und Wiederanlauf

## Serverkonfiguration

Explizite externe JSON-Datei, maximal 1 MiB; kein implizites .env-Laden.
Versioniertes Settings-Modell: src/job_control/models.py.
Maschinenlesbare Schemas stehen im [Vertragssnapshot](contract.v1.json).

Erforderlich: root als neues privates externes Jobverzeichnis, außerhalb des
Repositorys und getrennt von allen zugelassenen Inputs. Besitzer ist derselbe
dedizierte unprivilegierte Serviceuser für API/Executor; root muss Modus 0700
haben. SQLite wird neu mit 0600 erstellt. Keine vorhandene Anwendung-/Knowledge-
Datenbank darf verwendet oder als Jobdatenbank adoptiert werden.

Identities enthalten subject, role (viewer/operator), courses und token_sha256.
Token mindestens 32 urlsafe Zeichen aus einer starken Zufallsquelle
(z. B. secrets.token_urlsafe(32)); keine Passwörter als niedrigentropische Tokens.
Nur der SHA256-Verifier gehört in die geschützte Serverkonfiguration.
Klartexttoken außerhalb Git in Secretmanager/Clientspeicher halten.
Tokens werden weder in Jobdaten noch Logs gespeichert. Tokenrotation mit
demselben Subject erhält Jobidentität; Rollen-/Scopeänderungen erfordern einen
bewussten Neustart beider Services, kein automatischer Config-Reload.

execution_enabled=false ist der Default. Auch bei enabled brauchen Create/Start
einen echten aktuellen Executorheartbeat. Bei fehlender Konfiguration gibt es
keinen öffentlichen, anonym startbaren Controller. --port erlaubt nur
unprivilegierte lokale Ports; keine freigegebene Bindadresse aus Nutzereingaben.

Limits: max_jobs 100 (hart maximal 1000), max_queued 8 (max. 32),
max_parallel 1 (max. 2), höchstens ein Job je Process-ID.
Volle Kapazität führt zu 503, nicht zu einer unbegrenzten Warteschlange.
Keine automatische Löschung/Rotation der Jobhistorie.
Ein Job kann bis 32 MiB Inputkopien und 8 MiB Ergebnis behalten; Speicherbudget
und archivierte externe Arbeitsbereiche bewusst planen.

## Zugelassene Inputs

catalog ist eine serverseitige Map von Identifiern auf CatalogEntry:
kind manifest oder material_bundle, absoluter root, files als relative
Pfad→SHA256-Map, roles und course_ids. Maximal 32 Einträge, 128 Dateien je Eintrag,
8 MiB pro Datei/32 MiB gesamt. Keine Symlinks, Traversal oder Spezialdateien.

Manifest-Rollen: manifest. Alle referenzierten HTML-Seiten müssen ausdrücklich
in files enthalten sein. Das vorhandene FixtureManifest verifiziert zusätzlich
Original-URLs, Rollen und Seitenhashes. Keine verlinkte Ressource wird geladen.

Ein read-only Startup-Preflight bereitet die vorhandenen Plan-/Scopeindizes vor,
bevor der HTTP-Server Anfragen annimmt. Preview/Create/Start prüfen die freigegebenen
Hashes und diese Indizes, rufen aber keinen Planungsrunner innerhalb einer HTTP-
Anfrage auf. Die tatsächliche Planerstellung und Veröffentlichung geschieht im
begrenzten Adapterprozess. Bei geänderten Katalogen beide Services neu starten.

Materialbundle-Rollen: plan, normalized, receipt, raw. Relative Pfade/Layout der
bestehenden Materialpipeline erhalten; Bildartefakte bei Bedarf zusätzlich als
Dateien zulassen. Keine Umbenennung von Receiptpfaden. CatalogEntry wird mit
der angenommenen Preview persistiert. Ein später veränderter/revokierter
Katalog oder fehlende/falsche Bytes verhindert Dispatch/Adapterausführung.
Inputs liegen in betreibereigenen read-only freigegebenen Verzeichnissen;
schreibende Angreifer im Quellroot sind keine unterstützte Trustgrenze.

Bei Ausführung werden ausschließlich deklarierte, hashgeprüfte Bytes in ein
neues jobs/<job_id>/inputs kopiert. Die Runner bekommen nur diesen Snapshot.
Ergebnisse landen außerhalb davon in jobs/<job_id>/results.
Die vorhandenen Publish-/Planungs-/Quality-Funktionen bleiben unverändert.
Es werden keine Quellbytes korrigiert und keine alten Ergebnisse überschrieben.

## Ausführung und Ressourcen

HTTP und Executor laufen getrennt. SQLite WAL/BEGIN IMMEDIATE und
Unique(owner,request_key) schützen parallele Starts. Genau ein Executor besitzt
den OS-flock worker.lock. Ein API-Neustart startet/stoppt keine Kinder.
Ein eigener begrenzt wartender Bootstrap-flock serialisiert Schema-/WAL-
Initialisierung aus gleichzeitig startenden API-/Worker-Prozessen. Erst nach
abgewiesenen Fremd-/Versionsschemata wird das eigene Jobjournal auf WAL gesetzt.

Der Supervisor startet ausschließlich src.job_control.guardian. Dieser startet
ausschließlich src.job_control.adapter_worker mit root/job_id/Parentbezug.
Keine Shell, shell=True, Skript-/Modulparameter aus HTTP oder Shellkonfiguration.

Die beiden Defaultadapter: 30 s Walltime, 20 s CPU, 768 MiB Adressraum,
8 MiB Dateigröße, 64 Deskriptoren, 32 Tasks je UID, Core-Dumps aus.
Die optionalen PDF-/Workflowpfade verwenden 512 Tasks je UID: Linux zählt auch
alle anderen Threads desselben Benutzers. Die feste Workerstruktur und die
Jobparallelitätsgrenzen bleiben bestehen; [C19-Policy](pdf_lifecycle.md).
Grenzen stehen in der Registry, sind nicht von Jobparametern erweiterbar.
RLIMIT_NPROC ist pro UID und unter root nicht vollständig wirksam; daher
dedizierten Nicht-root-User und später zusätzliche cgroup-/Servicegrenzen nutzen.
Dies ist keine Sandbox für beliebigen feindlichen Python-Code: solche Jobs
werden gar nicht akzeptiert. Beide freigegebenen Runner sind offline; zusätzlich
blockiert der Adapter Python-Socketverbindungen und erhält keine geerbten
API-/Cloud-/Proxy-/User-Environment-Secrets.

Logs sind persistierte strukturierte Zustandsereignisse, keine unbegrenzten
Runnerdateien. Beliebiges stdout/stderr wird verworfen, nicht ungeprüft
redigiert weitergereicht. Die C10-Ergebnisdatei enthält detaillierte Findings.
API-Fehler/Ereignisse enthalten feste Meldungen und begrenzte technische
Exceptionklassennamen, keine Exceptionwerte oder Quellinhalte.

## Abbruch und Wiederanlauf

Cancel speichert zuerst cancel_requested. Nur der Executor/Guardian bestätigt
cancelled nach Ende des tatsächlich zugeordneten Payloads samt Prozessgruppe.
TERM, kurze Gracephase, danach KILL der weiterhin eigenen Gruppe. Der direkte
Payload bleibt bis zum Cleanup unreaped; seine PID kann dabei nicht als fremde
Prozessgruppe wiederverwendet werden. Linux-Subreaper sammelt eigene verwaiste
Nachfahren ein. Keine gespeicherten PIDs werden nach Neustart zum Kill benutzt.

Linux Parent-death-Signale sichern auch das Bootstrapfenster vor exec. Stirbt der
Supervisor, räumt der noch laufende Guardian seine Payloadgruppe auf; endet der
Guardian unerwartet, schützt zusätzlich das Parent-death-Signal des festen
Payloads. Normale API-Neustarts lassen all dies unberührt.

Linux-Verträge: [Parent-death-Signal](https://man7.org/linux/man-pages/man2/PR_SET_PDEATHSIG.2const.html)
und [Child-Subreaper](https://man7.org/linux/man-pages/man2/PR_SET_CHILD_SUBREAPER.2const.html).

Beim Executorstart: aktive Vorgänge über deren Lifecycle-flock aufräumen lassen,
dann nicht terminale alte Claims als interrupted markieren. Queued-Aufträge
dürfen erst danach und nach erneuter aktueller Autorisierung ausgeführt werden.
Completed/failed/cancelled/interrupted werden nie automatisch erneut ausgeführt.
Ein queued-Cancel ohne jemals gestarteten Prozess wird ausdrücklich bestätigt.

Nicht bestätigtes Cleanup, unerwarteter Guardianverlust oder interne
Kontrollfehler erzeugen eine persistente quarantine-Datei und stoppen weitere
Starts/Dispatches. Kein Erfolg und kein automatischer Retry werden behauptet.
Ein neuer Executor verweigert in diesem Fall den Start. Betreiber müssen den
dedizierten Service vollständig kontrolliert stoppen, die eigene Prozess-/Datei-
Situation prüfen und erst nach belegtem Ende aller zugehörigen Ausführungen die
Sperre bewusst aufheben. Kein automatisches Löschen oder Kill anhand alter PID.
SIGKILL/OS-Ausfälle ganzer Prozessbäume erfordern zusätzlich Plattform-/cgroup-
Überwachung; die lokalen Grenzen ersetzen keinen Produktions-Supervisor.

SQLite-Schema v1: fremde Tabellen, unbekannte Versionen und widersprüchliche
persistierte Jobdaten werden abgewiesen, nicht migriert/repariert. Backups nur
konsistent mit WAL bzw. nach kontrolliertem Stop durchführen. Keine produktive
DB-Migration, kein Docker-/Containerkill und keine Volume-Löschung.
