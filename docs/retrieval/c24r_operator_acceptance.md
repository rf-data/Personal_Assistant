# C24-R Operator Acceptance – 2026-10-26

Status vor menschlicher Abschlussprüfung: HOLD. PASS bedeutet tatsächlich
bestandenen Nachweis im genannten Umfang. HOLD bedeutet fehlenden Nachweis,
ungeklärte Zielintegration oder nötige Betreiberentscheidung. NOT APPLICABLE
wird nur mit begründetem Ausschluss verwendet. Keine automatische Freigabe.

| Prüfschritt | Status | Nachweis |
|---|---|---|
| Worktree vollständig | PASS | Ausgangsinventar erhalten; 56 Lieferdateien, SHA-256 und geprüfter Vollpatch |
| Tests ohne Socket | PASS | C2: 667 passed, 17 optionale Skips, 1 bewusste Abwahl; zusätzlich 72 ausführbare C1-Fälle |
| Echte HTTP-Tests | HOLD | 45 Socketfälle hier EPERM; kein Post-Fix-Nachweis außerhalb Sandbox |
| ContentStore-Lock-Fix | HOLD | deterministische Lock-/Cleanup-Probe PASS, Fixture-Event geprüft; tatsächlicher Loopback nach Fix fehlt |
| Indexjob-Regressionsschutz | PASS | 19 Indexjobtests und Handler-/Cancelproben bestanden |
| Dependencies reproduzierbar | HOLD | schmale Extras und hashgebundener Export geprüft; frische Installation fehlt, lokales soupsieve abweichend |
| Git-Backup | HOLD | Basis-HEAD unverändert; lokales Patchpaket geprüft, kein Branchcommit/Remote-Backup nachgewiesen |
| Integration gegen master geprüft | PASS | Remote-SHA/PRs und dateigenauer Vergleich; Umsetzung/Zielregression weiterhin HOLD |
| Loviscach-Pilot vorbereitet | PASS | Schema, Validator, CSV, Inventar; 0 reale Kandidaten/Gold, fachliche Abnahme HOLD |
| C26-Produktionsfreigabe | HOLD | menschliche Freigabe, echte Originale und Betriebsnachweise nicht Gegenstand dieses Abschlusses |

## 1. Nachweise sichern und Testumgebung herstellen

Das Paket `/tmp/c24r-final-validation-20261026/` und das danebenliegende
`.tar.gz` samt `.sha256` vor Bereinigung von `/tmp` dauerhaft sichern.
Im Repository mit exakt passendem Lieferstand:

```bash
cd "$HOME/0_Portfolio_Projekte/Personal_Assistant-c24r"
sha256sum -c /tmp/c24r-final-validation-20261026/artifacts.sha256
sha256sum -c /tmp/c24r-final-validation-20261026/files.sha256
```

Artefaktmanifest-Pfade sind absolut für diesen Paketort; `files.sha256` ist
repositoryrelativ. Bei verlagertem Paket die Artefaktmanifest-Prefixe auflösen,
keine unverifizierten Dateien anwenden. Das Archiv hat zusätzlich einen äußeren
SHA-256-Nachweis. Dependencyprofil wie in
[c24r_dependency_review.md](c24r_dependency_review.md) in frischer Venv installieren.
Anschließend beide vollständigen Befehle aus
[c24r_final_validation.md](c24r_final_validation.md) ausführen und Rohlogs sichern.

## 2. Echte HTTP-Abnahme nach Fixture-Fix

Außerhalb der socketgesperrten Umgebung, auf genau den manifestierten Dateien:

```bash
export PYTHONDONTWRITEBYTECODE=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1
export UV_CACHE_DIR=$(mktemp -d /tmp/c24r-http-cache.XXXXXX)
uv run --offline --no-sync python -m pytest -q -o addopts= -p no:cacheprovider \
  tests/test_c24r_integration.py::test_actual_loopback_job_to_search \
  tests/test_content_search_http.py::test_real_local_http_server_and_process_restart \
  tests/test_content_http.py
```

Erwartung: **45 passed**, 0 failed/error. Danach C1 vollständig: **117 passed**.
Diese Zahlen sind Sollwerte, keine hier erzielten Ergebnisse. Bei abweichendem
Ergebnis HOLD belassen; Logs und Umgebung festhalten. Kein Sleep, LOCK_NB- oder
ACL-/Quarantänewechsel zur Beruhigung eines Fehlers. Die übrigen Freigabepunkte
werden durch einen HTTP-Erfolg nicht automatisch freigegeben.

## 3. Zwei lokale Commits und Branchbackup

Nur im C24-R-Worktree mit normaler Betreiber-Schreibberechtigung. Die folgenden
Befehle sind vorbereitet, hier wegen der Filesystemgrenze nicht ausgeführt.
Kein automatisches Commit-Hook-Bypass und kein Force-Push.

```bash
cd "$HOME/0_Portfolio_Projekte/Personal_Assistant-c24r"
test "$(git branch --show-current)" = feat/c24r-retrieval_completion
test "$(git rev-parse HEAD)" = 4c057ae33d41ba98e227879cc8a51283338e4a0b
git diff --cached --quiet
sha256sum -c /tmp/c24r-final-validation-20261026/files.sha256
while IFS= read -r c24r_path; do
  git add -f -- "$c24r_path"
done < /tmp/c24r-final-validation-20261026/commit1-files.txt
git diff --cached --stat
git diff --cached --check
git diff --cached
# Nach Sichtung ausschließlich dieser 54 Completiondateien:
git commit -m "feat(c24r): complete retrieval integration and acceptance evidence"
git add -- pyproject.toml uv.lock
git diff --cached --stat
git diff --cached --check
git diff --cached
# Nach Sichtung ausschließlich dieser zwei Dependencydateien:
git commit -m "build(c24r): expose minimal PDF and HTML extras"
git status --short --branch
git log -2 --format='%H %s'
git push --set-upstream origin HEAD:refs/heads/feat/c24r-retrieval_completion
git ls-remote origin refs/heads/feat/c24r-retrieval_completion
git rev-parse HEAD
```

Bei einem fehlgeschlagenen Guard/Hook stoppen und Ursache prüfen; ein Shellblock
ist kein automatisches Abbruchprogramm. `operator_commit.sh` im Paket enthält
zusätzliche Guards und prüft die exakte Stagingdateiliste vor jedem Commit.
Nach dem Push müssen Remote-SHA und lokaler HEAD übereinstimmen. Bei
Non-fast-forward, fremden Stagingdateien oder verändertem Lieferhash HOLD;
kein Force-Push und keine Rücksetzung. Ein Backup ist keine Produktionsfreigabe.

Der Lieferpatch wird im bereits veränderten C24-R-Worktree **nicht** angewendet.
Nur bei Verlust des Worktrees: neuen Checkout der exakten Basis anlegen,
`git apply --check` und anschließend beide Teilpatches in Reihenfolge anwenden.
Vollpatch und Teilpatches sind Alternativen; niemals beide anwenden.

## 4. Integration separat vorlegen

Mit normalem Gitnetz zunächst `git fetch origin` und den neuen master-SHA
aufzeichnen. Kein Checkout oder Merge von master in diesem alten Worktree.
Im neu anzulegenden Integrationsbranch ausschließlich die neuen Komponenten aus
[c24r_master_integration_matrix.md](c24r_master_integration_matrix.md) übernehmen.
Keine Übernahme ganzer alter C16-/Search-/Index-/Dependencydateien.
Die aktuelle master-Testgruppe `test-offline` zuerst verwenden; Schmalprofil-
Entscheidungen und Kandidatenschema an Zielmodelle anpassen. Import-/Index-/ACL-/
Loviscach-/PDF- und echte HTTP-Regressionsprüfung auf dem Zielstand nachweisen.

## 5. Menschliche Entscheidungen

Betreiber hält getrennt fest: HTTP-Post-Fix-Log, frisches Profil, zwei echte
Commit-SHAs/Remote-SHA, freigegebener selektiver Integrationsdiff und Zieltests.
Loviscach benötigt separate Originalbelege, Rechte, Kurs-/ACLbindung und
unabhängiges menschliches Goldreview. Keine echten Downloads ohne Freigabe.
C26 bleibt bis zur gesonderten Produktionsentscheidung HOLD.
MAINT-05-Archivierungsprozesse werden durch dieses Paket nicht verändert.
