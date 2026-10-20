Worktree	Status	Empfehlung
Personal_Assistant-audit	Kleine virtuelle Umgebung	Später prüfen
Personal_Assistant-completion	CS50-Worker-Umgebung	Später prüfen
Personal_Assistant-completion-audit	Zwei gesicherte Originalberichte	Später prüfen
Personal_Assistant-materials	Letzter Materialentwicklungsstand	Vorerst behalten
Personal_Assistant-materials-finalcheck	Vollständig getesteter Materialstand	Vorerst behalten
Personal_Assistant-provenance-models	VS Code verwendet den Ordner	Nach Schließen der IDE erneut prüfen

#############################

uv run --offline --no-sync python -m scripts.cs50_materials inventory \
  --output /home/robfra/0_Portfolio_Projekte/gmp_compliance/docs/cs50-material-inventory.v1.json

uv run --offline --no-sync python -m scripts.cs50_materials plan \
  --course cs50_python \
  --section 0 \
  --output /home/robfra/0_Portfolio_Projekte/gmp_compliance/docs/python0-material-plan.v1.json

uv run --offline --no-sync python -m scripts.cs50_materials plan \
  --resource "$RESOURCE_ID" \
  --license-reviewed \
  --output /home/robfra/0_Portfolio_Projekte/gmp_compliance/docs/reviewed-one-material.v1.json


uv run --offline --no-sync python -m scripts.cs50_materials download \
  --plan /home/robfra/0_Portfolio_Projekte/gmp_compliance/docs/reviewed-one-material.v1.json \
  --workspace /tmp/python0-notes-artifacts \
  --resource "$RESOURCE_ID" \
  --max-resources 1


Codex-Aufgabenplanung für beide Repositories
Ich habe die aktuelle docs/ROADMAP.md vom 12. Oktober 2026 gelesen und sie mit dem heute auf GitHub sichtbaren Code abgeglichen.
Die Roadmap enthält bereits neun konkrete Codex-Aufgaben (C01–C09). Meine wichtigste Erkenntnis ist aber: Die Roadmap sollte aktualisiert werden, bevor du die nächsten größeren Codex-Arbeiten verteilst. Der aktuelle CS50-Entwicklungsstand und einige Abweichungen zwischen den Repositories werden darin noch nicht ausreichend berücksichtigt.
1. Gesamtbewertung
Personal_Assistant
Knowledge-Pipeline
Discovery, SRT-Verarbeitung und Knowledge-Anbindung sind weit fortgeschritten. Offen sind reale LLM-Qualität, produktive Batchverarbeitung und die Integration der gestapelten PRs.

personal-assistant-ui
Admin-Oberfläche
Ein erster Streamlit-Einstieg mit Dashboard-, Dateien- und Logs-Tabs liegt vor. Konfiguration, Inventar, Sicherheit und Deployment müssen konsistent fertiggestellt werden.



Besonders wichtig: In Personal_Assistant sind die CS50-PRs #14 bis #18 auf GitHub weiterhin als offene, aufeinander aufbauende PRs auffindbar. Dass die Änderungen gepusht sind, bedeutet deshalb noch nicht zwangsläufig, dass sie auf master integriert sind.
Das würde ich vor jedem weiteren größeren Entwicklungsschritt prüfen.
2. Meine priorisierte Aufgabenliste
Codex-Eignung: 5/5 = weitgehend selbstständig umsetzbar und automatisch testbar; 1/5 = stark von fachlichen oder betrieblichen Entscheidungen abhängig. Die Dringlichkeit ist meine Bewertung, nicht die Reihenfolge der Roadmap.Prio	Aufgabe	Repo	Dringlichkeit	Codex	Grundlage
1	Gestapelte CS50-PRs, Branch-Basen und Tests prüfen; Integrationsplan erstellen	Core	Sehr hoch	5/5	Zusätzlich
2	UI-Import- und Konfigurationsvertrag prüfen, BaseSettings vervollständigen	UI	Sehr hoch	5/5	C01
3	TXT-Importer: sechs fehlschlagende Tests und Zeitstempelvertrag korrigieren	Core	Hoch	5/5	Zusätzlich
4	Read-only Stage-Inventar mit eindeutiger Dateiklassifikation	UI	Hoch	5/5	C02
5	Reale LLM-Extraktion mit einem Chunk und Qualitätsprüfung	Core	Hoch	4/5	Zusätzlich
6	Knowledge-Consolidation: Skip/Resume, Fehler und Ausgabeintegrität testen	Core	Hoch	5/5	C07
7	Dateiansicht mit Stage-Filtern, Größe und Änderungsdatum	UI	Hoch	5/5	C03
8	Sicheren Log-Viewer implementieren	UI	Hoch	5/5	C04
9	Dashboard aus gemeinsamem Inventar einschließlich Lecture-Abdeckung	UI	Mittel–hoch	5/5	C05 + Erweiterung
10	Batch-Import der übrigen CS50-SRTs mit Coverage-Report	Core	Mittel–hoch	4/5	Zusätzlich
11	Gold-Evaluationsdatensatz und Knowledge-Qualitätsprüfungen	Core	Hoch	3/5	Roadmap Phase 3
12	Coolify-/Docker-Konfiguration, Mounts und Zugriffsschutz	UI	Hoch vor öffentlichem Betrieb	4/5	C06
13	Doppelte Dependencies in pyproject.toml entfernen	Core	Niedrig–mittel	5/5	C08
14	README, Architektur und Roadmap mit dem aktuellen Code abgleichen	Beide, getrennte PRs	Mittel	5/5	C09 + Ergänzung
Die ersten sechs Punkte hätte ich besonders im Blick: Sie verhindern, dass du auf einer unklaren Repository-Basis oder mit bekannten Fehlern weiterentwickelst.
3. Auffälligkeiten im aktuellen GitHub-Code
A. personal-assistant-ui: möglicher Startfehler
Die aktuelle app_ui.py importiert:
from src.core.environment import get_settings



Die referenzierte Datei src/core/environment.py konnte ich auf dem Default-Branch jedoch nicht abrufen. Auch ein Dockerfile am Repository-Root war unter diesem Namen nicht auffindbar.
Das ist kein vollständiger Beweis, dass die Module fehlen – sie könnten anders organisiert oder noch auf einem anderen Branch liegen. Es ist aber ein konkreter Grund, zuerst einen frischen App-Start und den Importpfad testen zu lassen.
Die UI enthält bereits die Tabs „Dashboard“, „Dateiansicht“ und „Logs“. Die Roadmap-Aussage „nur einfacher Dateibrowser“ ist damit zumindest teilweise überholt. Eine vollständige Admin-Oberfläche ist es aber ebenfalls noch nicht: Die Dateiansicht listet nur den unmittelbaren Verzeichnisinhalt, und die Logs-Ansicht zählt Dateien, ohne sie anzuzeigen.
B. Personal_Assistant: die Consolidation ist nicht vollständig sicher gegen fehlerhafte Resume-Zustände
In src/run_knowledge_consolidation.py erfolgt das Überspringen derzeit im Wesentlichen durch:
if output_path.exists():    continue



Damit würde auch eine bereits vorhandene, aber beschädigte oder unvollständig geschriebene Ergebnisdatei als abgeschlossen gelten.
Zusätzlich aktiviert run_knowledge_consolidation() aktuell configure_marvin(context), obwohl der deterministische Teil grundsätzlich davon unabhängig ist. Der reguläre Verarbeitungspfad ruft danach die semantische Konsolidierung auf.
Ich würde Codex deshalb nicht nur Tests für Skip/Resume erstellen lassen, sondern auch eine sichere, kleine Korrektur des Abschlussnachweises untersuchen: Eine vorhandene Datei ist noch kein validiertes Ergebnis.
C. Der Paketmanager hat ein einfaches Wartungsthema
In pyproject.toml sind im Extra lecture-worker tatsächlich docling[rapidocr] und pymupdf jeweils doppelt eingetragen.
C08 aus der Roadmap ist also weiterhin berechtigt. Das ist ein klassischer Codex-Auftrag, allerdings kein dringender Produktionsblocker.
D. Die Hauptdokumentation beschreibt noch die frühere GMP-Anwendung
Sowohl README.md als auch docs/architecture.md behandeln primär Dokumenten-Parsing, SOP-Generierung und die ältere Streamlit-/RAG-Architektur.
Das ist nicht falsch – diese Module existieren –, bildet aber den heutigen Lecture-/CS50-/Knowledge-Schwerpunkt und die Trennung zur neuen Admin-UI nicht ausreichend ab.
Ich würde diese Dokumentationsarbeiten nach der PR-Integration durchführen, damit Codex den tatsächlichen master-Stand dokumentiert.
4. Was die Roadmap noch nicht ausreichend erfasst
Die Roadmap enthält neun Entwicklungsphasen. Einige davon würde ich bewusst zurückstellen.
Roadmap-Bereich	Meine Einschätzung	Codex-Eignung
Quality Checks / Evaluation	Jetzt beginnen; Grundlage für verlässliches Knowledge	4/5 für Testharness, 2/5 für fachliche Goldlabels
Retrieval / Embeddings / Vector DB	Nach erster echter Knowledge-Evaluation	5/5 für Infrastruktur
Learning Application / Ask the Lecture	Nach Retrieval und Evidence-Tests	4/5
Dokumentgenerierung	Später, sobald Knowledge-Inhalte zuverlässig sind	4/5
Knowledge Graph	Noch nicht priorisieren	3/5
FastAPI / Backend	Noch keine Notwendigkeit für ein großes Backend erkennbar	4/5
Portfolio / technische Dokumentation	Schon parallel in kleinen Schritten sinnvoll	5/5
Ein wichtiger zusätzlicher Punkt ist die Evaluation von Formeln und Aussagen. Deine frühere Visual-Enrichment- und Formelrekonstruktionsarbeit hat bereits gezeigt, warum ein erfolgreiches LLM-Schema allein nicht genügt.
Ein Gold-Datensatz mit 30–50 manuell geprüften Fällen aus Mathematik, Python, SQL und AI wäre ein wertvoller Start. Codex kann Vergleichsfunktionen, Metriken und Reports hervorragend bauen. Die fachliche Richtigkeit der Gold-Referenzen würde ich aber nicht allein durch Codex bestimmen lassen.
5. Meine empfohlene Codex-Reihenfolge

Ich würde die nächsten Aufgaben in drei Arbeitsblöcke aufteilen, statt einfach C01–C09 nacheinander abzuarbeiten.
1
Repository-Basis und bekannte Fehler stabilisieren
CS50-PR-Stack prüfen, UI-Konfiguration und Startfähigkeit testen, TXT-Importer korrigieren, Consolidation-Resume absichern.
Kleine, unabhängige PRs; sehr hohe Codex-Eignung.



2
Erstmals ein nutzbares End-to-End-System herstellen
UI-Inventar und Dashboard entwickeln, echten CS50-LLM-Pilot fachlich bewerten, anschließend weitere SRT-Transkripte importieren und einen reproduzierbaren Knowledge-Batch planen.
Codex für Implementierung; du entscheidest über API-Kosten und fachliche Freigaben.



3
Qualität, Retrieval und Produktreife
Gold-Evaluation, Knowledge-Suche, evidenzbasierte Antworten, Knowledge-Assistant-UI, Dokumentations- und Deployment-Arbeiten.
Erst sinnvoll, wenn die vorherigen Stufen tatsächlich verlässlich arbeiten.
