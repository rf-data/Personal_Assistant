"""Joint synthetic recovery rehearsal. This is deliberately NOT a backup CLI."""

import hashlib
import sqlite3

import pytest

from scripts.job_control_demo import build_inputs
from src.content_store.backup import backup as content_backup
from src.content_store.backup import restore as content_restore
from src.content_store.errors import IntegrityError
from src.content_store.read_models import ContentReadSettings
from src.content_store.store import ContentStore
from src.evaluation_store.store import EvaluationStore
from src.job_control.controller import Controller
from src.job_control.models import Settings
from src.job_control.operations import backup as job_backup
from src.job_control.operations import restore as job_restore
from tests.content_store_support import OWNER
from tests.review_support import api, gateway, initialize, reviewed, setup_review, token


def test_joint_stopped_restore_preserves_content_review_jobs_and_idempotency(tmp_path):
    env = setup_review(tmp_path)
    original_registration = initialize(env)
    before = reviewed(env)
    jobs = env.tmp / "jobs"
    job_controller = Controller(
        Settings(
            root=jobs,
            catalog=build_inputs(tmp_path / "job-inputs"),
            identities=env.app.controller.settings.identities,
            execution_enabled=True,
        )
    )
    actor = job_controller.authenticate("Bearer " + token(OWNER.subject))
    preview = job_controller.preview(
        actor,
        dict(
            process_id="material_planning",
            parameters=dict(
                source_ref="demo_snapshots", course_id="cs50_python", section="0"
            ),
        ),
    )
    request = dict(preview=preview.model_dump(mode="json"), confirmed=True, start=False)
    job = job_controller.create(actor, request, "synthetic_c26g_job_0001")
    job_controller.store.transition(
        job.job_id, "interrupted", "interrupted", "Synthetic controlled interruption"
    )
    job_controller.store.heartbeat(0)
    config = tmp_path / "controller.json"
    config.write_text(job_controller.settings.model_dump_json())
    config.chmod(0o600)
    content_backup(env.content, tmp_path / "content-snapshot", actor=OWNER)
    job_backup(config, tmp_path / "job-snapshot")

    # There is no integrated EvaluationStore backup API. Rehearse the missing
    # adapter using SQLite's API under its EXISTING exclusive application lock.
    review_db = tmp_path / "review-snapshot.sqlite3"
    ledger = EvaluationStore(env.settings.root)
    with ledger.connection() as source:
        destination = sqlite3.connect(review_db)
        try:
            source.backup(destination)
        finally:
            destination.close()
    review_db.chmod(0o600)
    digest = hashlib.sha256(review_db.read_bytes()).hexdigest()

    restored_content = tmp_path / "restored-content"
    restored_jobs = tmp_path / "restored-jobs"
    restored_review = tmp_path / "restored-review"
    content_restore(tmp_path / "content-snapshot", restored_content, actor=OWNER)
    assert job_restore(tmp_path / "job-snapshot", restored_jobs)["activated"] is False
    restored_review.mkdir(mode=0o700)
    (restored_review / ".review.lock").touch(mode=0o600)
    restored_db = restored_review / "evaluation.sqlite3"
    restored_db.write_bytes(review_db.read_bytes())
    restored_db.chmod(0o600)
    assert hashlib.sha256(restored_db.read_bytes()).hexdigest() == digest
    EvaluationStore(restored_review)  # Full schema, ledger and heads verification.
    restored_settings = env.settings.model_copy(
        update=dict(
            root=restored_review,
            content=ContentReadSettings(
                root=restored_content,
                cursor_key_file=env.settings.content.cursor_key_file,
            ),
        )
    )
    env.app = gateway(restored_settings, restored_jobs)
    env.content = ContentStore(restored_content)
    assert api(env, "GET", "/tasks/positive") == before
    assert api(env, "GET", "/tasks/positive/raw") == b'# \xc3\x84\r\nprint("hello")\n'
    assert api(env, "GET", "/tasks/positive/revisions")
    assert initialize(env) == original_registration
    recovered_jobs = Controller(
        job_controller.settings.model_copy(update=dict(root=restored_jobs))
    )
    assert recovered_jobs.get(actor, job.job_id).status == "interrupted"
    assert (
        recovered_jobs.create(actor, request, "synthetic_c26g_job_0001").job_id
        == job.job_id
    )
    # A fresh controller reads the same restored root; no reinitialization.
    assert Settings.model_validate_json(config.read_bytes()).root == jobs
    with pytest.raises(ValueError):
        job_restore(tmp_path / "job-snapshot", restored_jobs)
    with sqlite3.connect(restored_db) as db:
        db.execute("UPDATE heads SET value='{}'")
    with pytest.raises(IntegrityError):
        EvaluationStore(restored_review)
    # Restore failures never alter the original content/ledger or its authority.
    env.app = gateway(env.settings, jobs)
    assert api(env, "GET", "/tasks/positive") == before
