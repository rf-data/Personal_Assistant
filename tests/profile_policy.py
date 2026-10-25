"""Explicit opt-in boundary, applied before any external test fixture runs."""

import pytest

EXTERNAL_FILES = {
    "test_content_http.py",
    "test_deployment_transport.py",
    "test_worker_image_content.py",
    "test_cs50_uv_installed_integration.py",
    "test_lazy_marvin_import.py",
    "test_https_preflight.py",
    "test_cs50_index_cli.py",
    "test_cs50_index_contract.py",
    "test_cs50_index_end_to_end.py",
    "test_cs50_ingestion.py",
    "test_cs50_knowledge_index_checkpoint.py",
    "test_cs50_knowledge_index_mapping.py",
    "test_cs50_retrieval.py",
    "test_cs50_retrieval_evaluation.py",
}
EXTERNAL_TESTS = {
    "test_real_local_http_server_and_process_restart",
    "test_small_host_compose_render_without_daemon",
    "test_compose_cli_resolves_only_explicit_profiles",
    "test_native_compose_default_and_all_profiles",
    "test_installed_provider_configuration_without_api",
    "test_offline_local_original_pilot",
    "test_real_local_pilot",
    "test_real_export_five_ids_provenance_and_worker_admission",
    "test_real_export_child_ids_still_explicitly_blocked",
    "test_real_python0_pilot",
    "test_optional_exact_week0_export",
    "test_optional_original_python_notes_read_only",
    "test_optional_original_pdf_preserves_text_and_all_misclassifications",
    "test_privileged_root_owned_mounts_real_worker_handoff",
    "test_real_children_rejected_even_with_hash_bound_overview_in_bundle",
    "test_real_operator_exports_read_only",
}


def pytest_addoption(parser):
    parser.addoption(
        "--run-external",
        action="store_true",
        help="Explicit external integration opt-in",
    )


def pytest_collection_modifyitems(config, items):
    for item in items:
        if item.path.name in EXTERNAL_FILES or item.originalname in EXTERNAL_TESTS:
            item.add_marker(pytest.mark.external_integration)
        if item.get_closest_marker("external_integration") and not config.getoption(
            "--run-external"
        ):
            item.add_marker(
                pytest.mark.skip(reason="External integration requires --run-external")
            )
