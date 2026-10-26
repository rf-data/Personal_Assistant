# C24-R Integrationsinventar

Ausgangscommit: `4c057ae33d41ba98e227879cc8a51283338e4a0b`.
Sauberer Arbeitsbaum im ausschließlich verwendeten C24-R-Worktree. Aktueller
Branch `feat/c24r-retrieval_completion`; Ziel `feat/c24-retrieval-completion`.
Die Umbenennung scheitert am schreibgeschützten gemeinsamen Git-Speicher.
Lieferung daher als geprüfter Patch mit Manifest; keine Sandboxumgehung.
Im Worktree und seinen Eltern liegt keine anwendbare AGENTS.md. Sicherheitsbasis:
Auftrag und `docs/development.md`; keine privaten Settings/Secrets gelesen.

| Komponente | Implementiert | Integrationsstand | Verbleibende Lücke | Quelle/Commit | Testabdeckung |
|---|---|---|---|---|---|
| C23 ContentStore | ja | Source/SourceVersion/ParsedDocumentVersion, immutable Artefakte, Live ACL | keine neue Storagearchitektur | PR #76–#81, Basisvorfahren | content_store/models/adapters/read |
| C24 Projektion | ja | verifizierte Versionen, deterministische Records/Locator | Jobbindung | `7d1b655`, PR #84 | content_index_projection |
| FTS5 | ja | Sourcepartitionen, atomare Generation, signierte Cursor, Live Sourceprüfung | HTTP/Jobtransport | `0f3d9dd`, PR #85 | content_fts |
| Vektorretrieval | ja | bestehender opt-in Adapter | außerhalb des primären Auftrags | `12740b7`, PR #86 | content_vector |
| C16 HTTP | ja | lokale HTTPServer-/Bearer-Identitäten, Content-/Reviewrouten | Search opt-in | Basis; DEV `4259187` | job_control/content_read |
| C16/C18 Prozesse | ja | Katalog, Preview, Queue, Idempotenz, Executor/Guardian, Quarantäne | Indexprozess opt-in | Basis; DEV `c07ed9a` | job_control/job_executor/workflows |
| Retrievalevaluation | ja | unabhängige Regionen, explizite Nenner, Quellen-/Versionsbelege | reale Kandidatenvorbereitung | `5a7d050`, PR #87 | content_retrieval_evaluation/integration |
| Human Review | ja | ACL, CAS, Revisionen, Draft/Confirm, Export | Kandidaten vor Originalfreigabe | `20b8916`, PR #90 | evaluation_store |
| Realpilot | synthetischer Integrationsnachweis | vollständige Adapterkette; reale Freigaben fehlen | D07, ggf. D06, Originalwurzeln/Reviewer | `c8894ab`, PR #91 | authorized_pilot |
| Loviscach | Legacyadapter vorhanden | keine dokumentierte Originalfreigabe nachgewiesen | autorisierte Originale erforderlich | vorhandene Corpusinventare | nur synthetische Vorbereitung zulässig |

## Herkunft und Auswahl

Lokale Git-Abstammung bestätigt #85/#87/#90/#91 als Basisvorfahren; read-only
GitHub-Abgleich bestätigt alle vier als merged. Die Issues #114/#115/#107/#108
sind offen und bestätigen die verbleibenden Verträge/Gates. UI PR #7 ist durch
#108/#91 referenziert; kein UI-Code wird übernommen oder geändert.
DEV-01A enthält den isolierten Featurecommit `4259187a3403253595e6388a9a2f9f3e788f6378`,
DEV-01B `c07ed9a17c703df17a44dfac075603fdbe108907`; B basiert auf A.
Die darüberliegenden Governance-/MAINT-Änderungen sind keine Abhängigkeiten.
Nur die jeweiligen Feature-Diffs werden nach `git apply --check` übernommen,
keine uncommitteten fremden Dateien, keine fremden Branches/Worktrees geändert.

## Dateiplan

R1: bestehende `src/content_store/search_http.py`, `search_models.py` aus DEV,
`src/job_control/http.py`, `scripts/job_control.py`, HTTPtests und APIvertrag.
R2: DEV `src/job_control/index_{models,jobs,http}.py`, bestehende catalog,
controller, registry, models, executor, adapter_worker und content_index;
Tests/vertragliche Schemas. Zusätzlicher lokaler HTTP-E2E-Nachweis.
R3: kleines auf vorhandenen Contract-/Locator-/Reviewtypen aufbauendes
Kandidatenvorbereitungsmodell, Provenienzvalidator/Export, synthetische Tests.
Keine breitflächige Refaktorierung; keine produktive Aktion. C26: HOLD.

Nachträglicher read-only Metadatenabgleich: DEV-01A ist tatsächlich PR #124,
merged als `79d800caf3270de07296b49dc4585c1e01ceb085`; DEV-01B ist PR #125,
merged als `b2c9e3ac41441721940269e86ffe3896b289540b`. Beide fehlen in dieser
älteren Basis; die übernommenen Featurecommits bleiben deren tatsächliche
Implementierungsherkunft. UI PR #7 wurde ebenfalls direkt verifiziert:
merged `90816a1578bcf67739ee9acaa483c1635aa0c44b`. Kein UI-Worktree gelesen/geändert.
