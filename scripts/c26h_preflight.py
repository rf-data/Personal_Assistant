"""Read-only H staging contract checks; no host, secrets, stores or deployment."""

import argparse
import copy
import json
from pathlib import Path
from types import SimpleNamespace

from scripts.c26g_preflight import check as check_g
from scripts.c26g_preflight import load
from scripts.https_preflight import require
from src.content_store.read_models import ContentReadSettings
from src.content_store.search_models import SearchSettings
from src.evaluation_store.models import ReviewSettings
from src.job_control.http import Application
from src.job_control.models import Settings

CONFIGURATION = "/app/configuration/c26-runtime/"
API_COMMAND = ["api", "--config", CONFIGURATION + "controller.json", "--port", "8016"]
BINDINGS = [
    "--content-config",
    CONFIGURATION + "content.json",
    "--review-config",
    CONFIGURATION + "review.json",
    "--search-config",
    CONFIGURATION + "search.json",
]


def check(backend, ui, controller, content, review, search, **https):
    """Check effective Compose plus all explicit existing versioned settings."""
    services = backend["services"]
    require(services["api"]["command"] == API_COMMAND + BINDINGS, "h_api_bindings")
    require(
        services["api"]["healthcheck"]["test"]
        == [
            "CMD",
            "python",
            "-m",
            "scripts.deployment",
            "health",
            "--role",
            "api",
            "--config",
            CONFIGURATION + "controller.json",
            *BINDINGS,
        ],
        "h_health_bindings",
    )
    # G enforces the predecessor's exact command. First check the H command,
    # then project only that field to its G representation; all other G checks
    # run unchanged. Never mutate the caller's effective Compose input.
    previous = copy.deepcopy(backend)
    previous["services"]["api"]["command"] = API_COMMAND
    require(ui.get("name") == "personal-assistant-c26h-ui-staging", "staging_ui_name")
    ui_role = ui["services"]["ui"]
    require(
        ui_role.get("profiles") == ["c26-ui-staging-approved"]
        and ui_role.get("restart") == "no"
        and ui_role.get("pull_policy") == "never",
        "inactive_manual_ui",
    )
    previous_ui = copy.deepcopy(ui)
    previous_ui["services"]["ui"]["restart"] = "unless-stopped"
    result = check_g(previous, previous_ui, controller, **https)
    require(backend.get("name") == "personal-assistant-c26h-staging", "staging_name")
    content = ContentReadSettings.model_validate(content)
    review = ReviewSettings.model_validate(review)
    search = SearchSettings.model_validate(search)
    require(review.content == content, "same_content_binding")
    require(
        not review.writes_enabled
        and not review.real_reviews_enabled
        and not review.grants
        and review.owner_authorization_reference is None,
        "disabled_review",
    )
    require(
        str(content.root) == "/app/runtime-state/content"
        and str(review.root) == "/app/runtime-state/reviews"
        and str(search.index_root) == "/app/runtime-state/index"
        and str(content.cursor_key_file)
        == CONFIGURATION + "secrets/content-cursor.key",
        "h_roots_and_key_reference",
    )
    Application(
        SimpleNamespace(settings=Settings.model_validate(controller)),
        content_settings=content,
        review_settings=review,
        search_settings=search,
    )
    for name, role in services.items():
        require(
            0 < float(role["cpus"]) <= 2 and 0 < int(role["pids_limit"]) <= 512,
            "bounded_cpu_pids",
        )
        memory = role["mem_limit"]
        if isinstance(memory, str) and memory.endswith("m"):
            memory = int(memory[:-1]) * 1024**2
        swap = role["memswap_limit"]
        if isinstance(swap, str) and swap.endswith("m"):
            swap = int(swap[:-1]) * 1024**2
        require(
            0 < int(memory) <= 2 * 1024**3 and int(swap) == int(memory),
            "bounded_memory",
        )
        require(
            role["logging"]
            == {"driver": "json-file", "options": {"max-size": "10m", "max-file": "3"}},
            "bounded_logs",
        )
        require(role.get("stop_grace_period") in {"30s", "30"}, "stop_grace")
        mounts = role["volumes"]
        targets = {v["target"] for v in mounts}
        expected = (
            {"/etc/caddy/Caddyfile", "/run/tls"}
            if name == "api-gateway"
            else {
                "/app/runtime-state",
                "/app/configuration",
                "/app/data",
                "/app/logs",
                "/app/.cache",
            }
        )
        require(
            len(targets) == len(mounts) and targets == expected, "exact_role_mounts"
        )
        require(len({v["source"] for v in mounts}) == len(mounts), "distinct_sources")
        sources = [Path(v["source"]) for v in mounts]
        require(
            all(".." not in p.parts for p in sources)
            and not any(
                a.is_relative_to(b) for a in sources for b in sources if a != b
            ),
            "separate_host_sources",
        )
        if name == "api-gateway":
            require(all(v.get("read_only") is True for v in mounts), "readonly_gateway")
        else:
            require(
                role["environment"]
                == {
                    "PA_PERSISTENT_ROOTS_FILE": CONFIGURATION + "persistent-roots.json"
                },
                "persistent_root_policy",
            )
    result.update(
        status="offline_staging_contract_valid",
        protocol="c26h-staging/1",
        configuration_bindings="checked_without_opening_stores",
    )
    # Runtime wiring is locally present; actual permissions/mounts and initialized
    # stores remain a manual gate, together with all G trust blockers.
    result["live_blockers"] = [
        b
        for b in result["live_blockers"]
        if b != "content_review_search_runtime_wiring"
    ] + ["actual_mount_permissions_and_store_initialization"]
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    for key in (
        "backend-compose-json",
        "ui-compose-json",
        "controller",
        "content",
        "review",
        "search",
    ):
        parser.add_argument("--" + key, type=Path, required=True)
    for key in ("origin", "tls-router", "http-router", "middleware"):
        parser.add_argument("--" + key, required=True)
    args = parser.parse_args(argv)
    try:
        result = check(
            *(
                load(getattr(args, k))
                for k in (
                    "backend_compose_json",
                    "ui_compose_json",
                    "controller",
                    "content",
                    "review",
                    "search",
                )
            ),
            **{
                k: getattr(args, k)
                for k in ("origin", "tls_router", "http_router", "middleware")
            },
        )
    except (
        ValueError,
        TypeError,
        KeyError,
        OSError,
        AttributeError,
        RecursionError,
        OverflowError,
    ):
        print(
            json.dumps(
                dict(
                    status="refused",
                    production_release="HOLD",
                    deployment_permitted=False,
                )
            )
        )
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
