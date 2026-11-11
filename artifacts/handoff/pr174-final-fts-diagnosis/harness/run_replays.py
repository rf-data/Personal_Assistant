"""Sequential fixed plan. No repetition of failed requests, no resume or repair."""
import json
import os
from pathlib import Path
import subprocess
import time

artifact = Path(__file__).resolve().parents[1]
session = json.loads((artifact / 'evidence/session.json').read_text())
target = Path(session['target'])
assert json.loads((artifact / 'evidence/target-case-exit.json').read_text())['exit'] == 0
assert len(json.loads((artifact / 'evidence/target-case-searches.json').read_text())) == 5
env = os.environ.copy()
env.update(PYTHONDONTWRITEBYTECODE='1', PYTEST_DISABLE_PLUGIN_AUTOLOAD='1',
           PYTHONPATH=str(artifact / 'harness') + os.pathsep + str(target),
           GIT_OPTIONAL_LOCKS='0', FTS_DIAG_TARGET=str(target))
commands = []
for mode in ('normal', 'single', 'contention', 'recovery'):
    output = artifact / f'evidence/{mode}-searches.json'
    assert not output.exists()
    env['FTS_PROBE_OUTPUT'] = str(output)
    command = [str(target / '.venv/bin/python'), '-B', str(artifact / 'harness/replay_target.py'), mode]
    started = time.monotonic()
    with (artifact / f'evidence/{mode}.log').open('w') as log:
        process = subprocess.run(command, cwd=target, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=65)
    commands.append(dict(mode=mode, cwd=str(target), argv=command, exit=process.returncode,
                         runner_wall_seconds=time.monotonic() - started))
    (artifact / 'evidence/replay-commands.json').write_text(json.dumps(commands, indent=2) + '\n')
    print(json.dumps(commands[-1]), flush=True)
    assert process.returncode == 0, 'Replay runner failed; see preserved log'
