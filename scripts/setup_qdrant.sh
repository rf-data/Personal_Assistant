
#!/bin/sh
# The former public-port test starter is retired. Never deploy implicitly.
set -eu
printf '%s\n' \
  'Qdrant requires the reviewed deployment/qdrant/compose.v1.yaml configuration.' \
  'Read docs/qdrant/c21q_deployment.md and obtain explicit Phase B approval.' >&2
exit 2
