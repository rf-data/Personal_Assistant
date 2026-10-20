"""Synchronous real imports in the installed uv environment; no SQLite workaround."""

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.skipif(
    importlib.util.find_spec("tiktoken") is None,
    reason="Requires installed lecture-worker dependencies",
)
@pytest.mark.parametrize(
    "module",
    [
        "src.tools_knowledge.find_knowledge",
        "src.tools_knowledge.consolidate_knowledge",
        "src.run_knowledge_extraction",
        "src.utils.llm_helper",
    ],
)
def test_synchronous_real_import_and_llm_contract(tmp_path, module):
    root = Path(__file__).resolve().parents[1]
    script = r"""
import importlib
import inspect
import logging
import os
from pathlib import Path
import socket
import sys
from types import ModuleType, SimpleNamespace

root = Path(sys.argv[1]); tmp = Path(sys.argv[2]); target = sys.argv[3]
sys.path.insert(0, str(root)); os.chdir(tmp)
os.environ.update(ROOT=str(tmp), CHROMA_DIR=str(tmp/'chroma'), DATA_DIR=str(tmp/'data'),
                  WIKI_EN_API='https://example.invalid', HEADER_AGENT='offline',
                  HF_API_KEY='offline-placeholder', OPENAI_API_KEY='offline-placeholder')
# Block optional SDKs even if installed. No library substitution
# occurs during the normal import/deterministic phase.
sdks = {'openai', 'marvin', 'pydantic_ai'}
class NoOptionalSDK:
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in sdks:
            raise ModuleNotFoundError('Optional SDK deliberately unavailable', name=fullname)
blocker = NoOptionalSDK(); sys.meta_path.insert(0, blocker)
def forbidden(*a, **kw): raise AssertionError('External call forbidden')
socket.socket.connect = forbidden; socket.socket.connect_ex = forbidden
socket.getaddrinfo = forbidden; socket.create_connection = forbidden
importlib.import_module(target)
find = importlib.import_module('src.tools_knowledge.find_knowledge')
conso = importlib.import_module('src.tools_knowledge.consolidate_knowledge')
helper = importlib.import_module('src.utils.llm_helper')
importlib.import_module('src.tools_knowledge.cs50_precise_evidence')
importlib.import_module('src.tools_knowledge.cs50_extraction_provider')
assert not sdks.intersection(sys.modules)
assert not list(tmp.rglob('*.db'))
if (root/'src/tools_transcribe/import_transcript.py').exists():
    importlib.import_module('src.tools_transcribe.import_transcript')
from src.model_transcribe.data_transcribe import TranscriptDocument, TranscriptSegment
from src.model_knowledge.data_knowledge import ChunkKnowledgeResult, TranscriptKnowledgeDocument
from src.core.config_knowledge import KnowledgeSettings
from src.core.memory import app_session
app_session.logger = logging.getLogger('offline-test')
transcript = TranscriptDocument(source='synthetic.srt', language='en',
    segments=[TranscriptSegment(seg_id=4, start=0, end=50, text='Synthetic text')],
    text='Synthetic text')
chunk = find.build_transcript_chunks(KnowledgeSettings(), transcript)[0]
result = ChunkKnowledgeResult.model_validate({
    'analysis': {'chunk_id':'stub', 'relevant':True, 'needs_visual_context':False},
    'extraction': {'chunk_id':'stub', 'statements':[], 'formulas':[{
        'expression_id':'F1', 'plain_text':'a + b', 'expression_type':'calculation',
        'segment_ids':[], 'start':0, 'end':0,
    }]},
})
find.attach_chunk_provenance(result, chunk)
doc = TranscriptKnowledgeDocument(source_id='verified', language='en',
    transcript_url=None, media_id=None, chunks=[result], visual_candidates=[])
final = conso.consolidate_knowledge(doc)
assert final.source_id == 'verified' and final.language == 'en'
assert final.formulas[0].evidence[0].segment_ids == [4]
assert final.formulas[0].evidence[0].end == 50
assert 'marvin' not in sys.modules
# SDK-dependent functions must cross the import boundary only when called.
for call, expected in [
    (helper.get_openai_client, 'openai'),
    (lambda: helper.configure_marvin(SimpleNamespace()), 'marvin'),
    (lambda: find.extract_knowledge('Text', None, None), 'marvin'),
]:
    try:
        call()
    except ModuleNotFoundError as error:
        assert error.name == expected
    else:
        raise AssertionError('Missing SDK was silently ignored')
assert not sdks.intersection(sys.modules)
# Offline LLM-boundary verification: explicit test doubles after import phase.
# No actual Marvin import, database, Agent construction or API call.
sys.meta_path.remove(blocker)
openai = ModuleType('openai')
client_calls = []
class OpenAI:
    def __init__(self): client_calls.append('construct')
openai.OpenAI = OpenAI
sys.modules['openai'] = openai
assert isinstance(helper.get_openai_client(), OpenAI)
assert client_calls == ['construct']
marvin = ModuleType('marvin'); marvin.defaults = SimpleNamespace(model=None)
calls = []
def fn(*, instructions):
    assert instructions == find.KNOWLEDGE_EXTRACTION_PROMPT
    def decorate(schema):
        assert schema.__name__ == 'extract_knowledge'
        assert list(inspect.signature(schema).parameters) == ['target_chunk','previous_context','next_context']
        assert inspect.signature(schema).return_annotation is ChunkKnowledgeResult
        calls.append('decorate')
        def invoke(*args, **kwargs):
            calls.append(dict(inspect.signature(schema).bind(*args, **kwargs).arguments))
            return result
        return invoke
    return decorate
marvin.fn = fn
sys.modules['marvin'] = marvin
ai = ModuleType('pydantic_ai')
ai.Agent = SimpleNamespace(instrument_all=lambda: calls.append('instrument'))
sys.modules['pydantic_ai'] = ai
helper.configure_marvin(SimpleNamespace(llm_model='offline-model', llm_context=None))
assert marvin.defaults.model == 'offline-model'
assert 'instrument' in calls
for _ in range(2):
    assert find.extract_knowledge('Text', None, None) is result
assert calls.count('decorate') == 1
assert calls[-1] == {'target_chunk':'Text','previous_context':None,'next_context':None}
assert not list(tmp.rglob('*.db'))
print('synchronous import, deterministic processing and offline LLM boundary: passed')
"""
    env = {
        key: os.environ[key]
        for key in ("PATH", "LANG", "TMPDIR", "LD_LIBRARY_PATH")
        if key in os.environ
    }
    result = subprocess.run(
        [sys.executable, "-I", "-c", script, str(root), str(tmp_path), module],
        env=env,
        cwd=tmp_path,
        text=True,
        capture_output=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "passed" in result.stdout
