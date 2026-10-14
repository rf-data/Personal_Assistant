# B01 – Eigenständiger CS50-Lecture-Runner

Abhängigkeit: A02–A05 (gestapelte PRs #27–#30). Der frühere Pilot wurde nicht
geändert und bleibt auf Python 0 / maximal zwei Chunks begrenzt.

prepare_lecture revalidiert Importbelege und beide Quellen, verwendet den echten
Chunker und bindet den vollständigen Plan in A01. Jobidentität nutzt portable
v2-Referenzen, bleibt bei einem expliziten Workspaceumzug gleich. Chunks über
6000 Zeichen oder leere Pläne werden ausdrücklich abgelehnt, nicht neu gesplittet.

run_lecture verarbeitet nur explizite Indizes oder alle Chunks. Das Jobreceipt
umfasst immer den gesamten Plan, sodass spätere Fenster denselben Job resumieren.
Alle vorhandenen Chunkartefakte werden vor Providerinitialisierung geprüft.
Dauerhafte Reservierung: A02-Journal zuerst, dann A01-Requestreceipt, dann HTTP.
Verwaiste Anfragen blockieren; keine Retries. Ein verlorenes Budget oder eine
fremde Attemptreferenz darf nicht zu neuen Requests führen. Usage wird zusätzlich
zu konservativen Reserven gespeichert. Umfangreiche Tokenreservierungen bleiben
verbraucht; keine automatische Rückerstattung.

Ein persistenter Scope-Laufzeitbeleg ergänzt das harte Subprozesszeitlimit.
Neustarts setzen die Deadline nicht zurück. Ein nach Dispatch verlorener
Laufzeitbeleg ist ein Konflikt. Request-/Token-/Zeitlimits sind Teil der Identität.

CLI (ohne execute-llm rein synthetisch/offline):

```bash
uv run --offline --no-sync python -m scripts.cs50_lecture \
  --plan docs/course_sources/cs50/cs50_lecture_plan.v1.json \
  --manifest /explicit/input.v2.json --workspace /explicit/source-workspace \
  --output /separate/scratch/lecture --course cs50_python --section 0 \
  --all-chunks --max-requests 1 --token-budget 60000 --timeout 120
```

Alternativ --start-index/--max-chunks; Default genau ein Chunk. Alle sechs
Kurszuordnungen sind erlaubt, Inputs müssen exakt einen Treffer ergeben. Week 0
und ai bleiben Strings. Defaultprovider openai_http, Evidence segment_v1 oder
explizit chunk. Nur --execute-llm plus Key und Parent-/Worker-Freigabe ermöglichen
reale Requests. Frisches Logverzeichnis pro Aufruf, persistenter Job-/Budgetroot.
Gesperrte Offline-Sockets und POSIX-Prozessgruppen-Timeout verhindern unbeabsichtigte
API-Aufrufe; der Provider selbst behält seinen 20-s-HTTP-Timeout ohne Retries.

B01-done bezeichnet abgeschlossene **Chunks**. Erst B02 erzeugt vollständiges
Knowledge-Dokument, Consolidation, Quality/Coverage und hashgebundenen Abschluss.
Keine Medien-/Whisperverarbeitung, keine Prompt-/Knowledge-Modelländerungen.
