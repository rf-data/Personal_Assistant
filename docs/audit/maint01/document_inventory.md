# B. MAINT-01 – Document Inventory

19.10.2026. [Branchinventar](branch_inventory.md), [Cleanup Proposal](cleanup_proposal.md),
[vollständige Versionstabelle](document_versions.tsv),
[Metadaten ungeklärter Fälle](../../_unresolved_imports/maint01/cases.tsv),
[genauer Importbeleg](import_manifest.md).

## Umfang und Vergleichsmaßstab

Explizite Arbeitsroots: die beiden bestätigten Primärcheckouts und ihre registrierten
Worktrees aus dem [Branchinventar](branch_inventory.md). Zusätzlich alle lokalen und
live GitHub-Branchheads derselben zwei Git-Objektbestände. Kein Home-Scan, kein
pauschaler Scan privater Arbeits-/Daten-/Testroots. Das nicht vorhandene lokale
`Personal_Assistant` ist keine zusätzliche Quelle.

Versionierte Markdown/RST/ADoc-Dokumente sowie Text-/JSON-/YAML-Dokumentation unter
`docs/`, Issue-Templates und dokumentierte Deploymentkonfigurationen wurden geprüft.
Konfiguration ist als solche gekennzeichnet, nicht automatisch ein Runbook.
Ausgeschlossen: `.git`, Venvs/Caches, `data`, `raw`, `inputs`, `outputs`, `private`,
`secrets`, `logs`, `models`, `docs/course_sources`, Testinputs und Env-/Credential-/
Token-Dateifamilien. Keine Rohmaterialien, Kursbundles oder Datenbanken gelesen/kopiert.
Untracked oder modifizierte Dokumente bleiben **nur Metadaten**, auch bei plausiblen
Titeln; Nutzeränderungen oder ein neuer Mtime erteilen keine Übernahmefreigabe.

Verglichen wird gegen die **live Default-Trees** `4c057ae` / `90816a1`, nicht die
älteren primären Arbeitsverzeichnisse. Eine Dokumentversion ist das Tupel
Repository, relativer Pfad, SHA256. Herkunftscommit, Branch/Scope, Worktreeroot,
Gitblob, Größe, Typ und optionaler Titel sind in der Versionstabelle gebunden.
Zeilen mit unbekanntem SHA wurden ausdrücklich nicht gelesen. SHA ist Integrität,
kein menschliches Fachurteil, Rechtebeweis oder Aktualitätsnachweis.

## Zählwerte ohne doppelte Erfolgszählung

| Messgröße | Anzahl | Bedeutung |
| --- | --- | --- |
| Versionstupel | 452 | 452 unterschiedliche Repository/Pfad/SHA256-Kombinationen, nicht 452 neue fehlende Dateien |
| Byteidentisch, gleicher Defaultpfad | 279 | Kein Import nötig |
| Byteidentisch, anderer Defaultpfad | 14 | Bereits anderweitig erhalten; kein zweiter Import |
| Andere Bytes am gleichen Pfad | 136 | Historische/aktive Varianten; kein automatisches Überschreiben |
| Pfad fehlt im Default | 23 | Enthält offene Draft-/PM-Pakete und historische Umzüge; kein pauschaler Import |
| Branch-Dokumentvorkommen | 12209 | Mehrfachreferenzen derselben Versionen über lokale/live Heads |
| Gelesene Worktree-Dokumentvorkommen | 5355 | Mehrfachkopien in getrennten gültigen Worktrees |
| Davon default-byteidentische Worktreevorkommen | 5149 | Kein zusätzlicher Qualitäts- oder Vollständigkeitsnachweis |
| Nur Metadaten erfasste untracked Dokumente | 4 | Kein Inhalt/Hash und keine Kopie |
| Ausgeschlossene Env-Familien-Metadateneinträge | 9 | Kein Env-Inhalt gelesen; Beispiele und echte Dateien getrennt prüfen |
| Sicher kopiert | 1 | Unveränderter historischer #88-ADR |
| Originalkopien in _unresolved_imports | 0 | Ausschließlich Metadatentabelle und Erklärung |


Die 293 byteidentischen Versionstupel sind 279 + 14. 5.149 physische
Worktreevorkommen ist eine andere Zählachse und wird nicht dazu addiert.
Leere/ungültige Worktrees und ausgeschlossene Daten gelten nicht als geprüfte
Dokumente. Die Inventur ist keine fachliche Neuabnahme alter Berichte.

## Fehlende Pfade und konkrete Zuordnung

| ID / Quelle | SHA256 / Bytes | Möglicher vorhandener Gegenpart | Ziel / Entscheidung |
| --- | --- | --- | --- |
| D0016 / `deployment/qdrant/compose.v1.yaml` | `324d7c5aeb4fcbf793ffc292218adf56d35d09a0206f49005eaaad7fa447200f` / 2274 | kein belegter byteidentischer Gegenpart | retain_open_PR72_bundle_no_selective_import |
| D0017 / `deployment/qdrant/qdrant.v1.yaml` | `4c4355676d93a04b74806723406caa0302439941ea1439e9092571385adaebf1` / 599 | kein belegter byteidentischer Gegenpart | retain_open_PR72_bundle_no_selective_import |
| D0036 / `docs/ROADMAP_update_20261015.md` | `a3e5362081d671bfe4b20b43d8e0a9f10cc7be377c2975c57e7258afe653da2d` / 13204 | kein belegter byteidentischer Gegenpart | review_missing_document_no_automatic_import |
| D0068 / `docs/architecture/human_review_workflow_adr.md` | `3ef6f647fc5730ed9e357e565a9f9aa33f5e9148c0d90b4d7943f0aca5c6b6c2` / 17436 | kein belegter byteidentischer Gegenpart | copy_unmodified_historical_ADR_from_PR88 |
| D0221 / `docs/cs50/final_integration_inventory.md` | `1f60868ea8b9a08e5ae9ed88847434075f5bbbd9b1282541dc2fc5e588220313` / 29848 | docs/cs50/archive/2026-10/final_integration_inventory.md | review_missing_document_no_automatic_import |
| D0258 / `docs/cs50_knowledge_checkpoint.md` | `c9ee1b9ffc3e2c0aaea5fdd6b4f979a58f44aef6d66e2d4eaf25056795f9d3da` / 9326 | docs/cs50/contracts/cs50_knowledge_checkpoint.md | review_missing_document_no_automatic_import |
| D0267 / `docs/cs50_pipeline_completion_report.md` | `94d031ac3fa982e4623657f5db969f1f82c8a27ab8ad08234570ab306e3c6808` / 9933 | docs/cs50/archive/2026-10/cs50_pipeline_completion_report.md | review_missing_document_no_automatic_import |
| D0288 / `docs/github_integration_status_2026-10-14.md` | `590bfb140fbdd151ae9073e2319b73bee0b94e3fca84bd4a010f904412d1ed55` / 21595 | docs/cs50/archive/2026-10/github_integration_status_2026-10-14.md | review_missing_document_no_automatic_import |
| D0357 / `docs/planning/pm01_validation.md` | `deb74f0bc6521e2880ef4ad71143a085f25aa6f24ec029be8bf4ec2a77456e38` / 5897 | kein belegter byteidentischer Gegenpart | retain_active_PM01_PR92_no_import |
| D0366 / `docs/qdrant/c21q_architecture.md` | `0091ec59bcc55a63480b664b9e4054cc48bbcd5ebfe49f0d50c8de2e978b90b9` / 5037 | kein belegter byteidentischer Gegenpart | retain_open_PR72_bundle_no_selective_import |
| D0367 / `docs/qdrant/c21q_deployment.md` | `e2efa7c8bb042d361020c1a1cf8a009ae52da7ee40cae95a2c7d3d28dda42e20` / 12540 | kein belegter byteidentischer Gegenpart | retain_open_PR72_bundle_no_selective_import |
| D0368 / `docs/qdrant/c21q_ingestion.md` | `e23c835442619e61b71e087b3c23e08ab2ce2656b79ae122bc56e7729b9c0dfc` / 9405 | kein belegter byteidentischer Gegenpart | retain_open_PR72_bundle_no_selective_import |
| D0369 / `docs/qdrant/c21q_operations.md` | `7dbacc7bb429e0dd72f532df2806b7af8a106d19a0fc9415f00b30c3c008c25a` / 14086 | kein belegter byteidentischer Gegenpart | retain_open_PR72_bundle_no_selective_import |
| D0370 / `docs/qdrant/c21q_security.md` | `f5a48e0b0ad74c857454579bb32644857adea048d22553abfe795eab3215a58f` / 4209 | kein belegter byteidentischer Gegenpart | retain_open_PR72_bundle_no_selective_import |
| D0371 / `docs/qdrant/c21q_validation.md` | `c2dd11c5ce8e8caad190d6d3a4d4c8b8f71798edeb4bc58adb7011ffdaf5fdfc` / 13228 | kein belegter byteidentischer Gegenpart | retain_open_PR72_bundle_no_selective_import |
| D0372 / `docs/qdrant/config.example.v1.json` | `db78a72acd7a39db7f29bde7079f5619351b85713d5f6576bc4e8d9fa9059b8b` / 784 | kein belegter byteidentischer Gegenpart | retain_open_PR72_bundle_no_selective_import |
| D0373 / `docs/qdrant/indexing.v1.json` | `535ef239dcdfb52b255e9bc7f1f8925d1e969387f68a0c334456a0b2338ffd40` / 897 | kein belegter byteidentischer Gegenpart | retain_open_PR72_bundle_no_selective_import |
| D0374 / `docs/qdrant/manual-review.v1.json` | `dd7e5a856f67cf9da04db58d185915061acea22583353654b0bba38984658a91` / 5000 | kein belegter byteidentischer Gegenpart | retain_open_PR72_bundle_no_selective_import |
| D0375 / `docs/qdrant/real-source-approval-review.v1.json` | `818d49b47e0eaaabc267e46ec3ec1f0cca851a674382ea1b6aa0401daded19e2` / 34395 | kein belegter byteidentischer Gegenpart | retain_open_PR72_bundle_no_selective_import |
| D0376 / `docs/qdrant/resources.v1.json` | `7c6af83b9e40d5d0324cafff3e61354fc81a3ff4145db46e02d1d480bd178435` / 1351 | kein belegter byteidentischer Gegenpart | retain_open_PR72_bundle_no_selective_import |
| D0377 / `docs/qdrant/retrieval.v1.json` | `4269fdee9cdbb80393e5bb96af84718b021bd4c603799dbeb0acd9d7db39f9a5` / 765 | kein belegter byteidentischer Gegenpart | retain_open_PR72_bundle_no_selective_import |
| D0378 / `docs/qdrant/validation.v1.json` | `804894c68ba1b5f0a7ab846c662281e545b82da89c796321af9456b3a48e1caf` / 12256 | kein belegter byteidentischer Gegenpart | retain_open_PR72_bundle_no_selective_import |
| D0404 / `src/core/logger_notes.md` | `e321d850d094f855667663fdcea2aee618e7e70d945dd28c20ea820f1e9a4cf1` / 20659 | docs/logger_notes.md | review_missing_document_no_automatic_import |

Ein identischer Dateiname in einem Archiv ist nur eine mögliche fachliche Beziehung,
kein Hashgleichheitsbeweis. Solche älteren Unterschiede bleiben im ursprünglichen
Gitbestand erhalten und werden nicht automatisch zusammengeführt. Vollständige
Herkunftsbranches/-commits und vorhandene byteidentische **andere Pfade** stehen
in [document_versions.tsv](document_versions.tsv), einschließlich aller 136
unterschiedlichen Versionen an bestehenden Pfaden.

## Kontrollierte Übernahme und Nichtübernahmen

Einzig übernommen: [historischer Review-ADR](../../architecture/human_review_workflow_adr.md)
aus #88, Commit `f3fae9ef6d2c919adb12b08242bf84819f2b42f2`, unveränderte Bytes am
bisher fehlenden Originalpfad. [Provenienz](import_manifest.md). Historische Aussage
„A nicht gemergt / B blockiert“ gilt nicht mehr; aktuelle Verträge sind B1/#90,
UI-B2/#7 und C2/#91. Kein veralteter Plannachtrag über den aktuellen Plan kopiert.

#89 r1/r2-Dateien sind bereits byteidentisch auf Default/#91 vorhanden; keine
Doppelübernahme. Die PM-01-Dateien bleiben vollständig im separaten #92. #72-
Dokumentation und Deploymentkonfiguration gehören zu dessen ungeprüftem Draftbundle;
keine losgelöste Runbook-/Configübernahme und keine Betriebsfreigabe durch MAINT.
Historische abweichende Berichte und Logger-/Roadmapnotizen werden nur zugeordnet,
nicht als heutiger Stand oder gesicherte Löschmasse behandelt.

## Ungeklärte und sensible Fälle

| Quelle | Relativer Pfad | Metadaten / Status | Entscheidung |
| --- | --- | --- | --- |
| $WORKSPACE/gmp_compliance | docs/nutrition.txt | 60 Bytes; untracked; SHA unbekannt | Keine Kopie; Eigentümer-/Datenschutz-/Auftragszuordnung nötig |
| $WORKSPACE/Personal_Assistant-c2406a | docs/operations/local_review_environment.md | 14094 Bytes; untracked; SHA unbekannt | Keine Kopie; Eigentümer-/Datenschutz-/Auftragszuordnung nötig |
| $WORKSPACE/Personal_Assistant-completion-audit | docs/cs50_pipeline_completion_audit.md | 25912 Bytes; untracked; SHA unbekannt | Keine Kopie; Eigentümer-/Datenschutz-/Auftragszuordnung nötig |
| $WORKSPACE/Personal_Assistant-completion-audit | docs/cs50_pipeline_completion_plan.md | 18101 Bytes; untracked; SHA unbekannt | Keine Kopie; Eigentümer-/Datenschutz-/Auftragszuordnung nötig |


Bei den Completion-Audit-Dateien ist eine öffentlich vorhandene Variante kein
Nachweis, dass die **untracked** lokalen Inhalte identisch sind. C24-06-A-Dokumente
werden nicht vorweg übernommen; `nutrition.txt` bleibt privat/ungeklärt.

| Repo | Env-Dateiname | Modus | Git tracked / ignored | Inhalt geprüft? |
| --- | --- | --- | --- | --- |
| gmp_compliance | .env.agentic | 0o644 | False / True | nein |
| gmp_compliance | .env.agentic.example | 0o644 | True / False | nein |
| gmp_compliance | .env.folder | 0o644 | False / True | nein |
| gmp_compliance | .env.folder.example | 0o644 | False / True | nein |
| gmp_compliance | .env.mlops | 0o644 | False / True | nein |
| gmp_compliance | .env.mlops.example | 0o644 | True / False | nein |
| gmp_compliance | .env.organizer | 0o644 | False / True | nein |
| gmp_compliance | .env.organizer.example | 0o644 | True / False | nein |
| personal-assistant-ui | .env | 0o644 | True / False | nein |


UI-`.env` ist im alten Primärcheckout versioniert und nicht ignoriert. Ohne Inhalt
kann sie eine harmlose Konfiguration oder etwas anderes sein; **kein Secretfund
behauptet**. Die echten lokalen Backend-Envdateien sind ignoriert, aber Metadaten
melden `0644`. Empfehlung: Betreiber prüft konkrete Inhalte und nötige Rechte
separat; keine Datei entfernt/umgeschrieben oder Credentialrotation ausgeführt.
Vorhandene `.env.*.example` sind bewusst getrennte Vorlagennamen; auch diese
wurden nicht inhaltlich gelesen oder kopiert.

[Unresolved-Bereich](../../_unresolved_imports/maint01/README.md) enthält zu allen
bewusst zurückgestellten fehlenden Fassungen sowie untracked/Envfällen nur
Metadaten mit Grund, Varianten und nächstem manuellen Entscheid.
