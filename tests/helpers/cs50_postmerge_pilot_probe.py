"""Run the portable pytest pilot fixtures; no separate global-variable overlay."""

import sys
from pathlib import Path

import pytest


def main():
    tests = Path(__file__).resolve().parents[1]
    selected = {
        "test_cs50_knowledge_pilot.py": [
            "test_fake_llm_full_pilot_binding",
            "test_fake_worker_two_chunks",
        ],
        "test_cs50_precise_evidence.py": [
            "test_full_pilot_preserves_source_and_consolidates",
            "test_invalid_provider_saved_no_precise_output",
        ],
        "test_cs50_quality.py": [
            "test_capture_before_overwrite_on_synthetic_concept_fixture",
        ],
    }
    return pytest.main(
        [
            f"{tests / module}::{name}"
            for module, names in selected.items()
            for name in names
        ]
        + ["-q"]
    )


if __name__ == "__main__":
    sys.exit(main())
