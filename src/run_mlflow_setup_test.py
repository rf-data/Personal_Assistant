## run_mlflow_setup_test.py
# import
import mlflow

from src.utils.mlflow_helper import create_mlflow_client, mlflow_fingerprint_check

# configuration - initial setup
client, mlflow_log = create_mlflow_client(initial=True)  # MlflowClient()
assert mlflow.get_tracking_uri().startswith("http"), mlflow_log.error(
    "MLflow tracking URI is not HTTP-based"
)

# --- sanity check: existing experiments ---
experiments = client.search_experiments()
assert len(experiments) > 0, mlflow_log.error(
    "MLflow reachable, but no experiments found"
)

mlflow_log.info(
    f"[SANITY CHECK] --> SUCCESS: MLflow has {len(experiments)} experiments"
)

# --- write check ---
mlflow.set_experiment("restart_check")
with mlflow.start_run():
    mlflow.log_metric("ping", 1)

mlflow_log.info(
    "[WRITE TEST] --> SUCCESS: MLflow write test run created in experiment 'restart_check'"
)

# --- fingerprint check ---
mlflow_fingerprint_check(client, logger=mlflow_log)
