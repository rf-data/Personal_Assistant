# Lokale Worktree-Bilanz vor der Bereinigung

Prüfbasis origin/master 8ba519e. Clean bezieht sich auf versionierte/untracked Dateien; ignorierte Dateien sind separat geprüft. Erhalt hat Vorrang. Gemeinsamer Git-Ordner aller vorhandenen Worktrees bestätigt. <workspace> bezeichnet das lokale Elternverzeichnis von gmp_compliance.

| Pfad | Branch | Zustand | In master? | Lokale Dateien / Commits außerhalb master | Empfehlung vor Entfernung |
|---|---|---|---|---|---|
| `<workspace>/gmp_compliance` | `master` | dirty | ja | 0 Commits; 3 untracked; 181 ignored (docs/cs50_pipeline_completion_audit.md, docs/cs50_pipeline_completion_plan.md, src/prio_list.md); .venv erhalten | Hauptarbeitskopie erhalten; .env/data/Cache/persönliche Dateien |
| `<workspace>/Personal_Assistant-archive` | `docs/cs50-archive` | clean | ja | 0 Commits; 0 untracked; 12 ignored | erhalten: Umgebungen/Caches separat prüfen |
| `<workspace>/Personal_Assistant-audit` | `detached` | clean | nein | 1 Commits; 0 untracked; 25 ignored; .venv erhalten | erhalten: außerhalb master liegende Commits; Umgebungen/Caches separat prüfen |
| `<workspace>/Personal_Assistant-audit-check` | `detached` | clean | nein | 1 Commits; 0 untracked; 17 ignored | erhalten: außerhalb master liegende Commits; Umgebungen/Caches separat prüfen |
| `<workspace>/Personal_Assistant-checkpoints` | `feat/cs50-knowledge-checkpoints` | clean | nein | 1 Commits; 0 untracked; 25 ignored | erhalten: außerhalb master liegende Commits; Umgebungen/Caches separat prüfen |
| `<workspace>/Personal_Assistant-completion` | `review/cs50-complete` | clean | ja | 0 Commits; 0 untracked; 26 ignored; .venv erhalten | erhalten: Umgebungen/Caches separat prüfen |
| `<workspace>/Personal_Assistant-completion-audit` | `docs/cs50-completion-audit` | dirty | ja | 0 Commits; 2 untracked; 20 ignored (docs/cs50_pipeline_completion_audit.md, docs/cs50_pipeline_completion_plan.md) | erhalten: unversionierte Dateien; Umgebungen/Caches separat prüfen |
| `<workspace>/Personal_Assistant-docs` | `docs/cs50-documentation` | dirty | ja | 0 Commits; 7 untracked; 12 ignored (docs/cs50/README.md, docs/cs50/archive/2026-10/README.md, docs/cs50/archive/2026-10/cs50_pipeline_completion_audit.md) | erhalten: unversionierte Dateien; Umgebungen/Caches separat prüfen |
| `<workspace>/Personal_Assistant-final-audit` | `docs/cs50-final-archive` | clean | nein | 1 Commits; 0 untracked; 20 ignored | erhalten: außerhalb master liegende Commits; Umgebungen/Caches separat prüfen |
| `<workspace>/Personal_Assistant-lazy-sdk` | `fix/optional-knowledge-sdk-imports` | clean | nein | 1 Commits; 0 untracked; 24 ignored | erhalten: außerhalb master liegende Commits; Umgebungen/Caches separat prüfen |
| `<workspace>/Personal_Assistant-pilot-regression` | `test/portable-cs50-pilot-regression` | clean | ja | 0 Commits; 0 untracked; 23 ignored | erhalten: Umgebungen/Caches separat prüfen |
| `<workspace>/Personal_Assistant-pilot-tests` | `test/portable-cs50-pilot` | clean | ja | 0 Commits; 0 untracked; 0 ignored | nach grünem Integrationsvergleich entfernen; keine ignored/untracked Dateien |
| `<workspace>/Personal_Assistant-provenance-models` | `fix/knowledge-transcript-metadata-contract` | clean | nein | 1 Commits; 0 untracked; 24 ignored | erhalten: außerhalb master liegende Commits; Umgebungen/Caches separat prüfen |
| `<workspace>/Personal_Assistant-quality-fix` | `fix/cs50-quality-synthetic-boundaries` | clean | nein | 1 Commits; 0 untracked; 23 ignored | erhalten: außerhalb master liegende Commits; Umgebungen/Caches separat prüfen |
| `/tmp/Personal_Assistant-lazy-baseline` | `detached` | nicht vorhanden / prunable | ja | 0 Commits; 0 untracked; 0 ignored | dauerhafte Refs sichern; ausschließlich veraltete Registrierung entfernen, falls git worktree remove ohne force gelingt |
| `/tmp/cs50-discovery-pr` | `feat/cs50-discovery-contracts` | nicht vorhanden / prunable | nein | 1 Commits; 0 untracked; 0 ignored | dauerhafte Refs sichern; ausschließlich veraltete Registrierung entfernen, falls git worktree remove ohne force gelingt |
| `/tmp/cs50-extraction-pr` | `feat/cs50-offline-extraction` | nicht vorhanden / prunable | nein | 2 Commits; 0 untracked; 0 ignored | dauerhafte Refs sichern; ausschließlich veraltete Registrierung entfernen, falls git worktree remove ohne force gelingt |
| `/tmp/cs50-full-coverage-pr2` | `feat/cs50-full-coverage` | nicht vorhanden / prunable | nein | 4 Commits; 0 untracked; 0 ignored | dauerhafte Refs sichern; ausschließlich veraltete Registrierung entfernen, falls git worktree remove ohne force gelingt |
| `/tmp/cs50-integration-audit-20261014/feature` | `detached` | nicht vorhanden / prunable | nein | 9 Commits; 0 untracked; 0 ignored | dauerhafte Refs sichern; ausschließlich veraltete Registrierung entfernen, falls git worktree remove ohne force gelingt |
| `/tmp/cs50-integration-audit-20261014/master-clean` | `detached` | nicht vorhanden / prunable | ja | 0 Commits; 0 untracked; 0 ignored | dauerhafte Refs sichern; ausschließlich veraltete Registrierung entfernen, falls git worktree remove ohne force gelingt |
| `/tmp/cs50-lecture-adapter-pr3` | `detached` | nicht vorhanden / prunable | nein | 5 Commits; 0 untracked; 0 ignored | dauerhafte Refs sichern; ausschließlich veraltete Registrierung entfernen, falls git worktree remove ohne force gelingt |
| `/tmp/cs50-selection-pr` | `feat/cs50-selection-preview` | nicht vorhanden / prunable | nein | 3 Commits; 0 untracked; 0 ignored | dauerhafte Refs sichern; ausschließlich veraltete Registrierung entfernen, falls git worktree remove ohne force gelingt |
| `/tmp/cs50-timed-knowledge-pr2` | `feat/cs50-timed-knowledge` | nicht vorhanden / prunable | nein | 4 Commits; 0 untracked; 0 ignored | dauerhafte Refs sichern; ausschließlich veraltete Registrierung entfernen, falls git worktree remove ohne force gelingt |
| `/tmp/knowledge-provenance-pr` | `feat/knowledge-transcript-provenance` | nicht vorhanden / prunable | nein | 2 Commits; 0 untracked; 0 ignored | dauerhafte Refs sichern; ausschließlich veraltete Registrierung entfernen, falls git worktree remove ohne force gelingt |
| `/tmp/knowledge-source-id-pr` | `fix/knowledge-source-id` | nicht vorhanden / prunable | nein | 1 Commits; 0 untracked; 0 ignored | dauerhafte Refs sichern; ausschließlich veraltete Registrierung entfernen, falls git worktree remove ohne force gelingt |
| `/tmp/lazy-marvin-pr` | `fix/lazy-marvin-import` | nicht vorhanden / prunable | nein | 3 Commits; 0 untracked; 0 ignored | dauerhafte Refs sichern; ausschließlich veraltete Registrierung entfernen, falls git worktree remove ohne force gelingt |
| `/tmp/math-import-pr` | `fix/math-normalization-import` | nicht vorhanden / prunable | nein | 1 Commits; 0 untracked; 0 ignored | dauerhafte Refs sichern; ausschließlich veraltete Registrierung entfernen, falls git worktree remove ohne force gelingt |
| `/tmp/official-transcript-pr` | `feat/official-transcript-import` | nicht vorhanden / prunable | nein | 1 Commits; 0 untracked; 0 ignored | dauerhafte Refs sichern; ausschließlich veraltete Registrierung entfernen, falls git worktree remove ohne force gelingt |

## Dry-Run-Kandidaten zur manuellen Prüfung

- Ignorierte pytest-/Ruff-/Python-Caches zusätzlicher Worktrees nach genauer Herkunftsprüfung. Keine pauschale Cachelöschung.
- Vollständig integrierter Personal_Assistant-completion: wegen workers/cs50/.venv und ignorierter Dateien vorerst erhalten.
- Personal_Assistant-pilot-regression: ancestry-integriert, aber ignorierte Caches; vorerst erhalten.
- Personal_Assistant-completion-audit: zwei unversionierte Berichte; Originale bleiben trotz Archivübernahme erhalten.
- Nicht integrierte Original-Commit-IDs in Checkpoint-/Lazy-/Provenienz-/Quality-Worktrees bleiben über Branches gesichert; keine Branchlöschung anhand bloßer inhaltlicher Ähnlichkeit.
- Hauptarbeitskopie: .env, data, Logs, Datenbanken, Cookies, persönliche Dateien und unbekannte Caches ausdrücklich ausgeschlossen. Keine Pfad- oder Dateinamenssuche als Löschfreigabe.

## Gesicherte detached Commits

| Ursprünglicher Worktree | Commit | Dauerhafte lokale Ref |
|---|---|---|
| `<workspace>/Personal_Assistant-audit` | `cdf3f711607b8c99783973a3a88ad6925a5d0079` | `refs/heads/archive/cs50-2026-10/cdf3f711607b` |
| `<workspace>/Personal_Assistant-audit-check` | `20574a01a7cada00c69200354a95df9107de57e2` | `refs/heads/archive/cs50-2026-10/20574a01a7ca` |
| `/tmp/cs50-integration-audit-20261014/feature` | `c74c8b72fc83aa07147c7f6d9113dc708122dc2f` | `refs/heads/archive/cs50-2026-10/c74c8b72fc83` |
| `/tmp/cs50-lecture-adapter-pr3` | `9dbf903416477d193b830d36836991f8501194a3` | `refs/heads/archive/cs50-2026-10/9dbf90341647` |

Alle vier Ref-Ziele nach Erstellung mit git rev-parse erneut verifiziert. Nicht integrierte Branch-Worktree-Commits bleiben zusätzlich unter ihren vorhandenen lokalen Branch-Refs erhalten; diese Branches werden nicht gelöscht.

## Tatsächlich ausgeführte Entfernung

| Pfad | Art | Ergebnis |
|---|---|---|
| `/tmp/Personal_Assistant-lazy-baseline` | obsolete registration | erfolgreich, verifiziert |
| `/tmp/cs50-discovery-pr` | obsolete registration | erfolgreich, verifiziert |
| `/tmp/cs50-extraction-pr` | obsolete registration | erfolgreich, verifiziert |
| `/tmp/cs50-full-coverage-pr2` | obsolete registration | erfolgreich, verifiziert |
| `/tmp/cs50-integration-audit-20261014/feature` | obsolete registration | erfolgreich, verifiziert |
| `/tmp/cs50-integration-audit-20261014/master-clean` | obsolete registration | erfolgreich, verifiziert |
| `/tmp/cs50-lecture-adapter-pr3` | obsolete registration | erfolgreich, verifiziert |
| `/tmp/cs50-selection-pr` | obsolete registration | erfolgreich, verifiziert |
| `/tmp/cs50-timed-knowledge-pr2` | obsolete registration | erfolgreich, verifiziert |
| `/tmp/knowledge-provenance-pr` | obsolete registration | erfolgreich, verifiziert |
| `/tmp/knowledge-source-id-pr` | obsolete registration | erfolgreich, verifiziert |
| `/tmp/lazy-marvin-pr` | obsolete registration | erfolgreich, verifiziert |
| `/tmp/math-import-pr` | obsolete registration | erfolgreich, verifiziert |
| `/tmp/official-transcript-pr` | obsolete registration | erfolgreich, verifiziert |
| `<workspace>/Personal_Assistant-pilot-tests` | physical worktree | erfolgreich, verifiziert |

Ein physischer Worktree / 14 veraltete Registrierungen entfernt. Integrierter Branch test/portable-cs50-pilot mit git branch -d gelöscht. Kein anderer Branch gelöscht; keine force-/prune-/reset-Operation.

## Erhaltene Worktrees nach Bereinigung

- `<workspace>/gmp_compliance`: Hauptarbeitskopie: geschützte Berichte, prio_list.md und lokale .env/data/persönliche Dateien.
- `<workspace>/Personal_Assistant-archive`: frischer Testworktree: Prüfkontext und Testcaches erhalten.
- `<workspace>/Personal_Assistant-audit`: nicht integrierte lokale Commit-IDs und/oder ignorierte Caches/Umgebungen; Erhaltung vor Speichergewinn.
- `<workspace>/Personal_Assistant-audit-check`: nicht integrierte lokale Commit-IDs und/oder ignorierte Caches/Umgebungen; Erhaltung vor Speichergewinn.
- `<workspace>/Personal_Assistant-checkpoints`: nicht integrierte lokale Commit-IDs und/oder ignorierte Caches/Umgebungen; Erhaltung vor Speichergewinn.
- `<workspace>/Personal_Assistant-completion`: Completion-Stand integriert; ignorierte Worker-.venv/Caches separat prüfen.
- `<workspace>/Personal_Assistant-completion-audit`: unversionierte Abschlussberichte erhalten.
- `<workspace>/Personal_Assistant-docs`: aktiver Dokumentations-PR-Worktree.
- `<workspace>/Personal_Assistant-final-audit`: nicht integrierte lokale Commit-IDs und/oder ignorierte Caches/Umgebungen; Erhaltung vor Speichergewinn.
- `<workspace>/Personal_Assistant-lazy-sdk`: nicht integrierte lokale Commit-IDs und/oder ignorierte Caches/Umgebungen; Erhaltung vor Speichergewinn.
- `<workspace>/Personal_Assistant-pilot-regression`: nicht integrierte lokale Commit-IDs und/oder ignorierte Caches/Umgebungen; Erhaltung vor Speichergewinn.
- `<workspace>/Personal_Assistant-provenance-models`: nicht integrierte lokale Commit-IDs und/oder ignorierte Caches/Umgebungen; Erhaltung vor Speichergewinn.
- `<workspace>/Personal_Assistant-quality-fix`: nicht integrierte lokale Commit-IDs und/oder ignorierte Caches/Umgebungen; Erhaltung vor Speichergewinn.
