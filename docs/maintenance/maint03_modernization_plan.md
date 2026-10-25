# MAINT-03 – Umgesetzte Pakete und weitere Modernisierung

Status: fachliche Audit-/Implementierungsarbeit im isolierten Aufgabenworktree;
Integration und Lifecycle siehe [Validierung](maint03_validation.md).
**Keine Produktionsfreigabe; C26 bleibt HOLD.**

## Umgesetzt

| Paket | Änderung / Zweck | Kompatibilität und verbleibende Grenze |
| --- | --- | --- |
| A – Dateisystem | `utils/path_helper.move_file` bricht vor bestehendem Ziel ab, erzeugt keine Quellpfade und verwendet expliziten Zielparent. `list_files` liest ohne mkdir, akzeptiert Einzeldateien und filtert Verzeichnisse aus. | Namen/Argumente und None-/Listenrückgabe bleiben. Fehlende Listeninputs liefern jetzt `ValueError`; zuvor angelegte Verzeichnisse sind kein zu erhaltendes Readverhalten. Move bleibt sequenziell, nicht racefest. Keine Änderung am allgemeinen `ensure_dir`. |
| B – Archivziel | `utils/zipfile_helper.unpack_single_zipfile` gibt den vorhandenen Parameter `dst_folder` an `ZipFile.extract(path=...)` weiter. | Gleiche Signatur, None und stdlib-Fehler-/Passwortsemantik. Beobachtbarer Ablageort wird auf den benannten Zielordner korrigiert. Kein neues ZIP-Sicherheitsprofil. |
| C – Fehlerklassifikation | `core.retry.is_retryable_exception` folgt cause/context iterativ und beendet Zyklen. Identische doppelte Statuskonstante entfernt. | Gleiche transienten Klassen/Statuswerte, explizite cause-Präzedenz, Retryanzahl und Backoff. Tiefe gültige Ketten werden jetzt vollständig geprüft. |

Zwei neue Testdateien sichern diese Pakete mit 34 parametrisierten Fällen ab.
Die Tests wurden zunächst gegen den unveränderten Anwendungscode ausgeführt:
12 erwartete Fehler belegten die Defekte, 22 Fälle charakterisierten erhaltenes
Verhalten. Nach Umsetzung: alle 34 bestanden. Die Session-/Konfigurationsabhängigkeit
der Legacy-ZIPdatei wird ausschließlich in diesen IOtests durch einen kontrollierten
Logger ersetzt; Dateisystem, ZipFile, Retry und Pydantic-Ressourcenmodell sind real.
Es wird kein voll installierter Legacy-AppSession-Smoke behauptet.

Keine neuen Produktabhängigkeiten, keine Umbenennungsserie, keine Formatierung
des Gesamtbestands und keine Entfernung öffentlicher Oberflächen. Alle Änderungen
sind als kleiner zusammenhängender Reviewumfang vorgesehen; lokale Commits sind
durch das schreibgeschützte gemeinsame Git-Verzeichnis gesperrt.

## Nächste unabhängige Pakete

| Reihenfolge | Befunde | Konkreter Umfang | Vorbedingung / Abnahme |
| --- | --- | --- | --- |
| Vorab | R18, R19 | QA-Zustände isolieren und Publikations-Abbruchfenster als ausdrücklichen Recoveryfall spezifizieren | Umask-/Modulcache-/IDauswahl-/Snapshotbelege aus diesem Audit verwenden. Hardlink- und Backupgrenzen beibehalten; keine automatische Restadoption oder Löschung. |
| 1 | R07, R15 | DOCX-Import und eindeutig gebrochene Legacyhelfer einzeln reparieren | Geklärter Aufrufervertrag und installiertes vorhandenes lecture-worker-Profil; echte synthetische DOCX-/Dateifixtures, keine Modell-/Netzwerkdownloads |
| 2 | R05, R08 | Parsingmodelle charakterisieren und Env-/AppSessionabhängigkeit entkoppeln | Feld-/Schemadiff und bekannte Importpfade; expliziter Migrationsvorschlag vor öffentlicher Änderung |
| 3 | R09 | Reine doppelte Recordbuilder extrahieren, kompatible alte Importpfade erhalten | Payload-/Provenienz-/Formelgolden, frische SDKfreie Imports, Input-/Output-Gleichheit |
| 4 | R06, R11 | Legacyparser gegen moderne Adapter abgrenzen; kleine reine Schritte isolieren | Funktionsfähiger Legacybaselinepfad und semantische Fixtures; keine stillen Locator-/Parserversionsänderungen |
| 5 | R10, R16, R17 | JSON-/Pfad-/Logging-/Transportverträge explizit machen | Separate Sicherheits-/Fehler-/Persistenzprüfung; Crash-/Race-/Redaction-/Limitfälle, keine neue globale Policy ohne Review |
| 6 | R13, R14 | Async-Lifecycle vorschlagen und Profile/Toolversionen vereinheitlichen | Öffentliche close-/aclose-Migration reviewen; exakte Lock-/Worker-Smokes im passenden Offlineprofil |

## Vorschlag MAINT-04: Testisolation und Legacy-Konfiguration

Der Name bezeichnet einen **neuen Codeauftrag**, nicht den historischen
[Cleanupauftrag MAINT-04](../audit/maint04/README.md). Der Folgeauftrag soll
zunächst R18s Testisolation stabilisieren und R19s Recoverygrenze klären, danach
R05/R07/R08/R15 charakterisieren, ohne C26-/C27-Produktcode zu übernehmen.

Lieferumfang: Matrix der beiden Parsingmodellfamilien, echte minimale DOCXfixture,
SDK-/Secretfreie Importtests, explizite Konfigurationsübergabe als Migrationsentwurf
und höchstens separat belegte kleine Fehlerkorrekturen. Alte Klassennamen,
JSONfelder und Runner bleiben bis zur geprüften Migration erreichbar. Keine
automatische Migration von Knowledge-, Content-, Queue- oder Indexbeständen.

Abnahme: Schema-/Default-/Roundtripgleichheit oder ausdrückliche dokumentierte
Abweichung, negative Imports ohne dotenv-/Netzwerk-/Modellinitialisierung,
kompatible alte Einstiegspfade und passende vorhandene Regressionen. Erst danach
über die kanonische Modellfamilie entscheiden. Kein Abschluss allein durch einen
offenen PR; Integration und Aufbewahrung nach AGENTS.md getrennt nachweisen.

## Review und Aufbewahrung

Der ausdrückliche Auftrag verbietet Merges in `master`. Damit bleibt die in
AGENTS.md verlangte Defaultintegration ausstehend; der Audit wird nicht als
vollständig integrierter Repositoryabschluss ausgegeben. Dokumente bleiben im
Aufgabenworktree und werden, sofern der vorhandene GitHubpfad trägt, ausschließlich
in einem eigenen Draft-PR gesichert. Offene Drafts bleiben unverändert.

Der vorbestehende Aufgabenbranch/-worktree muss erhalten bleiben. Es wurde kein
anderer Branch, Worktree, Stash, Cache oder privater Datenbestand gelöscht. Weder
der Mergezustand anderer Aufgaben noch gleichnamige ältere MAINT-Inventare geben
eine Cleanupfreigabe für diesen Lauf.
