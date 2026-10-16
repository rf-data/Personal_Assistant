# Pipeline-Metrics-Vertrag v1

Implementiert: `src/core/pipeline_metrics.py`, maschinenlesbarer Snapshot
`monitoring/pipeline-metrics.v1.json`, Offline-Validator und Prometheus-Text-
Renderer. Kein Exporter/HTTP-Server, Workerdispatch, Statusscanner oder globaler
Counter-Speicher. Keine neuen Dependencies.

Der Vertrag nimmt **bereits aggregierte reale Beobachtungen** an.
Leere Eingabe erzeugt leeren Text, keine Nullmesswerte. Unbekannte Zustände
werden ausgelassen. Vorhandene Receipts werden nicht automatisch als vollständige
Messhistorie behandelt.

| Metrik mit Präfix personal_assistant_ | Typ | Labels | Bedeutung |
| --- | --- | --- | --- |
| workers_available | Gauge | worker_pool | tatsächlich bereite lebende Worker |
| jobs_started_total | Counter | process, worker_pool | gestartete Dispatchversuche |
| jobs_completed_total | Counter | process, worker_pool, outcome | bestätigte terminale Versuche: success/failure/cancelled |
| jobs_failed_total | Counter | process, worker_pool, error_class | bestätigte Fehler; Teilmenge completed/failure |
| jobs_running | Gauge | process, worker_pool | aktuell bestätigte laufende Versuche, ohne queued/unknown |
| job_oldest_running_start_timestamp_seconds | Gauge | process, worker_pool | Unix-Startzeit des ältesten laufenden Versuchs; ohne laufenden Versuch auslassen |
| job_duration_seconds | Histogramm | process, worker_pool, outcome | Dauer bestätigter terminaler Versuche |
| pipeline_stage_duration_seconds | Histogramm | process, worker_pool, stage | Dauer abgeschlossener Stufen; nicht zusätzlich als Job zählen |

Eine Queue-Länge wird nicht angeboten: kein persistenter Queue-Service wurde
nachgewiesen. Optionalen Backlog später ausdrücklich definieren, statt Scheduler-
Listen oder pending Chunks als Queue auszugeben.

workers_available meint zugelassene gesunde Worker mit aktuellem Heartbeat,
einschließlich beschäftigter Worker, nicht freie Ausführungsslots. Die gleiche
aggregierte Jobpopulation darf nicht aus mehreren Controller-Replikaten erneut
gescrapt und summiert werden: genau ein autoritativer Exporter je disjunktem
Bereich oder eine gesondert geprüfte Leader-/Dedupstrategie ist erforderlich.

## Labels, Grenzen und Textformat

Vokabular ist endlich und im Snapshot festgehalten: zehn Prozess-/Stufennamen,
vier Worker-Pools (default/cpu/io/llm), drei Outcomes, sieben Fehlerklassen.
Mögliche Stufen sind keine Startberechtigung und kein Nachweis angebundener Worker.
Keine Run-/Lecture-/Course-IDs, Dateinamen, URLs, Exceptiontexte, Hashes oder
dynamischen Workernamen als Labels. `job` und `instance` fügt Prometheus aus
expliziter Discovery hinzu (maximal 32 konfigurierte Pipeline-Targets).

Histogrammgrenzen in Sekunden: 1, 5, 15, 60, 300, 900, 1800, 3600, +Inf.
Pro Labelsatz sind alle kumulativen Buckets, Summe und Count notwendig.
Einheiten/Operatoren werden nicht umgedeutet; keine negativen/NaN/Inf-Werte,
doppelten Zeitreihen, unbekannten Labels oder unvollständigen Histogramme.
Count ist ganzzahlig, Buckets monoton und +Inf identisch mit Count.
Der Renderer sortiert deterministisch, inklusive aufsteigender Bucketgrenzen,
und rundet Counterwerte nicht auf sechs signifikante Stellen.

Das harte Vertragsbudget ist 2000 tatsächlich ausgegebene Samples je Scrape.
Nicht jedes theoretisch mögliche Prozess-/Pool-/Stage-Kreuzprodukt darf
gleichzeitig materialisiert werden. Nur tatsächlich instrumentierte Kombinationen
ausgeben; Budgetüberschreitung wird abgewiesen, nicht still abgeschnitten.
Prometheus begrenzt den Pipeline-Scrape zusätzlich auf 5000 Samples, 32 Targets,
2 MB und 10 s. Namensfilter ist keine vollständige Kardinalitätssicherung:
der spätere Exporter muss den Validator tatsächlich benutzen und fremde Labels
**abweisen**, nicht nur löschen und Zeitreihen versehentlich zusammenführen.

HTTP-Integration: Content-Type `text/plain; version=0.0.4; charset=utf-8`,
ein konsistenter Snapshot, authentifizierte private Scrapegrenze.
Buckets/Labels sind Vertragsänderungen; Versionierung und Consumer-Prüfung nötig.
Counter monoton innerhalb einer Exporterlebensdauer; Resets nach Neustart müssen
eindeutig sein. Histogramme/Counter sind nicht der Ersatz für die Jobdatenbank.
Prometheus rate/increase behandelt beobachtete Resets; verlorene Ereignisse lassen
sich damit nicht rekonstruieren.

## Fehlerrate, Laufzeiten und Alarmierung

Fehlerrate: rate(jobs_failed_total[15m]) geteilt durch rate(jobs_completed_total
mit outcome success oder failure). Abbrüche sind nicht im Nenner.
Alarm über 20 Prozent, mindestens fünf abgeschlossene Versuche in 15 Minuten,
zehn Minuten anhaltend. Kein künstliches positives Ergebnis bei leerem Nenner.
Das Dashboard kann bei fehlendem Nenner No data anzeigen.

p95 aus echten Histogrammbuckets über fünf Minuten, nach Prozess bzw. Stage.
Dies ist eine Schätzung aus Buckets. Keine Laufzeiten aus Dateizeitstempeln.
LongRunning verwendet die echte älteste Startzeit und jobs_running > 0:
über 30 Minuten, fünf Minuten anhaltend. Abschluss-Histogramme allein können
keine noch laufenden hängenden Jobs erkennen.

TargetDown alarmiert nach zwei Minuten für tatsächlich konfigurierte Targets.
WorkerUnavailable braucht echte workers_available < 1. MetricsMissing erkennt
einen erreichbaren konfigurierten Pipeline-Exporter ohne Availability-Metrik.
Ohne konfigurierten Exporter kein Worker-Alarm: die Dashboard-Texttafel benennt
diese Integrationslücke. Fehlende einzelne Pools erfordern später einen
autorisierten erwarteten Poolkatalog.

## Integration mit Runnern, Job-Control und UI

1. Den in C14 definierten Controller-/Worker-Vertrag separat implementieren.
   Nur dieser hat eine verlässliche Gesamtsicht auf Dispatch, Eigentümer,
   Start/Ende, bestätigten Abbruch, Heartbeats und aktive Versuche.
2. Metriken an atomaren, persistierten Statusübergängen aktualisieren.
   create/queued ist noch kein Start. Idempotenter Retry darf denselben Versuch
   nicht erneut zählen; neuer Dispatchversuch zählt neu. Unbekannt/partial/blocked
   nicht automatisch als failure/success klassifizieren.
3. Checkpoints/ArtifactReceipts zur Verifikation nutzen, aber nicht rückwirkend
   vollständige Counter/Laufzeiten aus unvollständigen Artefakten erfinden.
   Fehler auf feste Klassen abbilden, Detailkontext in autorisierten Joblogs.
4. Worker readiness aus echten, zeitbegrenzten Heartbeats ermitteln.
   Abbruch zählt erst nach terminaler Bestätigung. Running-Gauge nach Neustart
   aus autoritativen Zuständen rekonstruieren oder bis dahin auslassen.
5. Kleine Adapter nur an ausgewählten Runnergrenzen ergänzen, Vertragstests mit
   synthetischen Events ausführen, Budget/Auth/TLS/Timeouts testen.
6. Erst dann privaten Exporter freigeben und pipeline-Discovery aktivieren.
   Pipeline-Labels und Targetadressen nicht aus unkontrollierten UI-Parametern bilden.

Die Admin-UI kann die provisionierten Grafana-Dashboards später per autorisiertem
Link öffnen. Prometheus ist keine Steuerungs-API: Jobstart/Cancel bleibt beim
authentifizierten Controller. Keine Docker-Sockets/Hostpfade oder Tokens im
Browser. C15 verändert weder das UI-Repository noch bestehende Worker.

Referenz für Namens-/Labelkonventionen:
[Prometheus](https://prometheus.io/docs/practices/naming/).
