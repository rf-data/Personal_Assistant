"""Private gateway readiness: trusted TLS plus the existing C16 auth boundary."""

import http.client
import os
import ssl


def main():
    context = ssl.create_default_context(cafile="/run/tls/ca.crt")
    connection = http.client.HTTPSConnection(
        os.environ["API_DNS"], 8443, timeout=2, context=context
    )
    try:
        connection.request(
            "GET",
            "/v1/processes",
            headers={"Authorization": "Bearer health-probe-invalid"},
        )
        response = connection.getresponse()
        return 0 if response.status == 401 else 1
    finally:
        connection.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError):
        raise SystemExit(1) from None
