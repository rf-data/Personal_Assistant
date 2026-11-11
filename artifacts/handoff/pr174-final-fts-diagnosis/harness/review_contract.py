"""Review original adapter handler and correct the diagnostic prefix assumption.

Does not rerun any search and does not rewrite the recorded measurements.
"""
import ast
import inspect
import json
import os
from pathlib import Path

from src.content_store.errors import Unavailable
from src.tools_rag import content_fts

artifact = Path(__file__).resolve().parents[1]
assert Path(content_fts.__file__).is_relative_to(Path(os.environ['FTS_DIAG_TARGET']))
function = ast.parse(inspect.getsource(content_fts.search_database)).body[0]
handler = next(n for n in ast.walk(function) if isinstance(n, ast.ExceptHandler))
assert isinstance(handler.type, ast.Attribute) and handler.type.value.id == 'sqlite3' and handler.type.attr == 'Error'
assert len(handler.body) == 1
statement = handler.body[0]
assert isinstance(statement, ast.Raise) and isinstance(statement.cause, ast.Constant) and statement.cause.value is None
assert statement.exc.func.id == 'Unavailable'
assert [arg.value for arg in statement.exc.args] == ['FTS query/database unavailable']
expected = str(Unavailable('FTS query/database unavailable'))
assert expected == 'unavailable: FTS query/database unavailable'
errors = json.loads((artifact / 'evidence/contention-searches.json').read_text())
assert len(errors) == 6
assert all(e['public_outcome'] == 'Unavailable' and e['public_native_context_code'] == 9 for e in errors)
result = dict(
    original_adapter_handler_ast_verified=True,
    unchanged_public_type='Unavailable',
    unchanged_public_code='unavailable',
    unchanged_public_message=expected,
    display_context_suppressed_by_original_raise_from_none=True,
    six_measured_native_context_codes=[e['public_native_context_code'] for e in errors],
    measured_contract_boolean_usable=False,
    diagnostic_mistake="The initial comparator omitted ContentStoreError's 'unavailable: ' prefix; false is a harness assertion value, not a changed product contract.",
    correction='Checker corrected; raw search evidence retained unchanged; no requests repeated.',
    contract_violation_observed=False,
)
(artifact / 'evidence/contract-review.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
