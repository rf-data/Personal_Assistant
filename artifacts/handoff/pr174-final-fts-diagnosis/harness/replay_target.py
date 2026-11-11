"""Fixed-count independent searches of this session's fresh synthetic fixture."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import fts_probe
fts_probe.install()
from scripts import cs50_learning_mvp as mvp
from src.content_store.store import ContentStore
from src.tools_rag.content_index import ContentIndex

mode = sys.argv[1]
assert mode in {'normal', 'single', 'contention', 'recovery'}
artifact = Path(__file__).resolve().parents[1]
session = json.loads((artifact / 'evidence/session.json').read_text())
target = Path(session['target'])
assert Path.cwd() == target
root_matches = [p for p in Path(session['temporary_root']).glob('target-case-final/test_long_source_run_cache_and*/new-private-mvp')
                if not p.parent.is_symlink()]
assert len(root_matches) == 1
root = root_matches[0]
assert root.is_relative_to(session['temporary_root'])
intent = mvp.load(root, 'intent.json')
assert intent['source_origin'] == 'synthetic'
assert mvp.load(root, 'state.json')['phase'] == 'ready'
actor = mvp.actor_for(intent, 'synthetic-operator')
index = ContentIndex(ContentStore(root / 'store'), root / 'index', cursor_key_file=root / 'cursor.key')


def inventory():
    return {str(p.relative_to(root)): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in root.rglob('*') if p.is_file()}


before = inventory()
original_affinity = os.sched_getaffinity(0)
children = []
outcomes = []
metadata = dict(mode=mode, requested_samples={'normal': 3, 'single': 3, 'contention': 6, 'recovery': 2}[mode],
                contenders=3 if mode == 'contention' else 0, affinity_before=sorted(original_affinity),
                source='fresh lecture_171 fixture from original target-worktree test')
try:
    if mode in {'single', 'contention'}:
        os.sched_setaffinity(0, {min(original_affinity)})
    metadata['affinity_during'] = sorted(os.sched_getaffinity(0))
    if mode == 'contention':
        for _ in range(3):
            child = subprocess.Popen([sys.executable, '-B', str(artifact / 'harness/cpu_contender.py')],
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
            children.append(child)
            assert child.stdout.readline().strip() == 'READY'
        metadata['all_contenders_alive_at_start'] = all(c.poll() is None for c in children)
        assert metadata['all_contenders_alive_at_start']
    started = time.monotonic()
    for ordinal in range(metadata['requested_samples']):
        try:
            with index.search_lexical('variable', actor=actor, limit=5) as page:
                assert page.items
        except Exception as exc:
            outcomes.append(dict(ordinal=ordinal, outcome=type(exc).__name__))
        else:
            outcomes.append(dict(ordinal=ordinal, outcome='ok'))
    metadata['measurement_wall_seconds'] = time.monotonic() - started
    metadata['all_contenders_alive_at_end'] = all(c.poll() is None for c in children)
finally:
    for child in children:
        if child.poll() is None:
            child.terminate()
        child.wait(timeout=5)
    os.sched_setaffinity(0, original_affinity)
    metadata['children_reaped'] = all(c.poll() is not None for c in children)
    metadata['affinity_restored'] = os.sched_getaffinity(0) == original_affinity
    metadata['synthetic_root_bytes_unchanged'] = inventory() == before
    metadata['outcomes'] = outcomes
    (artifact / f'evidence/{mode}-run.json').write_text(json.dumps(metadata, indent=2) + '\n')
assert metadata['children_reaped'] and metadata['affinity_restored'] and metadata['synthetic_root_bytes_unchanged']
assert len(fts_probe.EVENTS) == metadata['requested_samples']
if mode == 'contention':
    assert metadata['all_contenders_alive_at_end']
print(json.dumps(dict(mode=mode, samples=len(outcomes), success=sum(o['outcome'] == 'ok' for o in outcomes),
                      failures=sum(o['outcome'] != 'ok' for o in outcomes), bytes_unchanged=True)))
