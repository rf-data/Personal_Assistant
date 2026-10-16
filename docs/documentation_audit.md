# Dokumentationsaudit und Konsolidierung (C17.0)

Stand: 16.10.2026. Verifizierte Backendbasis `78b35a5`, UI-`main` `137651e`.
[Inventar](repository_inventory.md), [Maschinenbericht](audit/repository_inventory.v1.json),
[Remote-/PR-Belege](audit/remote_snapshot.v1.json), [Cleanupplan](cleanup_plan.md).

## Verfahren und Nachweistiefe

130 versionierte Markdown-/RST-Dokumente und 18 JSON-Dokument-/Quell-/Reportartefakte
unter `docs/` wurden erfasst. Der Worktreevergleich ergab 1.500 Vorkommen an
180 unterschiedlichen Markdown-/RST-Pfaden. Relativer Pfad, SHA-256, Git-HEAD,
Ancestry, Inhalt/Version, vorhandene Implementierungsreferenzen und Rolle des
Dokuments werden getrennt betrachtet. Identischer Basename ist kein Duplikatbeweis.
Der öffentliche JSON-Bericht beschränkt sich auf nachweislich veröffentlichte
Dateipfade und aktuelle Dokumentationsbelege. Wiederholte lokale Pfad-/Hash-
vorkommen samt Worktree-Fundorten werden ausschließlich im ignorierten privaten
Detailbericht normalisiert; sie sind nicht Teil des PR-Payloads.

Die per-Datei-Tabelle verbindet mechanische Evidenz mit fachlicher Einordnung.
Architektur, Top-Level-Einstiege und C10–C18-Integrationsgrenzen wurden direkt
gegen Modelle, Runner, Registry und gemergte PRs geprüft. Die dort angegebenen
Tests belegen ihren jeweiligen Scope. Statische Pfad-/Linkprüfung ist kein
vollständiger semantischer Beweis aller Beispiele in jedem historischen Bericht;
solche Berichte behalten ihre explizite damalige Commit-/Testbasis. Ein fehlender
Pfad innerhalb eines Codebeispiels wird nicht automatisch als Produktionsfehler
behandelt. Neue Auditberichte sind benannte Ausgaben und werden nicht über
selbstreferenzielle Hashes als ihre eigene unabhängige Wahrheit behandelt.

Sensitive/ignorierte Laufzeitdateien, `.env`, private lokale Auditberichte und
Orga-/Dateninhalte wurden durch den Auditor nicht gelesen oder übernommen.
Die bei der separaten Testausführung gefundene alte Runtime-Kopierfixture und
deren Korrektur sind transparent im [Testnachweis](audit/validation.md) beschrieben.

## Konkret behobene Widersprüche

| Vorherige Aussage / Lücke | Aktuelle Evidenz | Maßnahme |
| --- | --- | --- |
| Hauptrepo sei primär GMP-Streamlit, Tests nur Fragmente | gemergte Material-/Lecture-/Evaluation-/C16-/C18-Module und umfangreiche Offline-Suiten | README/Architektur/Entwicklung/Roadmap erneuert |
| C14 sei nur Dateibrowser, C17-HTTP-Client noch Zukunft | UI-PR #1/#2 gemergt; C17-Tree exakt mit Remote identisch; aktuelle E2E-Suite | UI-Zuständigkeit und Clientstatus korrigiert |
| Formelevaluation / Resume allgemein nur offen | C11/C12 vorhanden und getestet; Grenzen weiterhin explizit | synthetische Evaluation und konservativen Resume von offenen fachlichen Fragen getrennt |
| keine persistente Queue / kein echter Jobexporter vorhanden | C16-Store/Executor/Metrics; C18 erweitert endliche Labels auf elf | C15-Basisvertrag gegenüber C16-Erweiterung richtig eingeordnet |
| elf C16/C18-README-/Vertrags-/Fixturetexte lokal nicht vorhanden | lokaler Ausgangscommit `b58f63c` lag hinter Remote | Hauptarbeitskopie kollisionsfrei auf aktuellen Master-Audit-Branch gebracht |
| historische Parser-v1-Berichte wirken aktuell | HTML-v2/PDF-v2 vorhanden; alte Paketberichte weiterhin wertvoll | historische Banner und v2-Einstiege ergänzt |
| `frontend/chat_app/streamlit_app.py` sei Startpfad | Datei fehlt; Seiten liegen in `chat_page.py`, alter Rootrunner hat unqualifizierten Import | unbelegten Startbefehl entfernt, keine alternative Lauffähigkeit erfunden |
| zwei Rootabschlussberichte sind aktive zweite Fassungen | Plan byteidentisch archiviert; Audit nur eine korrigierte Pfadreferenz abweichend | Rootpfade als kompatible Archivverweise erhalten |

Die früheren vier Übersichtsdokumente sind einschließlich damaliger Aussagen im
[Archiv](archive/2026-10/repository-overview/README.md) erhalten. Quell-/Zielhashes
und erlaubte Banner-/Link-/portable Beispielpfadänderungen stehen im [Manifest](audit/archive_manifest.v1.json).

## Übersicht je versioniertem Markdown-/RST-Dokument

Fundort ist der relative Link. Hash ist der aktuelle SHA-256-Präfix; die vollständigen
Hashwerte der veröffentlichten Dokumente stehen im öffentlichen Maschinenbericht.
Lokale Varianten und deren Worktree-Fundorte verbleiben im privaten Detailbericht.
Varianten zählen unterschiedliche Inhalte am selben Pfad vor den Auditänderungen.
Gleiche Namen mit unterschiedlichen Inhalten bleiben getrennt. Die letzten drei
Spalten dokumentieren Aktualität, Referenzimplementierung und Maßnahme.

| Dokument / Fundort | SHA-256 / Varianten | Aktualität / Rolle | Referenzimplementierung | Maßnahme |
| --- | --- | --- | --- | --- |
| [README.md](../README.md) | `f68e2e390714` / 5 | aktueller Einstieg, überarbeitet | src/job_control/registry.py; src/workflows/definition.py | aktuelle Paketstände/Tests abgeglichen; behalten |
| [docs/ROADMAP.md](ROADMAP.md) | `92b520e259e2` / 4 | aktueller Einstieg, überarbeitet | src/job_control/registry.py; src/workflows/definition.py | aktuelle Paketstände/Tests abgeglichen; behalten |
| [docs/architecture.md](architecture.md) | `bb01a124f013` / 1 | aktueller Einstieg, überarbeitet | src/job_control/registry.py; src/workflows/definition.py | aktuelle Paketstände/Tests abgeglichen; behalten |
| [docs/cs50/README.md](cs50/README.md) | `3ac276a786c4` / 5 | aktueller Einstieg, überarbeitet | src/tools_materials/; src/tools_knowledge/; src/job_control/ | aktuelle C10–C18-Stände ergänzt; alte Testzahlen abgegrenzt |
| [docs/cs50/archive/2026-10/README.md](cs50/archive/2026-10/README.md) | `6f2c913e4018` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/analysis.md](cs50/archive/2026-10/analysis.md) | `45e65f9836b4` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/cs50_knowledge_checkpoint_test_report.md](cs50/archive/2026-10/cs50_knowledge_checkpoint_test_report.md) | `0621c1ed018f` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/cs50_pipeline_completion_audit.md](cs50/archive/2026-10/cs50_pipeline_completion_audit.md) | `6f01ccba7a1c` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/cs50_pipeline_completion_plan.md](cs50/archive/2026-10/cs50_pipeline_completion_plan.md) | `b9b7b078046e` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/cs50_pipeline_completion_report.md](cs50/archive/2026-10/cs50_pipeline_completion_report.md) | `ecfce9399af7` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/extraction_report.md](cs50/archive/2026-10/extraction_report.md) | `f9bc671e500d` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/final_integration_blocker.md](cs50/archive/2026-10/final_integration_blocker.md) | `3cf3cd836f3f` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/final_integration_inventory.md](cs50/archive/2026-10/final_integration_inventory.md) | `c0faba36a2f6` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/first_llm_quality_report.md](cs50/archive/2026-10/first_llm_quality_report.md) | `c07df185236c` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/full_coverage_report.md](cs50/archive/2026-10/full_coverage_report.md) | `e09802f31180` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/github_integration_status_2026-10-14.md](cs50/archive/2026-10/github_integration_status_2026-10-14.md) | `f6ff7b89b67a` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/lazy_marvin_initialization.md](cs50/archive/2026-10/lazy_marvin_initialization.md) | `9ef32639327e` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/llm_pilot_runtime_report.md](cs50/archive/2026-10/llm_pilot_runtime_report.md) | `4ae3f0bf5067` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/llm_smoke_preparation.md](cs50/archive/2026-10/llm_smoke_preparation.md) | `21fbffb91d62` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/material_regression_report.md](cs50/archive/2026-10/material_regression_report.md) | `825a33c8f9b1` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/math_normalization_import_fix.md](cs50/archive/2026-10/math_normalization_import_fix.md) | `157ce6d7e865` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/optional_sdk_lazy_import_report.md](cs50/archive/2026-10/optional_sdk_lazy_import_report.md) | `bbcf035c5e00` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/portable_pilot_test_report.md](cs50/archive/2026-10/portable_pilot_test_report.md) | `2df09548cde4` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/post_merge_audit.md](cs50/archive/2026-10/post_merge_audit.md) | `a4c0ddeb72c1` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/project_consolidation_document_index.md](cs50/archive/2026-10/project_consolidation_document_index.md) | `078fb120cfe2` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/quality_synthetic_boundaries_report.md](cs50/archive/2026-10/quality_synthetic_boundaries_report.md) | `718832a37cb7` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/selection_preview.md](cs50/archive/2026-10/selection_preview.md) | `a957fc1a4906` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/six_course_completion_report.md](cs50/archive/2026-10/six_course_completion_report.md) | `6f0709d1a9ec` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/srt_knowledge_integration_report.md](cs50/archive/2026-10/srt_knowledge_integration_report.md) | `da67be4ede7d` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/timed_knowledge_selection_report.md](cs50/archive/2026-10/timed_knowledge_selection_report.md) | `d7cdf308a5bc` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/transcript_import_report.md](cs50/archive/2026-10/transcript_import_report.md) | `72d4441810fd` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/transcript_index_e2e_report.md](cs50/archive/2026-10/transcript_index_e2e_report.md) | `04b9615c1879` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/transcript_index_regression_report.md](cs50/archive/2026-10/transcript_index_regression_report.md) | `434545984796` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/transcript_knowledge_integration_plan.md](cs50/archive/2026-10/transcript_knowledge_integration_plan.md) | `6d5be15b9609` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/uv_installed_integration_report.md](cs50/archive/2026-10/uv_installed_integration_report.md) | `75cb73781e5b` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/archive/2026-10/week_fixture_fetch_report.md](cs50/archive/2026-10/week_fixture_fetch_report.md) | `e0808e2d950e` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/cs50/contracts/cs50_budget_contract.md](cs50/contracts/cs50_budget_contract.md) | `61e3f23a597b` / 1 | bestehender fachlicher Vertrag | src/tools_knowledge/cs50_checkpoint.py; src/tools_lecture/adapt_cs50.py | behalten; jeweilige Freigaben/Schema- und Quellenbindung beachten |
| [docs/cs50/contracts/cs50_knowledge_checkpoint.md](cs50/contracts/cs50_knowledge_checkpoint.md) | `ecfff7c132d0` / 1 | bestehender fachlicher Vertrag | src/tools_knowledge/cs50_checkpoint.py; src/tools_lecture/adapt_cs50.py | behalten; jeweilige Freigaben/Schema- und Quellenbindung beachten |
| [docs/cs50/contracts/cs50_metadata_forwarding.md](cs50/contracts/cs50_metadata_forwarding.md) | `bed1b255e749` / 1 | bestehender fachlicher Vertrag | src/tools_knowledge/cs50_checkpoint.py; src/tools_lecture/adapt_cs50.py | behalten; jeweilige Freigaben/Schema- und Quellenbindung beachten |
| [docs/cs50/contracts/cs50_portable_inputs.md](cs50/contracts/cs50_portable_inputs.md) | `3aeb6d7eb807` / 1 | bestehender fachlicher Vertrag | src/tools_knowledge/cs50_checkpoint.py; src/tools_lecture/adapt_cs50.py | behalten; jeweilige Freigaben/Schema- und Quellenbindung beachten |
| [docs/cs50/contracts/discovery.md](cs50/contracts/discovery.md) | `eca80cbe0179` / 1 | bestehender fachlicher Vertrag | src/tools_knowledge/cs50_checkpoint.py; src/tools_lecture/adapt_cs50.py | behalten; jeweilige Freigaben/Schema- und Quellenbindung beachten |
| [docs/cs50/contracts/knowledge_index.md](cs50/contracts/knowledge_index.md) | `17145bd92902` / 1 | geplanter / noch unvollständiger Vertrag | src/model_transcribe/data_transcribe.py; src/tools_rag/cs50_knowledge_index.py | nicht als vollständig integriert markieren; TXT-/Knowledge-Index-Grenzen offen |
| [docs/cs50/contracts/knowledge_source_id_contract.md](cs50/contracts/knowledge_source_id_contract.md) | `fed5c7a3c3de` / 1 | bestehender fachlicher Vertrag | src/tools_knowledge/cs50_checkpoint.py; src/tools_lecture/adapt_cs50.py | behalten; jeweilige Freigaben/Schema- und Quellenbindung beachten |
| [docs/cs50/contracts/knowledge_transcript_provenance.md](cs50/contracts/knowledge_transcript_provenance.md) | `3cbe7f9c04ef` / 1 | bestehender fachlicher Vertrag | src/tools_knowledge/cs50_checkpoint.py; src/tools_lecture/adapt_cs50.py | behalten; jeweilige Freigaben/Schema- und Quellenbindung beachten |
| [docs/cs50/contracts/material_artifacts.md](cs50/contracts/material_artifacts.md) | `1c5ad258e443` / 1 | bestehender fachlicher Vertrag | src/tools_materials/processing.py; tests/test_cs50_material_quality.py | behalten; jeweilige Freigaben/Schema- und Quellenbindung beachten |
| [docs/cs50/contracts/material_code.md](cs50/contracts/material_code.md) | `fb50fc1dc825` / 1 | bestehender fachlicher Vertrag | src/tools_materials/processing.py; tests/test_cs50_material_quality.py | behalten; jeweilige Freigaben/Schema- und Quellenbindung beachten |
| [docs/cs50/contracts/material_download.md](cs50/contracts/material_download.md) | `5e8b9ce9ae01` / 1 | bestehender fachlicher Vertrag | src/tools_materials/processing.py; tests/test_cs50_material_quality.py | behalten; jeweilige Freigaben/Schema- und Quellenbindung beachten |
| [docs/cs50/contracts/material_mapping.md](cs50/contracts/material_mapping.md) | `3b6a6f86e750` / 2 | bestehender fachlicher Vertrag | src/tools_materials/processing.py; tests/test_cs50_material_quality.py | behalten; jeweilige Freigaben/Schema- und Quellenbindung beachten |
| [docs/cs50/contracts/material_processing.md](cs50/contracts/material_processing.md) | `20d44dd19cd2` / 1 | bestehender fachlicher Vertrag | src/tools_materials/processing.py; tests/test_cs50_material_quality.py | behalten; jeweilige Freigaben/Schema- und Quellenbindung beachten |
| [docs/cs50/contracts/material_quality.md](cs50/contracts/material_quality.md) | `3915bcac0ac5` / 1 | bestehender fachlicher Vertrag | src/tools_materials/processing.py; tests/test_cs50_material_quality.py | behalten; jeweilige Freigaben/Schema- und Quellenbindung beachten |
| [docs/cs50/contracts/selection_policy.md](cs50/contracts/selection_policy.md) | `dd5fdf413eef` / 1 | bestehender fachlicher Vertrag | src/tools_knowledge/cs50_checkpoint.py; src/tools_lecture/adapt_cs50.py | behalten; jeweilige Freigaben/Schema- und Quellenbindung beachten |
| [docs/cs50/contracts/timeless_transcript_architecture.md](cs50/contracts/timeless_transcript_architecture.md) | `b6bc47065466` / 1 | geplanter / noch unvollständiger Vertrag | src/model_transcribe/data_transcribe.py; src/tools_rag/cs50_knowledge_index.py | nicht als vollständig integriert markieren; TXT-/Knowledge-Index-Grenzen offen |
| [docs/cs50/contracts/transcript_embeddings.md](cs50/contracts/transcript_embeddings.md) | `4db65f4fb383` / 1 | bestehender fachlicher Vertrag | src/tools_rag/cs50_ingestion.py; src/tools_rag/cs50_retrieval.py | behalten; jeweilige Freigaben/Schema- und Quellenbindung beachten |
| [docs/cs50/contracts/transcript_index.md](cs50/contracts/transcript_index.md) | `1de94d8750b1` / 1 | bestehender fachlicher Vertrag | src/tools_rag/cs50_ingestion.py; src/tools_rag/cs50_retrieval.py | behalten; jeweilige Freigaben/Schema- und Quellenbindung beachten |
| [docs/cs50/contracts/transcript_metadata_model_contract.md](cs50/contracts/transcript_metadata_model_contract.md) | `e607ada448ea` / 1 | bestehender fachlicher Vertrag | src/tools_knowledge/cs50_checkpoint.py; src/tools_lecture/adapt_cs50.py | behalten; jeweilige Freigaben/Schema- und Quellenbindung beachten |
| [docs/cs50/evaluation/cs50_quality_evaluation.md](cs50/evaluation/cs50_quality_evaluation.md) | `c5385f060c58` / 1 | paket-/methodenspezifische Evaluation | zugehörige tests/test_cs50_*.py / Evaluationsmodule | behalten; technische Nachweise von fachlicher Qualität trennen |
| [docs/cs50/evaluation/html_notes_v2.md](cs50/evaluation/html_notes_v2.md) | `d8466bf93048` / 1 | paket-/methodenspezifische Evaluation | zugehörige tests/test_cs50_*.py / Evaluationsmodule | behalten; technische Nachweise von fachlicher Qualität trennen |
| [docs/cs50/evaluation/material_html.md](cs50/evaluation/material_html.md) | `cad5065798db` / 1 | historischer v1-Testnachweis | src/tools_materials/parse_html.py; src/tools_materials/parse_pdf.py | v2-Verweis ergänzt, ursprüngliche Zahlen erhalten |
| [docs/cs50/evaluation/material_parser_matrix.md](cs50/evaluation/material_parser_matrix.md) | `4d4fe4283d77` / 2 | paket-/methodenspezifische Evaluation | zugehörige tests/test_cs50_*.py / Evaluationsmodule | behalten; technische Nachweise von fachlicher Qualität trennen |
| [docs/cs50/evaluation/material_pdf.md](cs50/evaluation/material_pdf.md) | `1d599e441b85` / 1 | historischer v1-Testnachweis | src/tools_materials/parse_html.py; src/tools_materials/parse_pdf.py | v2-Verweis ergänzt, ursprüngliche Zahlen erhalten |
| [docs/cs50/evaluation/material_quality.md](cs50/evaluation/material_quality.md) | `f874c8240b44` / 1 | paket-/methodenspezifische Evaluation | zugehörige tests/test_cs50_*.py / Evaluationsmodule | behalten; technische Nachweise von fachlicher Qualität trennen |
| [docs/cs50/evaluation/material_tests.md](cs50/evaluation/material_tests.md) | `4b971f1c9d85` / 2 | paket-/methodenspezifische Evaluation | zugehörige tests/test_cs50_*.py / Evaluationsmodule | behalten; technische Nachweise von fachlicher Qualität trennen |
| [docs/cs50/evaluation/pdf_v2.md](cs50/evaluation/pdf_v2.md) | `7222b73b71dc` / 1 | paket-/methodenspezifische Evaluation | zugehörige tests/test_cs50_*.py / Evaluationsmodule | behalten; technische Nachweise von fachlicher Qualität trennen |
| [docs/cs50/evaluation/precise_evidence_comparison_report.md](cs50/evaluation/precise_evidence_comparison_report.md) | `edcad1851821` / 1 | paket-/methodenspezifische Evaluation | zugehörige tests/test_cs50_*.py / Evaluationsmodule | behalten; technische Nachweise von fachlicher Qualität trennen |
| [docs/cs50/evaluation/transcript_retrieval.md](cs50/evaluation/transcript_retrieval.md) | `0b4b8e7dfe8b` / 1 | paket-/methodenspezifische Evaluation | zugehörige tests/test_cs50_*.py / Evaluationsmodule | behalten; technische Nachweise von fachlicher Qualität trennen |
| [docs/cs50/operations/archive_cleanup_report.md](cs50/operations/archive_cleanup_report.md) | `27e54e470a77` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/archive_manifest.md](cs50/operations/archive_manifest.md) | `681f8cfb0a6c` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/cs50_batch_execution.md](cs50/operations/cs50_batch_execution.md) | `846f73aadbf1` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/cs50_course_scheduler.md](cs50/operations/cs50_course_scheduler.md) | `194a0db82ffd` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/cs50_lecture_completion.md](cs50/operations/cs50_lecture_completion.md) | `5eecf1489efb` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/cs50_lecture_runner.md](cs50/operations/cs50_lecture_runner.md) | `3c9a8978a316` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/cs50_pipeline_test_matrix.md](cs50/operations/cs50_pipeline_test_matrix.md) | `a2b922aa510d` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/cs50_schedule_reporting.md](cs50/operations/cs50_schedule_reporting.md) | `b5b0179e18a1` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/historical_pr_review.md](cs50/operations/historical_pr_review.md) | `a4d865d545c3` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/knowledge_input_integration_report.md](cs50/operations/knowledge_input_integration_report.md) | `3bc061e6372c` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/knowledge_selection_preview.md](cs50/operations/knowledge_selection_preview.md) | `f49d8f194b9f` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/lecture_adapter_report.md](cs50/operations/lecture_adapter_report.md) | `65640115e27e` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/local_cleanup_inventory.md](cs50/operations/local_cleanup_inventory.md) | `82dbbe085353` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/material_completion.md](cs50/operations/material_completion.md) | `b764be2eaf63` / 2 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/material_coverage.md](cs50/operations/material_coverage.md) | `71b977d380c5` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/material_gap_analysis.md](cs50/operations/material_gap_analysis.md) | `78793d205714` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/material_ingestion.md](cs50/operations/material_ingestion.md) | `3cea7ff91468` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/six_course_fixture_provenance.md](cs50/operations/six_course_fixture_provenance.md) | `1f175489b968` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/six_course_overview.md](cs50/operations/six_course_overview.md) | `30786a9f75a6` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/six_course_preview.md](cs50/operations/six_course_preview.md) | `7a892661942c` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/six_course_video_preview.md](cs50/operations/six_course_video_preview.md) | `7f6f2b669646` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/srt_executor_report.md](cs50/operations/srt_executor_report.md) | `559441abf9b4` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/transcript_index_architecture.md](cs50/operations/transcript_index_architecture.md) | `9fbfc613cfd2` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/transcript_index_cli.md](cs50/operations/transcript_index_cli.md) | `c5ca0a2500af` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/transcript_index_completion.md](cs50/operations/transcript_index_completion.md) | `9d79cd85bf4c` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/transcript_ingestion.md](cs50/operations/transcript_ingestion.md) | `b7d4312be602` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50/operations/transcript_retrieval.md](cs50/operations/transcript_retrieval.md) | `e6a85ba9b2d2` / 1 | Betriebsvertrag / datierter Snapshotbericht | src/tools_lecture/; src/tools_knowledge/; scripts/cs50_*.py | behalten; Commit-/Fixture-/Testscope im Dokument gilt, kein Livezustand |
| [docs/cs50_pipeline_completion_audit.md](cs50_pipeline_completion_audit.md) | `237822a7a400` / 1 | aktueller Archivverweis | docs/cs50/archive/2026-10/ | kompatiblen Rootpfad behalten; Inhalt im Archiv |
| [docs/cs50_pipeline_completion_plan.md](cs50_pipeline_completion_plan.md) | `7e99821d01bc` / 1 | aktueller Archivverweis | docs/cs50/archive/2026-10/ | kompatiblen Rootpfad behalten; Inhalt im Archiv |
| [docs/development.md](development.md) | `a200131fb813` / 1 | aktueller Einstieg, überarbeitet | src/job_control/registry.py; src/workflows/definition.py | aktuelle Paketstände/Tests abgeglichen; behalten |
| [docs/examples/visual_inventory/html.inventory.v1.md](examples/visual_inventory/html.inventory.v1.md) | `e6d3362fe2e9` / 1 | synthetischer Beispielreport | zugehöriger versionierter Reportvertrag | behalten; keine Gold-/Produktivbehauptung |
| [docs/examples/visual_inventory/pdf.inventory.v1.md](examples/visual_inventory/pdf.inventory.v1.md) | `84e0ccd39988` / 1 | synthetischer Beispielreport | zugehöriger versionierter Reportvertrag | behalten; keine Gold-/Produktivbehauptung |
| [docs/job_control/README.md](job_control/README.md) | `4f6c71aec7fa` / 2 | aktueller C16-Vertrag | src/job_control/; tests/test_job_control.py; tests/test_job_executor.py | C17-Verweise korrigiert; Default/optional C18 trennen |
| [docs/job_control/api.md](job_control/api.md) | `33877d95c51e` / 1 | aktueller C16-Vertrag | src/job_control/; tests/test_job_control.py; tests/test_job_executor.py | C17-Verweise korrigiert; Default/optional C18 trennen |
| [docs/job_control/architecture.md](job_control/architecture.md) | `552cada7eedb` / 1 | aktueller C16-Vertrag | src/job_control/; tests/test_job_control.py; tests/test_job_executor.py | C17-Verweise korrigiert; Default/optional C18 trennen |
| [docs/job_control/integration.md](job_control/integration.md) | `a5ecdd9e6326` / 1 | aktueller C16-Vertrag | src/job_control/; tests/test_job_control.py; tests/test_job_executor.py | C17-Verweise korrigiert; Default/optional C18 trennen |
| [docs/job_control/operations.md](job_control/operations.md) | `5365ea47ec79` / 1 | aktueller C16-Vertrag | src/job_control/; tests/test_job_control.py; tests/test_job_executor.py | C17-Verweise korrigiert; Default/optional C18 trennen |
| [docs/job_control/validation.md](job_control/validation.md) | `c64dae0a9881` / 1 | historischer Paket-Testnachweis | src/job_control/; tests/test_job_control.py; tests/test_job_executor.py | C17-Verweise korrigiert; Default/optional C18 trennen |
| [docs/knowledge_consolidation_hardening.md](knowledge_consolidation_hardening.md) | `ef5bdb0348c1` / 1 | aktueller C12-Vertrag | src/tools_knowledge/consolidation_run.py; tests/test_consolidation_hardening.py | behalten; semantische Liveausführung nicht freigeben |
| [docs/knowledge_consolidation_test_results.md](knowledge_consolidation_test_results.md) | `8ce9b65590a3` / 1 | historischer Paket-Testnachweis | src/tools_knowledge/consolidation_run.py; tests/test_consolidation_hardening.py | behalten; semantische Liveausführung nicht freigeben |
| [docs/logger_notes.md](logger_notes.md) | `e027afbab767` / 1 | unklar / historischer Entwurf | src/core/logger.py | behalten; manuelle Nutzungs-/Archivprüfung |
| [docs/math_evaluation/README.md](math_evaluation/README.md) | `75a588b6f34d` / 1 | aktueller C11-Vertrag | src/tools_evaluation/evaluate_math.py; tests/test_math_formula_evaluation.py | behalten; synthetisch/real und undetermined trennen |
| [docs/math_evaluation/example/summary.md](math_evaluation/example/summary.md) | `9b67cb0db2f8` / 1 | synthetischer Beispielreport | zugehöriger versionierter Reportvertrag | behalten; keine Gold-/Produktivbehauptung |
| [docs/math_evaluation/validation.md](math_evaluation/validation.md) | `1b64773e82a3` / 1 | historischer Paket-Testnachweis | src/tools_evaluation/evaluate_math.py; tests/test_math_formula_evaluation.py | behalten; synthetisch/real und undetermined trennen |
| [docs/monitoring/README.md](monitoring/README.md) | `f520ef772846` / 1 | aktueller Konfigurationsvertrag | src/core/pipeline_metrics.py; src/job_control/metrics.py; tests/test_monitoring_config.py | C16-Queue/Exporter und elf C18-Labels ergänzt; kein Livebetrieb behauptet |
| [docs/monitoring/audit.md](monitoring/audit.md) | `bffe1c08bf0b` / 1 | historischer Paketbefund | src/core/pipeline_metrics.py; src/job_control/metrics.py; tests/test_monitoring_config.py | C16-Queue/Exporter und elf C18-Labels ergänzt; kein Livebetrieb behauptet |
| [docs/monitoring/operations.md](monitoring/operations.md) | `2f39dbe0aa86` / 1 | aktueller Konfigurationsvertrag | src/core/pipeline_metrics.py; src/job_control/metrics.py; tests/test_monitoring_config.py | C16-Queue/Exporter und elf C18-Labels ergänzt; kein Livebetrieb behauptet |
| [docs/monitoring/pipeline-metrics.md](monitoring/pipeline-metrics.md) | `a456bf852ac0` / 1 | aktueller Konfigurationsvertrag | src/core/pipeline_metrics.py; src/job_control/metrics.py; tests/test_monitoring_config.py | C16-Queue/Exporter und elf C18-Labels ergänzt; kein Livebetrieb behauptet |
| [docs/monitoring/validation.md](monitoring/validation.md) | `1ae7e9d200f9` / 1 | historischer Paketbefund | src/core/pipeline_metrics.py; src/job_control/metrics.py; tests/test_monitoring_config.py | C16-Queue/Exporter und elf C18-Labels ergänzt; kein Livebetrieb behauptet |
| [docs/project_consolidation_report.md](project_consolidation_report.md) | `e283a649ad8a` / 1 | historischer Nachweis | damaliger Commit / Archivmanifest | erhalten; damalige Zahlen nicht als neuen Gesamttest ausgeben |
| [docs/visual_inventory.md](visual_inventory.md) | `f4f2d7b011f1` / 1 | aktueller C13-Vertrag | src/tools_materials/visual_inventory.py; tests/test_cs50_visual_inventory.py | behalten; technische Inventur ist kein Enrichment |
| [docs/visual_inventory_test_results.md](visual_inventory_test_results.md) | `c1692428c142` / 1 | historischer Paket-Testnachweis | src/tools_materials/visual_inventory.py; tests/test_cs50_visual_inventory.py | behalten; technische Inventur ist kein Enrichment |
| [docs/workflows/README.md](workflows/README.md) | `4453a7ba6e53` / 1 | aktueller C18-Vertrag | src/workflows/; tests/test_cs50_workflows.py | behalten; PDF-/UI-/Providergrenzen bleiben offen |
| [docs/workflows/architecture.md](workflows/architecture.md) | `7742ab420bd9` / 1 | aktueller C18-Vertrag | src/workflows/; tests/test_cs50_workflows.py | behalten; PDF-/UI-/Providergrenzen bleiben offen |
| [docs/workflows/example-report.v1.md](workflows/example-report.v1.md) | `49867afcd1eb` / 1 | synthetischer Beispielreport | zugehöriger versionierter Reportvertrag | behalten; keine Gold-/Produktivbehauptung |
| [docs/workflows/validation.md](workflows/validation.md) | `afa1e5468a35` / 1 | historischer Paket-Testnachweis | src/workflows/; tests/test_cs50_workflows.py | behalten; PDF-/UI-/Providergrenzen bleiben offen |
| [frontend/chat_app/README.md](../frontend/chat_app/README.md) | `781694d0d258` / 1 | Legacy, Grenze korrigiert | st_chat_app.py; frontend/chat_app/chat_page.py | kein geprüfter Start; Zielzuständigkeit UI, nicht löschen |
| [monitoring/grafana/potential_metrics.md](../monitoring/grafana/potential_metrics.md) | `5d0793c07cf5` / 1 | unklar / historischer Entwurf | historische Planung, kein aktiver Vertrag | behalten; manuelle Nutzungs-/Archivprüfung |
| [monitoring/prometheus/targets/README.md](../monitoring/prometheus/targets/README.md) | `d2242e6af22b` / 1 | aktueller Konfigurationsvertrag | src/core/pipeline_metrics.py; src/job_control/metrics.py; tests/test_monitoring_config.py | C16-Queue/Exporter und elf C18-Labels ergänzt; kein Livebetrieb behauptet |
| [src/prio_list.md](../src/prio_list.md) | `2c4334d263bb` / 2 | unklar / historischer Entwurf | historische Planung, kein aktiver Vertrag | behalten; manuelle Nutzungs-/Archivprüfung |
| [tests/fixtures/consolidation/README.md](../tests/fixtures/consolidation/README.md) | `236723a91f14` / 1 | synthetische Fixturebeschreibung | tests/fixtures/; zugehörige Paketsuite | behalten; keine reale Modellqualität ableiten |
| [tests/fixtures/job_control/README.md](../tests/fixtures/job_control/README.md) | `c642c978eccb` / 1 | synthetische Fixturebeschreibung | tests/fixtures/; zugehörige Paketsuite | behalten; keine reale Modellqualität ableiten |
| [tests/fixtures/visual_inventory/README.md](../tests/fixtures/visual_inventory/README.md) | `b17acc300f0f` / 1 | synthetische Fixturebeschreibung | tests/fixtures/; zugehörige Paketsuite | behalten; keine reale Modellqualität ableiten |
| [workers/cs50/README.md](../workers/cs50/README.md) | `ac9b90fe30c0` / 1 | aktueller Profilvertrag; alte Laufzahlen | workers/cs50/pyproject.toml; workers/cs50_index/pyproject.toml | historischen Installationsnachweis behalten; aktuelle Prüfgrenzen ergänzt |
| [workers/cs50_index/README.md](../workers/cs50_index/README.md) | `b346007fe701` / 1 | aktueller Profilvertrag; alte Laufzahlen | workers/cs50/pyproject.toml; workers/cs50_index/pyproject.toml | historischen Installationsnachweis behalten; aktuelle Prüfgrenzen ergänzt |

## Frühere Pfade und nur lokal vorhandene Dokumente

Die folgende Liste enthält alle 50 im aktuellen Master fehlenden Pfade aus den
untersuchten Worktreevarianten. Davon sind 49 über konkrete vorhandene Archiv-/
Vertragspfade erhalten. Inhaltsunterschiede durch frühere Link-/Pfadkorrekturen
werden als solche benannt; sie sind keine behauptete Byteidentität. Die eine
zusätzliche Benutzer-Roadmap bleibt unverändert außerhalb des PRs.

| Früherer / lokaler Pfad | Heutiger Fundort | Einordnung / Maßnahme |
| --- | --- | --- |
| lokale Benutzerplanung (Details privat) | nur lokal vorhanden | unverändert/unversioniert behalten; kein Mastervertrag |
| `docs/course_sources/cs50/analysis.md` | [docs/cs50/archive/2026-10/analysis.md](cs50/archive/2026-10/analysis.md) | Archivmanifest; Inhalt mit historischen/editorialen Änderungen erhalten; nicht zurückkopieren |
| `docs/course_sources/cs50/discovery.md` | [docs/cs50/contracts/discovery.md](cs50/contracts/discovery.md) | Archivmanifest; Inhalt mit historischen/editorialen Änderungen erhalten; nicht zurückkopieren |
| `docs/course_sources/cs50/extraction_report.md` | [docs/cs50/archive/2026-10/extraction_report.md](cs50/archive/2026-10/extraction_report.md) | Archivmanifest; Inhalt mit historischen/editorialen Änderungen erhalten; nicht zurückkopieren |
| `docs/course_sources/cs50/first_llm_quality_report.md` | [docs/cs50/archive/2026-10/first_llm_quality_report.md](cs50/archive/2026-10/first_llm_quality_report.md) | Archivmanifest; Inhalt mit historischen/editorialen Änderungen erhalten; nicht zurückkopieren |
| `docs/course_sources/cs50/full_coverage_report.md` | [docs/cs50/archive/2026-10/full_coverage_report.md](cs50/archive/2026-10/full_coverage_report.md) | Archivmanifest; Inhalt mit historischen/editorialen Änderungen erhalten; nicht zurückkopieren |
| `docs/course_sources/cs50/knowledge_input_integration_report.md` | [docs/cs50/operations/knowledge_input_integration_report.md](cs50/operations/knowledge_input_integration_report.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/course_sources/cs50/knowledge_selection_preview.md` | [docs/cs50/operations/knowledge_selection_preview.md](cs50/operations/knowledge_selection_preview.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/course_sources/cs50/knowledge_source_id_contract.md` | [docs/cs50/contracts/knowledge_source_id_contract.md](cs50/contracts/knowledge_source_id_contract.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/course_sources/cs50/knowledge_transcript_provenance.md` | [docs/cs50/contracts/knowledge_transcript_provenance.md](cs50/contracts/knowledge_transcript_provenance.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/course_sources/cs50/lazy_marvin_initialization.md` | [docs/cs50/archive/2026-10/lazy_marvin_initialization.md](cs50/archive/2026-10/lazy_marvin_initialization.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/course_sources/cs50/lecture_adapter_report.md` | [docs/cs50/operations/lecture_adapter_report.md](cs50/operations/lecture_adapter_report.md) | Archivmanifest; Inhalt mit historischen/editorialen Änderungen erhalten; nicht zurückkopieren |
| `docs/course_sources/cs50/llm_pilot_runtime_report.md` | [docs/cs50/archive/2026-10/llm_pilot_runtime_report.md](cs50/archive/2026-10/llm_pilot_runtime_report.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/course_sources/cs50/llm_smoke_preparation.md` | [docs/cs50/archive/2026-10/llm_smoke_preparation.md](cs50/archive/2026-10/llm_smoke_preparation.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/course_sources/cs50/math_normalization_import_fix.md` | [docs/cs50/archive/2026-10/math_normalization_import_fix.md](cs50/archive/2026-10/math_normalization_import_fix.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/course_sources/cs50/optional_sdk_lazy_import_report.md` | [docs/cs50/archive/2026-10/optional_sdk_lazy_import_report.md](cs50/archive/2026-10/optional_sdk_lazy_import_report.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/course_sources/cs50/portable_pilot_test_report.md` | [docs/cs50/archive/2026-10/portable_pilot_test_report.md](cs50/archive/2026-10/portable_pilot_test_report.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/course_sources/cs50/post_merge_audit.md` | [docs/cs50/archive/2026-10/post_merge_audit.md](cs50/archive/2026-10/post_merge_audit.md) | Archivmanifest; Inhalt mit historischen/editorialen Änderungen erhalten; nicht zurückkopieren |
| `docs/course_sources/cs50/precise_evidence_comparison_report.md` | [docs/cs50/evaluation/precise_evidence_comparison_report.md](cs50/evaluation/precise_evidence_comparison_report.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/course_sources/cs50/quality_synthetic_boundaries_report.md` | [docs/cs50/archive/2026-10/quality_synthetic_boundaries_report.md](cs50/archive/2026-10/quality_synthetic_boundaries_report.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/course_sources/cs50/selection_policy.md` | [docs/cs50/contracts/selection_policy.md](cs50/contracts/selection_policy.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/course_sources/cs50/selection_preview.md` | [docs/cs50/archive/2026-10/selection_preview.md](cs50/archive/2026-10/selection_preview.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/course_sources/cs50/six_course_completion_report.md` | [docs/cs50/archive/2026-10/six_course_completion_report.md](cs50/archive/2026-10/six_course_completion_report.md) | Archivmanifest; Inhalt mit historischen/editorialen Änderungen erhalten; nicht zurückkopieren |
| `docs/course_sources/cs50/six_course_fixture_provenance.md` | [docs/cs50/operations/six_course_fixture_provenance.md](cs50/operations/six_course_fixture_provenance.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/course_sources/cs50/six_course_overview.md` | [docs/cs50/operations/six_course_overview.md](cs50/operations/six_course_overview.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/course_sources/cs50/six_course_preview.md` | [docs/cs50/operations/six_course_preview.md](cs50/operations/six_course_preview.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/course_sources/cs50/six_course_video_preview.md` | [docs/cs50/operations/six_course_video_preview.md](cs50/operations/six_course_video_preview.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/course_sources/cs50/srt_executor_report.md` | [docs/cs50/operations/srt_executor_report.md](cs50/operations/srt_executor_report.md) | Archivmanifest; Inhalt mit historischen/editorialen Änderungen erhalten; nicht zurückkopieren |
| `docs/course_sources/cs50/srt_knowledge_integration_report.md` | [docs/cs50/archive/2026-10/srt_knowledge_integration_report.md](cs50/archive/2026-10/srt_knowledge_integration_report.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/course_sources/cs50/timed_knowledge_selection_report.md` | [docs/cs50/archive/2026-10/timed_knowledge_selection_report.md](cs50/archive/2026-10/timed_knowledge_selection_report.md) | Archivmanifest; Inhalt mit historischen/editorialen Änderungen erhalten; nicht zurückkopieren |
| `docs/course_sources/cs50/timeless_transcript_architecture.md` | [docs/cs50/contracts/timeless_transcript_architecture.md](cs50/contracts/timeless_transcript_architecture.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/course_sources/cs50/transcript_import_report.md` | [docs/cs50/archive/2026-10/transcript_import_report.md](cs50/archive/2026-10/transcript_import_report.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/course_sources/cs50/transcript_knowledge_integration_plan.md` | [docs/cs50/archive/2026-10/transcript_knowledge_integration_plan.md](cs50/archive/2026-10/transcript_knowledge_integration_plan.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/course_sources/cs50/transcript_metadata_model_contract.md` | [docs/cs50/contracts/transcript_metadata_model_contract.md](cs50/contracts/transcript_metadata_model_contract.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/course_sources/cs50/uv_installed_integration_report.md` | [docs/cs50/archive/2026-10/uv_installed_integration_report.md](cs50/archive/2026-10/uv_installed_integration_report.md) | Archivmanifest; Inhalt mit historischen/editorialen Änderungen erhalten; nicht zurückkopieren |
| `docs/course_sources/cs50/week_fixture_fetch_report.md` | [docs/cs50/archive/2026-10/week_fixture_fetch_report.md](cs50/archive/2026-10/week_fixture_fetch_report.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/cs50_batch_execution.md` | [docs/cs50/operations/cs50_batch_execution.md](cs50/operations/cs50_batch_execution.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/cs50_budget_contract.md` | [docs/cs50/contracts/cs50_budget_contract.md](cs50/contracts/cs50_budget_contract.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/cs50_course_scheduler.md` | [docs/cs50/operations/cs50_course_scheduler.md](cs50/operations/cs50_course_scheduler.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/cs50_knowledge_checkpoint.md` | [docs/cs50/contracts/cs50_knowledge_checkpoint.md](cs50/contracts/cs50_knowledge_checkpoint.md) | Archivmanifest; Inhalt mit historischen/editorialen Änderungen erhalten; nicht zurückkopieren |
| `docs/cs50_knowledge_checkpoint_test_report.md` | [docs/cs50/archive/2026-10/cs50_knowledge_checkpoint_test_report.md](cs50/archive/2026-10/cs50_knowledge_checkpoint_test_report.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/cs50_lecture_completion.md` | [docs/cs50/operations/cs50_lecture_completion.md](cs50/operations/cs50_lecture_completion.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/cs50_lecture_runner.md` | [docs/cs50/operations/cs50_lecture_runner.md](cs50/operations/cs50_lecture_runner.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/cs50_metadata_forwarding.md` | [docs/cs50/contracts/cs50_metadata_forwarding.md](cs50/contracts/cs50_metadata_forwarding.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/cs50_pipeline_completion_report.md` | [docs/cs50/archive/2026-10/cs50_pipeline_completion_report.md](cs50/archive/2026-10/cs50_pipeline_completion_report.md) | Archivmanifest; Inhalt mit historischen/editorialen Änderungen erhalten; nicht zurückkopieren |
| `docs/cs50_pipeline_test_matrix.md` | [docs/cs50/operations/cs50_pipeline_test_matrix.md](cs50/operations/cs50_pipeline_test_matrix.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/cs50_portable_inputs.md` | [docs/cs50/contracts/cs50_portable_inputs.md](cs50/contracts/cs50_portable_inputs.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/cs50_quality_evaluation.md` | [docs/cs50/evaluation/cs50_quality_evaluation.md](cs50/evaluation/cs50_quality_evaluation.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/cs50_schedule_reporting.md` | [docs/cs50/operations/cs50_schedule_reporting.md](cs50/operations/cs50_schedule_reporting.md) | exakter SHA-256-Treffer an explizitem Archiv-/Vertragspfad; nicht zurückkopieren |
| `docs/github_integration_status_2026-10-14.md` | [docs/cs50/archive/2026-10/github_integration_status_2026-10-14.md](cs50/archive/2026-10/github_integration_status_2026-10-14.md) | Archivmanifest; Inhalt mit historischen/editorialen Änderungen erhalten; nicht zurückkopieren |

## JSON-Verträge, Gold-/Beispielartefakte unter docs

Diese Dateien sind im vollständigen Dateiinventar mit Git-/SHA-256-Identität
enthalten. Sie werden weder migriert noch aus neuen Vorhersagen als unabhängige
Goldreferenzen erzeugt. JSON-Syntax-/Schema-/Beispieltests laufen in den jeweiligen
Paketsuiten; historische Ergebniszahlen bleiben an ihren ursprünglichen Scope gebunden.

| Artefakt | Rolle / Maßnahme |
| --- | --- |
| [docs/course_sources/cs50/cs50_lecture_plan.v1.json](course_sources/cs50/cs50_lecture_plan.v1.json) | source/fixture; behalten; Version/Beispiel-/Goldscope beachten |
| [docs/course_sources/cs50/manifest.json](course_sources/cs50/manifest.json) | source/fixture; behalten; Version/Beispiel-/Goldscope beachten |
| [docs/course_sources/cs50/regression_manifest.json](course_sources/cs50/regression_manifest.json) | source/fixture; behalten; Version/Beispiel-/Goldscope beachten |
| [docs/cs50/evaluation/python0_retrieval_questions.v1.json](cs50/evaluation/python0_retrieval_questions.v1.json) | schema_or_recorded_example; behalten; Version/Beispiel-/Goldscope beachten |
| [docs/cs50/examples/material-quality-html.v1.json](cs50/examples/material-quality-html.v1.json) | schema_or_recorded_example; behalten; Version/Beispiel-/Goldscope beachten |
| [docs/cs50/examples/material-quality-pdf.v1.json](cs50/examples/material-quality-pdf.v1.json) | schema_or_recorded_example; behalten; Version/Beispiel-/Goldscope beachten |
| [docs/examples/consolidation-run.v1.json](examples/consolidation-run.v1.json) | schema_or_recorded_example; behalten; Version/Beispiel-/Goldscope beachten |
| [docs/examples/visual_inventory/html.inventory.v1.json](examples/visual_inventory/html.inventory.v1.json) | schema_or_recorded_example; behalten; Version/Beispiel-/Goldscope beachten |
| [docs/examples/visual_inventory/pdf.inventory.v1.json](examples/visual_inventory/pdf.inventory.v1.json) | schema_or_recorded_example; behalten; Version/Beispiel-/Goldscope beachten |
| [docs/job_control/contract.v1.json](job_control/contract.v1.json) | schema_or_recorded_example; behalten; Version/Beispiel-/Goldscope beachten |
| [docs/job_control/example-run.v1.json](job_control/example-run.v1.json) | schema_or_recorded_example; behalten; Version/Beispiel-/Goldscope beachten |
| [docs/math_evaluation/example/manifest.json](math_evaluation/example/manifest.json) | schema_or_recorded_example; behalten; Version/Beispiel-/Goldscope beachten |
| [docs/math_evaluation/example/report.json](math_evaluation/example/report.json) | schema_or_recorded_example; behalten; Version/Beispiel-/Goldscope beachten |
| [docs/math_evaluation/formula_cases.v1.json](math_evaluation/formula_cases.v1.json) | synthetic_gold; behalten; Version/Beispiel-/Goldscope beachten |
| [docs/math_evaluation/gold_references.v1.json](math_evaluation/gold_references.v1.json) | synthetic_gold; behalten; Version/Beispiel-/Goldscope beachten |
| [docs/monitoring/validation.example.json](monitoring/validation.example.json) | schema_or_recorded_example; behalten; Version/Beispiel-/Goldscope beachten |
| [docs/workflows/contract.v1.json](workflows/contract.v1.json) | schema_or_recorded_example; behalten; Version/Beispiel-/Goldscope beachten |
| [docs/workflows/example-report.v1.json](workflows/example-report.v1.json) | schema_or_recorded_example; behalten; Version/Beispiel-/Goldscope beachten |

## Zielstruktur und ungeklärte Fälle

Die vorhandenen `cs50/{contracts,operations,evaluation,archive}`, `job_control`,
`monitoring`, `math_evaluation`, `workflows` und `examples` bleiben erhalten.
[docs/README.md](README.md) ist der gemeinsame Einstieg; neue Auditbelege liegen
unter `audit/`, alte Übersichten unter `archive/2026-10/repository-overview/`.
Es gibt keine breite Ordnerumbenennung und keinen automatischen UI-Codetransfer.

Die lokalen privaten `project_cleanup_*`-Berichte und `_dev_tasks.md` wurden nur
als Metadaten erfasst; ihre Inhalte/Aktualität werden nicht behauptet. Logger-/
Prioritätsentwürfe, manuelle Legacy-Aufrufe und externe Deploymentreferenzen
bleiben offen. [Konkrete Kategorie-B-/C-Liste](cleanup_plan.md) statt stiller Löschung.
Die vier weiterhin offenen historischen PRs bleiben sichtbar; insbesondere der
TXT-Rest von #9 wurde erneut als bekannter Fehler nachgewiesen.
