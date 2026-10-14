# A03 – Portable CS50-Knowledge-Inputs

Abhängigkeit: A02-Branch (PR #27); A01 ist in master integriert. Neue Manifeste
haben schema_version=2 und workspace_binding=explicit_cli_workspace. Alle drei
Artefaktpfade und die geplanten Bindingpfade sind relativ zum explizit angegebenen
Workspace, ohne '..' oder absolute Referenzen. URLs, Sprache, IDs, Hashes und
Transcript-/Discovery-Provenienz bleiben unverändert. Keine Dateisuche.

load_knowledge_manifest liest v1 und v2 ausdrücklich. Bestehende v1-API und
save_knowledge_manifest bleiben unverändert; v1 bindet weiterhin seine absoluten
Pfade. resolve_knowledge_input löst v2 ausschließlich am gegebenen Workspace auf.
Der bestehende Binder revalidiert anschließend beide Dateien und Importbelege.
Portable Dateien haben keine schwächeren Hash-/Identitätsregeln.

report_cs50_knowledge_input erzeugt standardmäßig v2, unterstützt --workspace und
--legacy-v1. save_portable_manifest publiziert exklusiv/atomar über A01.
Der ursprüngliche begrenzte Pilot bleibt v1-kompatibel und unverändert; der neue
Lecture-Runner verwendet den Versionsloader. Dieser PR migriert keine Dateien.

Tests: vier portable Fälle plus 28 bestehende Inputfälle (ein Originalpilot-Skip):
Workspacekopie/Umzug mit unveränderten relativen JSONs, alte v1-Datei, fremder
Workspace, Traversal, absolute Pfade, Symlink und beschädigter Rohhash.
