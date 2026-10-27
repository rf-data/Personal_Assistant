# C26-CS50P-03: Release Readiness

27.10.2026. **Weiterhin HOLD.** Reviewbares Diagnose-/Betreiberpaket, kein
nachgewiesener SQLite-Stabilitätsfix und keine Host-/Produktionsfreigabe.
C26-04 Backup/Restore bleibt für vollständigen Produktionsbetrieb **DEFERRED**.
Kein Merge, Deployment, Hetzner-SSH, Coolify-, VPN-, Firewall- oder Secretwechsel.
Keine echten Kursdownloads oder produktiven Jobs.

## Entscheidungen und Ergebnis

1. **SQLite reproduziert und behoben?** BUSY 5 bei BEGIN mit unabhängigen
   synthetischen Writern reproduziert, aber nicht abschließend kausal geklärt
   oder behoben. Zusätzlich einmal native Guardianquarantäne mit Phase setup.
   [Befund und Audit](cs50p_sqlite_stability.md). Keine speculative Timeout-/Retry-
   oder Mutexänderung; src/, scripts/, Limits und Admission unverändert.
2. **Tests?** Tabelle unten; alle roten Vorläufe bleiben erhalten. Keine Addition
   überlappender Suiten und keine Umdeutung gescheiterter Stresstests.
3. **Download-/Verarbeitungsweg?** Synthetisch durchgängig bestanden: Download,
   Receipt-/Hashprüfung, Dedup, Seal/Katalogreview, genau ein Grant, C16-Guardian,
   Status, Verarbeitung, geprüfter Resultatabruf in einem **neuen Clientprozess**,
   Cancel und kontrolliertes Resume. Replay/Parallelstart und ungültige Grants
   bleiben blockiert. Getrennte Szenarien, kein behaupteter Live-Erstlauf.
4. **Units installierbar?** Offline-Syntax und Härtungsanalyse bestanden mit
   ausdrücklich verändertem Fixture-ExecStart. Originalprüfung scheitert an
   fehlendem `/opt/cs50p/venv/bin/python`. Keine positive Originalinstallation,
   keine Ziel-systemd-/UID-/cgroup-/Kernelabnahme. Nur Download und native
   Einzeljobinstanz für den Erstbetrieb vorsehen, kein Legacyworker zusätzlich.
5. **SSH/VPN?** Betreiber muss persönliches Konto/MFA, einzelne Gerätefreigabe,
   enge Tailscale-Grants und OpenSSH-Schlüsselzugang nach
   [Preflight](cs50p_hetzner_preflight.md) einrichten und negativ testen. Alten
   Adminzugang behalten; öffentliche SSH-Regel erst nach VPN-/Konsolentest und
   separater Entscheidung anfassen. Kein Tailscale SSH, CS50P-Port oder Webdienst.
6. **Serverinstallation fehlt?** Hashgeprüftes Wheelhouse/Sourcepaket für tatsächliche
   Architektur, positive vollständige CPython-3.12-Neuinstallation, neue Accounts/
   private Pfade, root-eigene Releases, echte Specs/Quellenfreigaben, Units und
   konkrete Sudo-Regeln sowie Ressourcen-/Dateisystem-/Journalprüfung. Exakte
   Reihenfolge: [Installation](cs50p_hetzner_installation.md), danach
   [Erstlauf](cs50p_first_run.md).
7. **Entscheidungen/Freigaben?** SQLiteursache/Umgang mit offenem Fehlermodus;
   Review des Kandidaten und reguläre spätere Integration; echte Quellen-/Lizenz-/
   robots-/Retentionfreigaben; konkreter Host, Dienst-UID, Geräte/IPs/SSHkey und
   sudo-Scope; positive Runtime-/Hostabnahme; danach gesonderte Genehmigung für
   genau einen echten Download und einen Job. Keine solche Freigabe hier erteilt.
8. **Risiken?** Konkurrenz/Quarantäne weiterhin möglich; synthetisch gemockte
   Kapazitätswerte ersetzen keine 2-vCPU-/4-GB-Abnahme. Keine Diskquote,
   begrenzte Journalretention, keine getestete Stromausfall-/Produktivrestorekette.
   Falsche VPN-/SSH-Regeln können Zugang verlieren; Konsole/alter Login bleiben
   Rückweg. Ein vertrauenswürdiger Betreiber mit Schreibrecht als Dienst-UID ist
   kein Angreifermandant; keine Mehrbenutzerisolation behauptet.
9. **READY FOR REVIEW oder HOLD?** Betriebs-/C26-Kandidat **HOLD**. Dokumente und
   Diagnosepatches können geprüft werden; neue rote Stresstests verhindern die
   Aussage „SQLite stabil“. Kein ungetesteter Livepunkt wird freigegeben.

## Tatsächlich ausgeführte Validierung

Rohbelege, vollständige JUnitdateien, reproduzierbarer Nachlauf und maschinenlesbare
Zusammenfassung: [artifacts/c26_cs50p_03](../../artifacts/c26_cs50p_03/).
Unveränderte Rohlogs/JUnit werden für die Gitlieferung zusätzlich im geprüften
`raw-evidence.tar.gz` mit Einzeldateihashes aufbewahrt; lokale Originale bleiben.
Testumgebung siehe environment.json; vorhandene c24r-Testvenv **nur gelesen**,
keine Änderung an diesem oder einem anderen fremden Worktree. uv-Venvversuch
scheiterte vor Installation am schreibgeschützten Cache. returns und
pydantic-settings fehlen dort; deshalb kein Runtimeclosurebeweis.

| Lauf / Bereich | Erfolgreich | Fehlgeschlagen | Übersprungen | Aussage |
| --- | ---: | ---: | ---: | --- |
| baseline: Native/MVP + bestehende SQLitegrenzen | 81 | 1 | 0 | Native CLI einmal Guardianquarantäne / BUSY 5 / setup |
| sqlite-process: erste neue Mehrprozessfälle | 2 | 2 | 0 | Beide Writerstressfälle BUSY 5 / begin; Dauerlock/Crash bestehen |
| sqlite-diagnostic: isolierter Nachlauf | 3 | 1 | 0 | 300-Zyklenstress scheitert bei Begin |
| regression: 13 Module | 284 | 0 | 0 | C16/C18, Native, Download, Kapazität, Ergebnisse, Binding, v1/v2 |
| sqlite-final: sechs neue Prozessfälle | 5 | 1 | 0 | Ohne Pause 1/2 Stressfälle rot; mit 10-ms-Testpause 0/2 rot; Crash/Dauerlock bestehen |
| resume-01 bis resume-10 | 10 Einzelläufe | 0 | 0 | Bekannter interrupted-before-state-write-Resume: 0/10 fehlgeschlagen |
| native-01 bis native-05 | 5 Einzelläufe | 0 | 0 | CLI review/approve/run/result/recover: 0/5 fehlgeschlagen |
| Ruff check / format check | bestanden | 0 | 0 | Sechs relevante Produkt-/Testdateien |
| systemd Original | 0 | 1 Prüfaufruf | 0 | Drei Units: Zielinterpreter fehlt lokal |
| systemd Fixture / Offline-Security | 2 Prüfaufrufe | 0 | 0 | Nur ExecStart=/usr/bin/true ersetzt; systemd 252 |

Alle pytest-Läufe: **0 errors**, keine deselected-Tests in diesen ausgewählten
Modulen. Kleine Wiederholungszahlen sind beobachtete Raten, keine statistische
Zuverlässigkeitsgarantie. Broad-regression dauert 379,02 s laut Konsole; deren
284 Tests enthalten 23 Native- und 48 MVPfälle (überlappende frühere Läufe nicht
hinzuzählen). Die sechs neuen Stresstests wurden separat ausgeführt und bleiben
mit ihrem roten Ergebnis sichtbar.

| Anforderung | Konkreter Offlinebeleg / Grenze |
| --- | --- |
| Download, Hashes, Materialinventar, Dedup | test_cs50p_mvp.py und test_cs50_batch_worker.py, MockTransport ohne Kurskontakt |
| Katalog, Grant, Worker, Verarbeitung, neues Resultatclient | test_full_download_review_admission_worker_status_processing_result |
| Cancel, Prozessneustart, Resume | Native-/CS50-Workflowtests, bestehende Cancel/Completion-Konkurenztests; Kill eines synthetischen SQLitewriters |
| Geänderte/abgelaufene/unbekannte Authority | Parametrisierte Native-Denytests, keine Aufweichung |
| offline-test explizit, ssh-runtime lehnt Testdaten ab | Native-Runtime-Separationstests und unveränderte Settingsvalidierung |
| Ein Job, kein Replay/Parallelstart | Grantverbrauch, Workerlock, Native-Denytests; C26-v1/v2-Regressionsverträge |
| Status/Result privat, kein API-Port | Lokale CLI; Netzwerkguard der Tests, Unit PrivateNetwork / AF_UNIX |
| SSH-Verbindungsabbruch | Dienstprofil bindet an systemd, nicht SSH; **echter Trenn-/Neuverbindungstest noch nicht auf Hetzner nachgewiesen** |
| Ressourcen | Kapazitäts-/Grenztests bestanden; reale CPU/RAM/Swap/PIDs/Disk/Quota/Cancel-cgroup nicht auf Hetzner nachgewiesen |
| Härtung | Offlineexposure: Download 4,2; Native/Legacyworker 3,5. Heuristik, kein Sicherheitszertifikat oder Hostnachweis |

**Nicht ausgeführt:** echte HTTPS-Kursübertragung, produktiver Job, Live-VPN/
SSH-/Firewall-/Coolifyänderung, öffentlicher Listener, systemd-Dienststart,
vollständige frozen Runtime-Neuinstallation, Zielhost-/Cgroup-/UID-/NPROC-/
Netz-/Plattenquotenprüfung, unabhängiger Review und Defaultbranchintegration.
Kein übersprungener Livepunkt wird als bestandener Test gezählt.

## Sicherung, Git und Lifecycle

Ausgangs-/End-HEAD, Tracking und live Featurebranch identisch: 2f2b410.
GitHub lesend am Ende: master `a8af1d9372eb435d3e1331c33b047d21120d57c2`;
lokaler master `c1007efdbac3c1544020f328a3a1347e481797ba` ist veraltet und
wurde nicht verändert. Gitindex liegt im schreibgeschützten gemeinsamen
Gitverzeichnis. Keine Umgehung über Connector-Commits, kein Push/PR/Merge.
Nativebasis gesichert; **neue Arbeit noch uncommitted, Review/Integration pending**.

[Übergabe](../../artifacts/c26_cs50p_03/handoff/HANDOFF.md) enthält getrennte
Test-/Dokumentations-/Belegpatches, vollständige Dateiliste, SHA-256 und
Anwendungs-/Bytevergleich gegen HEAD. README gehört nicht zur Tasklieferung;
deren vorherige Änderung und Hash bleiben separat erhalten. Keine temporären
Gitbranches/Worktrees angelegt oder entfernt. Bestehender Featurebranch und
Worktree bleiben wegen ausstehendem Review/Integration erhalten. Keine fremden
Branches, Daten, Venvs, Stashes oder Quarantänen bereinigt.

Gemäß AGENTS.md müssen dauerhafte Dokumente später über den regulären Reviewweg
auf master gelangen. Das ausdrückliche Mergeverbot dieses Auftrags hat Vorrang:
kein vollständiger Lifecycle-/Integrationsabschluss behauptet. Die persistenten
Taskbelege bleiben bis zur erlaubten Integration erhalten; temporäre synthetische
pytest-Daten sind keine produktiven Recoveryartefakte.
