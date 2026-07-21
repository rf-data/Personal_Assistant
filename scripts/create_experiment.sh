#!/usr/bin/env bash

# exit on error
set -e

# ----------------------------
# Paths & logging
# ----------------------------
PROJECT_ROOT="$( cd "$( dirname "${BASH_SOURCE[0]}" )/.." &> /dev/null && pwd )"

mkdir -p "$PROJECT_ROOT/logs"
LOGFILE="$PROJECT_ROOT/logs/0_mlflow_setup.log"

# ----------------------------
# Load environment variables
# ----------------------------
{
  echo ""
  echo "===== START CREATING MLFLOW_FINGERPRINT [$(date '+%Y-%m-%d %H:%M:%S')] ===="
  if [ -f "$PROJECT_ROOT/.env" ]; then
    echo "Loading environment variables from ../.env"
    set -o allexport
    source "$PROJECT_ROOT/.env"
    set +o allexport
  else
    echo ""
    echo "No .env file found - relying on defaults"
  fi

  mlflow experiments create \
    --experiment-name fingerprint \
    --artifact-location file:////workspaces/gmp_compliance/mlflow/artifacts


} >> "$LOGFILE" 2>&1
