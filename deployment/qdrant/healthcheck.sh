#!/bin/bash
# Qdrant v1.19.1 /readyz is intentionally exempt from API-key authentication.
# Uses Bash builtins only: the official CPU image does not promise curl/wget.
set -euo pipefail
exec 3<>/dev/tcp/127.0.0.1/6333
printf 'GET /readyz HTTP/1.1\r\nHost: localhost\r\nConnection: close\r\n\r\n' >&3
IFS= read -r status <&3
[[ "$status" == $'HTTP/1.1 200 '* || "$status" == $'HTTP/1.0 200 '* ]]
