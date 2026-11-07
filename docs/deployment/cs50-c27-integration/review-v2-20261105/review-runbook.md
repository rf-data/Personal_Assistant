# C27 Stage-0 Review v2 – Offline-Runbook

Dieses Runbook prüft ausschließlich den neuen additiven v2-Dateivertrag. Es
autorisiert keine Integration, Indexänderung, automatische Formatierung oder
Änderung historischer Tests. Bestehende Branches und Worktrees bleiben erhalten.

## Eingaben und Bindung

REVIEW ist dieses Worktree; SOURCE ist das benachbarte
`Personal_Assistant-cs50-server-runtime`. Basis:
`a8af1d9372eb435d3e1331c33b047d21120d57c2`. AGENTS.md und
.pre-commit-config.yaml beachten. Es wird ausschließlich lokal gearbeitet.

Zuerst im Review-Paketverzeichnis ausführen:

```bash
sha256sum -c SHA256SUMS
sha256sum SHA256SUMS
```

Den zweiten Digest mit dem separat veröffentlichten Abschlussbericht vergleichen.
SHA256SUMS enthält keinen Eigenhash. Das neue Testmodul pinnt zusätzlich
`candidate-manifest-v2.json` auf
`c56a5258c9ec750fa6a56b123c0bc83ded655eef8d2b4ca4dca8f2e1697f7450`.
Manifest und Ergebnisdatei enthalten alle sechs alten und neuen Produktendhashes.
Der Produktpatch enthält keine Tests und keine Stage-1-Dateien.

## Index und Arbeitsdateien nur lesen

Vom REVIEW-Repositoryroot:

```bash
git branch --show-current
git rev-parse HEAD
git diff --cached --name-status
git diff --cached --numstat
git diff --cached --check
git diff --exit-code
/home/robfra/.cache/pre-commit/repokzno83cn/py_env-python3.12/bin/ruff --version
/home/robfra/.cache/pre-commit/repokzno83cn/py_env-python3.12/bin/ruff format --check --no-cache \
  src/model_materials/acquisition.py src/tools_materials/code_zip.py \
  src/tools_materials/source_acquisition.py src/tools_materials/storage.py \
  src/tools_materials/text_validation.py \
  docs/deployment/cs50-c27-integration/review-v2-20261105/tests/review_integrity_v2.py
```

Erwartet: Branch `review/c27-stage0-20261105`, genannter HEAD, genau sechs
Produktpfade, vier A und zwei M, 362 Einfügungen / 3 Löschungen, keine ungestagten
Änderungen an bestehenden getrackten Dateien, Ruff 0.16.0. Die neuen Review-Dateien
sind ungestagt; vorhandene Ignore-Regeln können insbesondere JSON ausblenden.
Nicht automatisch hinzufügen oder Ignore-Regeln ändern. Bei Produkt-/Indexdrift:
HOLD und Untersuchung, keine Reparatur im Rahmen dieser Prüfung.

## Frische isolierte Kandidaten herstellen

Das folgende Standardbibliotheksprogramm wird vom REVIEW-Repositoryroot gestartet.
Es schreibt ausschließlich in eine neue /tmp-Wurzel, erzeugt keine Git-Referenzen
und nutzt keinen anderen Index. `git archive` liest den gepinnten Basiscommit.
Nur für v1 wird eine bekannte EOF-Leerzeilenwarnung zugelassen; die Patchbytes
werden dabei nicht korrigiert. V2 wird strikt mit `--whitespace=error` geprüft.

```bash
/home/robfra/.cache/pre-commit/repokzno83cn/py_env-python3.12/bin/python -B - <<'PY'
import hashlib
import io
import json
import os
from pathlib import Path
import subprocess
import tarfile
import tempfile

review = Path.cwd()
source = review.parent / 'Personal_Assistant-cs50-server-runtime'
package = review / 'docs/deployment/cs50-c27-integration/review-v2-20261105'
env = {**os.environ, 'GIT_OPTIONAL_LOCKS': '0', 'PYTHONDONTWRITEBYTECODE': '1'}
def run(args, cwd=review):
    return subprocess.run(args, cwd=cwd, env=env, check=True, capture_output=True).stdout
def sha(raw):
    return hashlib.sha256(raw).hexdigest()
raw = (package / 'candidate-manifest-v2.json').read_bytes()
assert sha(raw) == 'c56a5258c9ec750fa6a56b123c0bc83ded655eef8d2b4ca4dca8f2e1697f7450'
m = json.loads(raw)
audit = Path(tempfile.mkdtemp(prefix='c27-review-v2-recheck-'))
archive = run(['git', 'archive', '--format=tar', m['base']])
for name, patch, whitespace in [
    ('stage0-v1', source / m['history']['v1_patch']['path'], 'nowarn'),
    ('stage0-v2', package / 'stage0-v2.patch', 'error'),
    ('combined-v2', package / 'stage0-v2.patch', 'error'),
]:
    expected = m['history']['v1_patch']['sha256'] if name == 'stage0-v1' else m['stage0']['sha256']
    assert sha(patch.read_bytes()) == expected
    root = audit / name
    root.mkdir()
    with tarfile.open(fileobj=io.BytesIO(archive)) as tar:
        for item in tar.getmembers():
            assert not Path(item.name).is_absolute() and '..' not in Path(item.name).parts
            assert item.isdir() or item.isfile()
        tar.extractall(root, filter='data')
    run(['git', 'apply', '--check', '--whitespace=' + whitespace, str(patch)], cwd=root)
    run(['git', 'apply', '--whitespace=' + whitespace, str(patch)], cwd=root)
for name, expected in m['stage1']['source_sha256'].items():
    path = source / name
    assert not any(p.is_symlink() for p in (path, *path.parents))
    data = path.read_bytes()
    assert sha(data) == expected, name
    target = audit / 'combined-v2' / name
    assert not target.exists(), name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
python = '/home/robfra/.cache/pre-commit/repokzno83cn/py_env-python3.12/bin/python'
run([python, '-B', str(package / 'tests/review_integrity_v2.py'),
     '--stage0-root', str(audit / 'stage0-v2'),
     '--v1-root', str(audit / 'stage0-v1'),
     '--combined-root', str(audit / 'combined-v2'),
     '--source-root', str(source), '--audit', str(audit),
     '--results', str(audit / 'test-results.json')])
print(audit)
print((audit / 'test-results.json').read_text())
PY
```

Nur die 55 Stage-1-Pfade werden in den getrennten Kombinationsbaum kopiert, nach
Prüfung ihrer historischen Quellhashes. Fehlt ein Input oder die lokale
Python-/Ruff-Umgebung, die betroffene Prüfung als NOT_RUN dokumentieren; keine
Downloads oder Paketinstallation. Tests ohne `-O` und ohne PYTHONOPTIMIZE starten.
Die neuen Testfixtures bleiben unter der ausgegebenen Auditwurzel erhalten.

## Durchgeführter Lauf und Ergebnisgrenzen

Originale Auditwurzel: `/tmp/c27-review-v2-20261105-ap_c1jer`. CPython 3.12.12,
Standardbibliothek, Ruff 0.16.0. 15 neue Tests und 86 Unterfälle bestanden.
Syntax wurde mit `compile(..., 'exec')` im Speicher geprüft, ohne Produktmodule
zu importieren und ohne Bytecodecaches zu schreiben. Keine vorhandenen Tests
wurden editiert. Die zwei reinen historischen v1-Prüffunktionen werden aus dem
hashgebundenen Original per AST extrahiert, auf einem eigenen vollständigen
v1-Vertragsfixture positiv geprüft und mit v2 erwartungsgemäß negativ geprüft.
Das ist kein Pytestlauf der alten Suite.

Vor/nach gebunden: Indexdatei, staged Diff, alle sechs Produktbytes, 190
SOURCE-Input-/Nachweisdateien, SOURCE-Index und vorhandener Six-Courses-Diff,
Shared-Refs und Worktree-Registrierungen. Die [Ergebnisdatei](integrity-results.json)
enthält die Dateiinventare und die einzelnen neuen Testergebnisse. Der früh
gestoppte Vorbereitungslauf wegen zwei fehlender optionaler historischer Harnesses
und der manuell korrigierte erste Formatcheck der neuen Testdatei sind dort
offengelegt. Diese Ereignisse verändern den vorliegenden Produktkandidaten nicht.

Alte 289/285-Fallergebnisse sind ausschließlich historische Evidenz. Kein neuer
vollständiger C27-Suite-, B1-, Host- oder Semantiklauf. B1 bleibt offen. B2 bleibt
durch eigenständige Kandidatenverträge explizit behandelt. GO_FOR_COMMIT_REVIEW
besagt hier ausschließlich, dass die neue Review-Revision intern konsistent und
prüfbar ist. Stage 0 ist nicht in master integriert; Stage 1 bleibt separat.
Keine aktuelle Live-Remote-Verifikation wurde vorgenommen.

Alle neuen Unterlagen bleiben zunächst ungestagt. Die spätere dauerhafte
Integration nach AGENTS.md ist wegen des Auftragsverbots ausstehend. Es wurden
keine temporären Git-Artefakte erzeugt oder entfernt; der vorbestehende Branch und
Worktree bleiben für Review erhalten. Auch die explizit benannten /tmp-Helfer und
Auditdaten werden für Nachprüfung behalten; kein Bestands- oder MAINT-Cleanup.
