with DAG(
    dag_id="train_knn_with_mlflow",
    start_date=datetime(2024, 1, 1),
    schedule_interval="@monthly",
    catchup=False,
    tags=["mlops", "mlflow"],
) as dag:

    train_knn = DockerOperator(
        task_id="train_knn",
        image="mymlops-knn_trainer",
        command="python src/knn_mlflow.py",
        docker_url="unix://var/run/docker.sock",
        network_mode="mlops-net",
        auto_remove=False,
        environment={
            "MLFLOW_TRACKING_URI": "http://mlflow:5000",
            "MONGO_URI": "mongodb://host.docker.internal:27017",
            "DB_NAME": "rakuten_db",
            "COLLECTION_NAME": "products",
        },
    )
