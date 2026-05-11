# Airflow + Pipelines
```code 
architecture-beta
    group orchestration(server)[Airflow and Pipelines]

    service postgres(database)[PostgreSQL] in orchestration
    service airflow(server)[Airflow] in orchestration
    junction junc1
    junction junc2
    junction junc3
    service etl(server)[ETL Pipeline] in orchestration
    service similarity(server)[Similarity Pipeline] in orchestration
    service recommender(server)[Recommend Pipeline] in orchestration

    postgres:R -- L:airflow
    airflow:B -- T:junc2
    junc1:R -- L:junc2
    junc2:R -- L:junc3
    junc1:B --> T:etl
    junc2:B --> T:similarity
    junc3:B --> T:recommender

```
# APIs
```
architecture-beta
    group apis(cloud)[FastAPI]

    service fast(cloud)[FastAPI] in apis
    junction junc1
    junction junc2
    junction junc3
    service etl_trigger(cloud)[ETL Trigger] in apis
    service sim_trigger(cloud)[SimMatrix Trigger] in apis
    service rec_trigger(cloud)[Recommend Trigger] in apis

    fast:B -- T:junc2
    junc1:R -- L:junc2
    junc2:R -- L:junc3
    junc1:B -- T:etl_trigger
    junc2:B -- T:sim_trigger
    junc3:B -- T:rec_trigger

```

# Orchestration
```
architecture-beta
    group apis(cloud)[FastAPI]

    service fast(cloud)[FastAPI] in apis
    junction junc_api1
    junction junc_api2
    junction junc_api3
    service etl_trigger(cloud)[ETL Trigger] in apis
    service sim_trigger(cloud)[SimMatrix Trigger] in apis
    service rec_trigger(cloud)[Recommend Trigger] in apis

    fast:R -- L:junc_api2
    junc_api1:B -- T:junc_api2
    junc_api2:B -- T:junc_api3
    junc_api1:R -- L:etl_trigger
    junc_api2:R -- L:sim_trigger
    junc_api3:R -- L:rec_trigger

    group orchestration(server)[Airflow and Pipelines]

    service postgres(database)[PostgreSQL] in orchestration
    service airflow(server)[Airflow] in orchestration
    junction junc1
    junction junc2
    junction junc3
    service etl(server)[ETL Pipeline] in orchestration
    service similarity(server)[Similarity Pipeline] in orchestration
    service recommender(server)[Recommend Pipeline] in orchestration

    postgres:B -- T:airflow
    airflow:L -- R:junc2
    junc1:B -- T:junc2
    junc2:B -- T:junc3
    junc1:L --> R:etl
    junc2:L --> R:similarity
    junc3:L --> R:recommender

    etl_trigger:R --> L:etl
    sim_trigger:R --> L:similarity
    rec_trigger:R --> L:recommender
```

# Microservice (Docker)
```
architecture-beta
    group micro(cloud)[Microservice Stack]

    service docker(server)[Docker] in micro
    service moni(cloud)[Monitoring] in micro
    service apis(cloud)[FastAPI] in micro
    service air(cloud)[Airflow] in micro
    service ml(cloud)[MLflow] in micro
    junction j1
    junction j2

    j1:R -- L:docker
    docker:R -- L:j2

    air:B -- T:j1
    apis:T -- B:j1
    moni:B -- T:j2
    ml:T -- B:j2
```

# MLflow
```
architecture-beta
    group experiment_tracking(cloud)[Experiment Tracking]

    service mlflow(cloud)[MLflow] in experiment_tracking
```

# Monitoring
```
architecture-beta
    group monitoring(internet)[Monitoring Stack]

    service prom(internet)[Prometheus] in monitoring
    service graf(internet)[Grafana] in monitoring
    service node(server)[Node Exporter] in monitoring

    node:R --> L:prom
    prom:R --> L:graf
```

# entire structure
```
---
config:
  layout: elk
  look: neo
---
flowchart TB
 subgraph CI["CI/CD"]
        git["Git Repo"]
        release["Milestone Pipeline"]
  end
 subgraph DS["Data Sources"]
        mongo["MongoDB"]
        postgres["PostgreSQL"]
  end
 subgraph ORCH["Airflow & Pipelines"]
        airflow["Airflow"]
        etl["ETL Pipeline"]
        sim["Similarity Matrix Pipeline"]
        rec["Recommendation Pipeline"]
  end
 subgraph API["API Layer"]
        api1["Trigger ETL"]
        api2["Trigger Similarity"]
        api3["Trigger Recommendation"]
  end
 subgraph EXP["MLflow Tracking"]
        mlflow["MLflow"]
  end
 subgraph MON["Monitoring"]
        prom["Prometheus"]
        graf["Grafana"]
        nodeexp["Node Exporter"]
  end
 subgraph DOCKER["Docker Compose"]
        d_airflow["airflow-docker"]
        d_api["api-docker"]
        d_ml["mlflow-docker"]
        d_mon["monitoring-docker"]
  end
    mongo --> etl
    etl --> sim
    sim --> rec & mlflow
    rec --> mlflow
    postgres --> airflow
    airflow --> etl & sim & rec
    api1 --> etl
    api2 --> sim
    api3 --> rec
    nodeexp --> prom
    prom --> graf
    git --> release
    release --> airflow
    d_airflow --> ORCH
    d_api --> API
    d_ml --> EXP
    d_mon --> MON
```