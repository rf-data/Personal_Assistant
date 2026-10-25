# MAINT-04 – Kompatibilitätsreview

Vergleich mit `aafba19` unter Pydantic 2.13.4 und 2.14.1. **HOLD**, keine
Produktionsfreigabe. „Vollständig“ bedeutet jeweils den genannten getesteten
Vertrag, nicht alle denkbaren Pythonreflexionen oder privaten Datenbestände.
[Inventar](maint04_configuration_inventory.md), [Validierung](maint04_validation.md).

| Kategorie | Einstufung | Nachweis und verbleibende Grenze |
| --- | --- | --- |
| Öffentliche Imports | Eingeschränkt nachgewiesen | Alle 21 Namen und __module__/__qualname__ erhalten; echter frischer P-Import unter gesperrten Settings-/Session-/SDKimports; L-Deklarationen per AST geprüft. Vollständiger L-Appimport benötigt weiterhin optionale Pakete und Envwerte. |
| Klassenidentität | Erhalten für öffentliche nominale Verträge; Reflexion eingeschränkt | Alle 21 Paare bleiben verschieden; gegenseitiges isinstance=False und model_validate(model_instance)→model_type; familieninterne Vererbung und lokale Nested-Factories erhalten. MRO/__bases__/Feldherkunft verändern sich durch private Basen. |
| Modellvalidierung | Vollständig im charakterisierten Umfang | 42 eingefrorene Feld-/Configverträge; null je Feld, Extras, Modellinstanzen, falsche Literals, numerische/Boolkonvertierung, vollständige Dumps, leere Payloads und Fehlerfälle. Keine eigenen Validatoren/Serializer in beiden Familien. |
| Defaultwerte | Vollständig im charakterisierten Umfang | Alle 42 Defaultdumps und Default-/Factorymetadaten unverändert; voneinander unabhängige Instanzlisten/Nested-Defaults. Keine vereinheitlichten PDF-/Loggingdefaults. |
| JSON-Serialisierung | Vollständig im charakterisierten Umfang | model_dump(mode=json), model_dump_json, exclude_unset und JSON-Roundtrips; Loggingfelder bleiben nur L, Flags nur P. |
| JSON-Deserialisierung | Vollständig im charakterisierten Umfang | Leere, vollständige, synthetisch gespeicherte und aus vier versionierten YAMLs abgeleitete Payloads. Keine Normalisierung unbekannter Felder über bisherige Pydanticregeln hinaus. |
| JSON-Schemas | Vollständig für die 42 Settingsschemas | Vorher eingefrorene SHA-256 in validation und serialization identisch; Titel/$defs und Factory-/Defaultunterschied bleiben bestehen. Workflow-Snapshots unabhängig und weiterhin rot. |
| Gespeicherte Legacyconfigs | Eingeschränkt auf zugängliche Referenzen | Vier versionierte YAMLs und fünf synthetische JSONformen mit erwarteter Annahme/Ablehnung; keine privaten Bestände. streamlit_run bleibt für P ungültig; classify-Flags gehen beim L-Read weiterhin verloren. |
| CLI-Verhalten | Eingeschränkt | Vorhandene synthetische Material-/Lecture-/Offline-Smoke-Tests; Profile nutzen gleiche Guards. Keine echte Legacy-UI, keine voll installierte SDK-CLI. Runnerargumente/Produktcode unverändert. |
| Laufzeitkontexte | Eingeschränkt | Echte ParseContext-Klassendeklaration ohne Tokenizerimport, Enumwahl/Assignmentvalidierung/JSONroundtrip; Lecturebuilder mit echten YAMLs und injiziertem Encoding/Hashing. Keine globale AppSessioninitialisierung. |
| Parserintegration | Eingeschränkt | Reale synthetische moderne PDF/HTML/Code-/Materialtests; isolierte Legacy-Dispatch-/Pfad-/Markdown-/Persistenzgrenzen mit realen ausgeschnittenen Funktionskörpern. Kein voller DIY-/DOCX-/Docling-/Bild-/LLM-E2E-Lauf. |
| Python-Persistenz | Teilnachweis | Alle 21 P-Klassen nach Pickleroundtrip mit exaktem Typ/Namen; keine Behauptung über externe historische Pickles oder Legacy-Appunpickling. |
| Dynamische Erweiterungen | Offen / Review nötig | Keine Repositorynutzung gefunden, die exakte MRO oder gemeinsam geerbte Klassenfeld-Metadaten mutiert; externe Nutzung unbekannt. Instanzdefaults sind getestet, Klassenmetadaten können nun gemeinsame private Ursprünge haben. |
| Migration zwischen Familien | Weiterhin explizit erforderlich | Kein impliziter Adapter. L→P scheitert an Loggingfeldern; P→L kann Flags verlieren. Migrationsentwurf mit Originalbeibehaltung im Guide. |

Die 19 AST-Duplikate der Voranalyse waren **keine 19 identischen Pythonklassen**.
GeneralSettings besitzt trotz gleichem Schema verschiedene verschachtelte
Factoryklassen. ParsePDFSettings hat zusätzlich zum Feldunterschied einen bisher
leicht übersehenen Default-/Factoryunterschied bei extraction_model. Deshalb
bleiben sämtliche öffentlichen Identitäten und die zwei divergenten Modelle.

Der bisherige `RunSettings`-Discriminatorfehler ist ausdrücklich durch einen
Negativtest erhalten. Das behauptet keine funktionierende Aliasvalidierung.
Seine Reparatur erfordert eine eigene Formateinführung; ebenso bleiben das
`txt`/`plain_text`-Lookupgefälle und fehlende Legacy-Imports offen.
