# C27-R18 – Commit- und Staging-Plan

Noch nicht ausführen. Kein Git-Artefakt wurde von R18 erzeugt. Alle vorhandenen Branches, Stashes, Worktrees, Umgebungen und ignorierten Daten bleiben unverändert. Eine spätere Integration erfolgt auf einem neu autorisierten Kandidatenworktree; der bestehende C27-Worktree bleibt Quelle und wird nicht gestaged.

## Vollständiger Umfang

Das JSON-Inventar führt alle 1117 R16-Dateien und die 4 historischen R12-Berichte einzeln mit Zielpfad, Quelle, SHA-256, Trackingstatus, R12-Gruppe und Stagingentscheidung auf. Hinzu kommen die exakten neuen Payloadziele, darunter das unveränderte 32-Dateien-Acceptance-Overlay. Die sieben R18-Berichte haben ausdrücklich dokumentierte Repositoryziele unter docs/cs50/c27/reviews/r18; ihre Hashes stehen im äußeren SHA256SUMS, damit das Inventar nicht seinen eigenen Hash enthalten muss. `operator.py` materialisiert diese sieben Einträge vor der Indexprüfung aus dem geprüften äußeren Manifest.

- C1: 34 bestehende R12-Code-/Konfigurations-/Test-/Fixturedateien; umfasst 4 versionierte Änderungen und 30 unversionierte Dateien.
- C2: 30 R12-Dokumentations-/Fixture-Nachweise einschließlich der 4 historischen Testberichte. Berichte bleiben historisch, niemals als neue CI-Ergebnisse zählen.
- C3: 19 R12-Integrations- und Reviewnachweise.
- C4: neue CI-Dateien aus payload/ und die sieben R18-Berichte. Kein lokales Auditverzeichnis, keine Testausgabe, venv, pyc, .env oder temporäre Kopie.

83 R12-Ziele = 79 manifestierte Nicht-Ausgabepfade plus 4 historische Berichte. 75 unversionierte R16-Dateien sind damit vollständig berücksichtigt; weder git ls-files allein noch git add -u wäre vollständig. Die weiteren 1038 bereits versionierten unveränderten Inputdateien werden nicht erneut gestaged; ihre Präsenz wird im späteren Checkout gegen R16 geprüft.

Das Acceptance-Overlay wird bewusst unter ci/c27-r18/acceptance-overlay versioniert. Es ist eine ausführbare CI-Testeingabe und überschreibt keine lokalen Acceptance-/Learning-Namespaces. Eine dauerhafte Integration des Acceptance-Produkts bleibt ein eigener Reviewgegenstand. Die später erzeugten Inputkopien enthalten exakt 1117 Learning- oder 1147 Acceptance-Dateien.

## Konflikte und Ignorepolitik

Der bestehende Worktree könnte die neuen Payloadpfade ohne Pfad-/Hashkollision aufnehmen. Keine Übernahme wurde durchgeführt. Für die 83 ursprünglichen Ziele gilt weiterhin die R12-Provenienzprüfung. Der spätere Operatorhelfer verlangt einen frischen Checkout exakt auf a8af1d9..., prüft vor jedem Schreiben sämtliche alten Zielhashes und alle Quellhashes, danach erneut alle Zielhashes.

Die bestehende .gitignore ignoriert generell *.json, __init__.py und *.pdf, hat aber gezielte bestehende Fixtureausnahmen. Keine Original-Inputdatei darf geändert werden, sonst würde der CI-Eingangshash scheitern. Daher neue eng begrenzte .gitignore-Dateien nur unter ci/c27-r18 und docs/cs50/c27/reviews/r18: explizite Ausnahmen für die zwei CI-JSON-Metadaten, das Overlay-__init__.py und das R18-Inventar. Kein git add -f, kein git add ., keine pauschale Negation. Die bestehende getrackte PDFfixture bleibt bereits im Basiskommit enthalten.

.env, virtuelle Umgebungen und pyc sind ausgeschlossen. Ein genereller rootweiter secrets.toml-Ausschluss ist nicht zuverlässig vorhanden; neue CI-Verzeichnisse schließen ihn explizit aus. Entscheidend bleibt die vollständige positive Dateiliste. Der Musterscan umfasst alle 1117 Inputs und später die neuen Dateien/4 Berichte. Kandidatenpfade stehen ohne Werte im Prüfbericht; keine automatische Secretfreiheit. Vor Freigabe vollständige Sichtprüfung der neuen und historischen Daten.

## Review- und Commitgrenzen

Der Operator erstellt nach gesonderter Erlaubnis review/c27-r18-integration in einem neuen Worktree auf der dokumentierten Basis. `operator.py copy --apply` kopiert exakt die zu integrierenden Dateien, ohne den Quellworktree zu verändern. Danach C1–C4 jeweils separat stagen, Indexpfade und Index-Blobhashes vergleichen, git diff --cached --check, Diff lesen und erst nach ausdrücklicher Commitfreigabe committen. Bestehende Hooks dürfen nur in einer zuvor autorisiert bereitgestellten Umgebung laufen; kein stilles Herunterladen von Hookumgebungen. Hookänderungen an Dateien/Index erfordern erneute Hash-/Diffprüfung und gegebenenfalls eine neue versionierte Planung; keine Freigabe per Hooküberspringen ableiten.

Vor einem CI-Push aus den geprüften vier Commits den Branch c27-ci/r18-first-run ableiten. Ein separat geprüfter Bootstrap ausschließlich der Workflowdatei muss über den regulären Reviewprozess auf master gelangen, da GitHub workflow_dispatch sonst nicht registriert. Der Jobguard verhindert Tests auf master. Keine solche Integration ist in R18 erlaubt; deshalb bleibt CI-Erstlauf BLOCKED.

Nach Pushfreigabe nur den neuen CI-Branch pushen, Remote-SHA abgleichen, dann separaten manuellen Lauf autorisieren. Kein automatischer Trigger durch Push. Keine PR-Erstellung oder Mergekommandos Bestandteil dieser Ausführung. Nach tatsächlichem Erstlauf Evidenz separat reviewen und Gateentscheid aktualisieren. Produktionsgate bleibt unabhängig NOT_APPROVED.

## Sicherung und Lifecycle

Die verlangten externen Berichte und Payloaddateien sind über SHA256SUMS gesichert, zusätzlich als verifiziertes Archiv außerhalb des Worktrees. Sandboxschreibrechte gelten nur für diesen Worktree und /tmp; die vom Auftrag gewünschte externe Ablage kann daher hier nur temporär erfolgen. Operator muss vor Ablauf/Neustart das geprüfte Paket in einen dauerhaften externen Handoff kopieren. Keine dauerhafte Default-Branch-Sicherung behauptet.

R18 hat keine Branches/Worktrees erzeugt und entfernt keine. Zukünftig erzeugte Kandidaten-/CI-/Bootstrapartefakte bleiben bis Integration und vollständiger Datensicherung erhalten. Erst nach dokumentierter Integration auf master und den AGENTS-Prüfungen dürfen ausschließlich die dann eindeutig task-eigenen temporären Git-Artefakte regulär entfernt werden. Bei ungemergtem PR oder Unsicherheit behalten; MAINT-01/02/03-Artefakte sind nicht freigegeben.
