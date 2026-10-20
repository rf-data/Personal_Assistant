"""Synthetic-only real HTTP C16/C24 acceptance server; never a production role.

Reuses the existing verified-code/index fixture and actual Executor. Restart with
--reuse preserves the same isolated store and catalog. No external IO.
"""

import argparse
import json
import select
import socket
import sys
from http.server import HTTPServer
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument("--reuse", action="store_true")
    parser.add_argument("--cert", type=Path)
    parser.add_argument("--key", type=Path)
    args = parser.parse_args()

    def no_outgoing(*a, **kw):
        raise RuntimeError("Synthetic acceptance server forbids outbound connections")

    socket.socket.connect = no_outgoing
    from src.content_store.store import ContentStore
    from src.job_control.controller import Controller
    from src.job_control.executor import Executor
    from src.job_control.http import Application, handler_for
    from src.job_control.index_models import IndexJobPlan
    from src.job_control.models import Settings
    from tests.index_job_support import setup

    root = args.workspace
    if args.reuse:
        settings = Settings.model_validate_json((root / "settings.json").read_bytes())
        spec = IndexJobPlan.model_validate_json(
            (root / "approved/index.v1.json").read_bytes()
        )
    else:
        root.mkdir(mode=0o700)
        env = setup(root)
        settings, spec = env.settings, env.spec
        (root / "settings.json").write_text(settings.model_dump_json())
        (root / "settings.json").chmod(0o600)
    controller = Controller(settings)
    application = Application(
        controller, content_settings=spec.content, search_settings=spec.search
    )
    executor = Executor(settings)
    try:
        with HTTPServer(("127.0.0.1", args.port), handler_for(application)) as server:
            if args.cert and args.key:
                import ssl

                context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                context.load_cert_chain(args.cert, args.key)
                server.socket = context.wrap_socket(server.socket, server_side=True)
            server.timeout = 0.05
            print(json.dumps({"port": server.server_port, "ready": True}), flush=True)
            while True:
                server.handle_request()
                executor.step()
                if select.select([sys.stdin], [], [], 0)[0]:
                    action = sys.stdin.readline().strip()
                    if action == "close" or not action:
                        break
                    if action == "revoke-viewer":
                        from tests.content_store_support import OWNER

                        content = ContentStore(spec.content.root)
                        sid = spec.source_ids[0]
                        source = content.get_source(sid, actor=OWNER)
                        content.set_source_grants(
                            sid,
                            (),
                            expected_acl_revision=source.acl_revision,
                            actor=OWNER,
                        )
                        print('{"revoked":true}', flush=True)
                    else:
                        raise ValueError("Unknown synthetic action")
    finally:
        executor.close()


if __name__ == "__main__":
    main()
