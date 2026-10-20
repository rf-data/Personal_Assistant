# Korrektur des Imports für Formelkonsolidierung

Die einzige produktive Änderung verschiebt den Import von `normalize_math_text`
aus `src.utils.text_helper` nach `src.utils.latex_helper`. Dort ist die vorhandene
Funktion tatsächlich definiert. Modelle, Algorithmen und Runner bleiben unverändert.

`tests/test_consolidation_math_import.py` importiert das vollständige echte Modul mit
`importlib.import_module` in einem frischen Python-Subprozess (`-I`). Kein AST-Ausschnitt
und keine Ersatzfunktion für Normalisierung werden verwendet. Der Test prüft die
Funktionsidentität mit latex_helper und konsolidiert zwei äquivalente Formeln zu einem
Ergebnis mit beiden Evidenzstellen. Ein transparenter Aufrufzähler delegiert an die
reale Normalisierung und belegt deren Verwendung.

Der vollständige App-Import ist nicht konfigurationsfrei: Die Importkette führt über
core.memory zu tiktoken und Parsing-Kontexten, sowie zu Settings, Logger und JSON-/Pfad-
Helfern. Ein unveränderter direkter Import in der vorhandenen schlanken Testumgebung
scheitert bereits mit `ModuleNotFoundError: No module named 'tiktoken'`. Die vorhandene
App-Konfiguration initialisiert zudem FolderEnvVars/AgenticEnvVars beim Import;
eine normale Installation benötigt diese Abhängigkeiten und passende Konfiguration.
Die Korrektur beseitigt den Helper-Fehler, beweist aber keinen vollständig gestarteten
App-Kontext. Es wurden keine zusätzlichen Pakete installiert oder Zugangsdaten geladen.

Die kontrollierte Umgebung ersetzt ausschließlich fünf importierte App-/I/O-Module:
core.memory, core.logger, core.config, utils.path_helper und utils.dict_helper.
Ihre ausführbaren I/O-/Logger-Funktionen sind verboten. Echte Knowledge-Modelle,
text_helper, latex_helper und das Konsolidierungsmodul werden regulär importiert.
Socket und DNS sind gesperrt; Marvin, OpenAI und Whisper dürfen nicht geladen sein.
Damit prüft der Test auch den früher defekten Importpfad, den AST-Tests nicht abdecken.

Die separate source_id-Korrektur aus PR #10 ist keine Änderung dieses PRs. Für den
Regressionstest auf dem bisherigen master wird die dokumentierte ID ausschließlich
am Testobjekt gesetzt, wenn dieses Modellfeld dort noch fehlt. Bei vorhandenem Feld
wird die reguläre validierte Konstruktion verwendet. Dies isoliert den Helper-Test von
der bereits separat behobenen Quellen-ID-Vertragslücke; keine Modelländerung erfolgt.

Validierung: neuer echter Import-/Formelkonsolidierungstest; zusätzliche bestehende
source_id-, offizielle Import- und CS50-Vertragstests im Workspace. Ruff und Repository-
Commit-Hooks prüfen die neuen Dateien. Kein Netzwerk-/LLM-Aufruf, keine Quelldaten-
Änderung und kein Runner-Aufruf. Der frühere Pilot-Test zur erwarteten falschen
Importquelle wird im Workspace auf die korrigierte Importquelle aktualisiert.
