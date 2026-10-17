"""Acceptance-only loopback server using the unchanged production HTTP handler.

Own process, ephemeral port, explicit synthetic configuration. Never a registry
process or production deployment. stdout contains readiness, never credentials.
"""

import argparse
import json
import socket
from http.server import HTTPServer

from src.job_control.controller import Controller
from src.job_control.http import Application, handler_for
from src.job_control.models import load_settings


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", required=True)
    parser.add_argument("--port", type=int, default=0)
    parser.add_argument(
        "--metrics",
        action="store_true",
        help="Read test store aggregates and exit without a listener",
    )
    args = parser.parse_args()

    def forbidden(*args, **kwargs):
        raise RuntimeError("Acceptance server forbids outgoing connections")

    socket.socket.connect = forbidden
    settings = load_settings(args.config)
    controller = Controller(settings)
    if args.metrics:
        from src.job_control.metrics import render_metrics

        print(
            render_metrics(
                controller.store, settings.worker_ttl, settings.identities[0].courses
            ),
            end="",
        )
        return
    application = Application(controller)
    with HTTPServer(("127.0.0.1", args.port), handler_for(application)) as server:
        print(json.dumps(dict(port=server.server_port)), flush=True)
        server.serve_forever(poll_interval=0.05)


if __name__ == "__main__":
    main()
