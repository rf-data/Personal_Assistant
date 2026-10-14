"""Persistent budgets across fresh processes, failures and corrupted receipts."""

import subprocess
import sys
from pathlib import Path

import pytest

from src.tools_knowledge.cs50_budget import (
    BudgetExhausted,
    BudgetIdentity,
    BudgetJournal,
)
from src.tools_knowledge.cs50_checkpoint import CheckpointConflict, fingerprint


def identity(requests=2, tokens=200):
    return BudgetIdentity(
        scope_sha256=fingerprint("scope"),
        allowed_jobs=("job",),
        max_requests=requests,
        max_tokens=tokens,
    )


def test_restart_unknown_and_usage(tmp_path):
    budget = BudgetJournal(tmp_path, identity())
    ref = budget.reserve("job", "a", {"reserved_tokens": 100})
    budget.finish("job", "a", status="unknown")
    assert ref["budget_id"] == identity().budget_id
    fresh = BudgetJournal(tmp_path, identity())
    with pytest.raises(CheckpointConflict, match="already reserved"):
        fresh.reserve("job", "a", {"reserved_tokens": 100})
    fresh.reserve("job", "b", {"reserved_tokens": 100})
    fresh.finish("job", "b", status="done", usage={"total_tokens": 12})
    state = fresh.snapshot()
    assert state.reserved_tokens == 200 and len(state.attempts) == 2
    assert type(state).model_validate_json(state.model_dump_json()) == state
    with pytest.raises(BudgetExhausted):
        fresh.reserve("job", "c", {"reserved_tokens": 1})


@pytest.mark.parametrize("kind", ["broken", "missing", "changed_limits", "foreign"])
def test_conflicts(tmp_path, kind):
    journal = BudgetJournal(tmp_path, identity())
    journal.snapshot()
    if kind == "broken":
        (tmp_path / "budget.v1.json").write_text("{broken")
    elif kind == "missing":
        (tmp_path / "budget.v1.json").unlink()
    elif kind == "changed_limits":
        journal = BudgetJournal(tmp_path, identity(3))
    if kind == "foreign":
        with pytest.raises(CheckpointConflict, match="Foreign"):
            journal.reserve("other", "a", {"reserved_tokens": 1})
    else:
        with pytest.raises(CheckpointConflict):
            journal.snapshot()


def test_concurrent_processes_one_budget(tmp_path):
    payload = identity(1).model_dump_json()
    bootstrap = """import sys
sys.path.insert(0, sys.argv[1])
from src.tools_knowledge.cs50_budget import BudgetJournal,BudgetIdentity,BudgetExhausted
budget=BudgetJournal(sys.argv[2],BudgetIdentity.model_validate_json(sys.argv[3]))
try:
 budget.reserve('job',sys.argv[4],{'reserved_tokens':100})
except BudgetExhausted:
 raise SystemExit(3)
"""
    root = str(Path(__file__).resolve().parents[1])
    children = [
        subprocess.Popen(
            [sys.executable, "-I", "-c", bootstrap, root, str(tmp_path), payload, key],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        for key in ("a", "b")
    ]
    codes = []
    for child in children:
        child.communicate(timeout=15)
        codes.append(child.returncode)
    assert sorted(codes) == [0, 3]
    assert len(BudgetJournal(tmp_path, identity(1)).snapshot().attempts) == 1


@pytest.mark.parametrize("status", ["unknown", "failed"])
def test_failed_attempt_still_consumes_budget(tmp_path, status):
    budget = BudgetJournal(tmp_path, identity(1))
    budget.reserve("job", "a", {"reserved_tokens": 100})
    budget.finish("job", "a", status=status)
    with pytest.raises(BudgetExhausted):
        BudgetJournal(tmp_path, identity(1)).reserve("job", "b", {"reserved_tokens": 1})


@pytest.mark.parametrize("failure", [429, 500, "timeout"])
def test_fake_http_failures_reserve_before_dispatch(tmp_path, failure):
    import httpx
    from test_cs50_knowledge_pilot import chunk

    from src.tools_knowledge.cs50_extraction_provider import (
        OpenAIHTTPProvider,
        RequestBudget,
    )

    journal = BudgetJournal(tmp_path, identity(1, 60000))
    local = RequestBudget()
    local.before_dispatch = lambda reservation: journal.reserve("job", "a", reservation)
    calls = []

    def handle(request):
        calls.append(request)
        assert len(journal.snapshot().attempts) == 1
        if failure == "timeout":
            raise httpx.ReadTimeout("synthetic timeout")
        return httpx.Response(failure)

    provider = OpenAIHTTPProvider(
        api_key="fake",
        model="fake",
        budget=local,
        transport=httpx.MockTransport(handle),
    )
    with pytest.raises((ValueError, httpx.ReadTimeout)):
        provider.extract(chunk(), {})
    provider.close()
    journal.finish("job", "a", status="unknown")
    with pytest.raises(BudgetExhausted):
        BudgetJournal(tmp_path, identity(1, 60000)).reserve(
            "job", "b", {"reserved_tokens": 1}
        )
    assert len(calls) == 1
