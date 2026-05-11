### Extract from 'Makefile'
```Code
ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PROJECT := rakuten

.PHONY: airflow_docker airflow_stop api_docker api_stop ml_docker ml_stop monitoring_docker monitoring_stop 

all_stop:
	docker stop $(docker ps -a -q)

all_remove:
	docker rm -v $(docker ps -a -q)

api_docker:
	docker compose -p $(PROJECT) -f $(ROOT)/docker-compose.api.yaml up --build -d

api_stop:
	docker compose -p $(PROJECT)  -f $(ROOT)/docker-compose.ml.yaml down

airflow_docker:
	docker compose -p $(PROJECT) --env-file env/airflow.env -f $(ROOT)/docker-compose.airflow.yaml up --build -d

airflow_stop:
	docker compose -p $(PROJECT) -f $(ROOT)/docker-compose.airflow.yaml down

ml_docker:
	docker compose -p $(PROJECT) -f $(ROOT)/docker-compose.ml.yaml up --build -d

ml_stop:
	docker compose -p $(PROJECT)  -f $(ROOT)/docker-compose.api.yaml down

monitoring_docker:
	docker compose -p $(PROJECT) -f $(ROOT)/docker-compose.monitoring.yaml up --build -d

monitoring_stop:
	docker compose -p $(PROJECT) -f $(ROOT)/docker-compose.monitoring.yaml down
```
