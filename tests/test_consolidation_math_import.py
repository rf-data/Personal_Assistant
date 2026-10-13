"""Import the real consolidation module in a clean, offline subprocess."""

import subprocess
import sys
from pathlib import Path


def test_real_import_and_formula_consolidation():
    root = Path(__file__).resolve().parents[1]
    script = r"""
import importlib
import json
import socket
import sys
from types import ModuleType, SimpleNamespace

sys.path.insert(0, sys.argv[1])

def forbidden(*args, **kwargs):
    raise AssertionError("No external calls or app IO permitted")

def block_network(*args, **kwargs):
    raise AssertionError("Network access forbidden during test")

# socket.socket = forbidden
socket.socket.connect = block_network
socket.socket.connect_ex = block_network
socket.create_connection = block_network
socket.getaddrinfo = block_network

# socket.getaddrinfo = forbidden
# Only environment/logger/file-IO dependencies are substituted. Target module,
# Pydantic models and both normalization helpers use their real import paths.
for name, attrs in {
    "src.core.memory": {"app_session": SimpleNamespace()},
    "src.core.logger": {"create_logger": forbidden},
    "src.core.config": {"folder_env_vars": SimpleNamespace()},
    "src.utils.path_helper": {"shorten_path": forbidden},
    "src.utils.dict_helper": {"save_dict": forbidden, "load_dict": forbidden},
}.items():
    module = ModuleType(name)
    module.__dict__.update(attrs)
    sys.modules[name] = module

consolidation = importlib.import_module("src.tools_knowledge.consolidate_knowledge")
latex = importlib.import_module("src.utils.latex_helper")
assert consolidation.normalize_math_text is latex.normalize_math_text
assert "marvin" not in sys.modules
assert "openai" not in sys.modules
assert "faster_whisper" not in sys.modules

models = importlib.import_module("src.model_knowledge.data_knowledge")
results = []
for index, expression in enumerate(["a + b", "a+b"]):
    results.append({
        "analysis": {"chunk_id": f"chunk_{index}", "relevant": True,
                     "needs_visual_context": False},
        "extraction": {"chunk_id": f"chunk_{index}", "statements": [], "formulas": [{
            "expression_id": f"F{index}", "plain_text": expression, "latex": expression,
            "expression_type": "calculation", "segment_ids": [1], "start": 1.0, "end": 3.0,
        }]},
    })
document = models.TranscriptKnowledgeDocument(
    source_id="verified_test_source", transcript_url="https://example.com/transcript.srt",
    media_id=None, chunks=results, visual_candidates=[],
)
# master still lacks source_id until independent PR #10 merges. Keep this test
# focused on the import fix without altering production models.
if "source_id" not in models.TranscriptKnowledgeDocument.model_fields:
    object.__setattr__(document, "source_id", "verified_test_source")
original = consolidation.normalize_math_text
calls = []
def tracked(value):
    calls.append(value)
    return original(value)
consolidation.normalize_math_text = tracked
result = consolidation.consolidate_knowledge(document)
assert calls and set(calls) == {"a + b", "a+b"}
assert len(result.formulas) == 1
assert len(result.formulas[0].evidence) == 2
assert result.source_id == "verified_test_source"
print(json.dumps({"import": "ok", "formula_count": len(result.formulas), "helper_calls": len(calls)}))
"""
    result = subprocess.run(
        [sys.executable, "-I", "-c", script, str(root)],
        capture_output=True,
        text=True,
        timeout=30,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert '"import": "ok"' in result.stdout
