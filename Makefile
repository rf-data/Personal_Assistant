ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PROJECT := personal_assistence

.PHONY: all fmt lint type_check monitoring_docker monitoring_stop
# mlflow_local n8n_quick text_prepare text_extract rag_prepare  # test
# all stop evaluation fire-alert reports  

all: fmt lint type_check

clean_linux:
	bash scripts/clean_linux.sh

fmt:
	uv run ruff format .

lint:
	uv run ruff check . --fix

monitoring_docker:
	docker compose -p $(PROJECT) -f $(ROOT)/docker/docker-compose.monitoring.yaml up --build -d

monitoring_stop:
	docker compose -p $(PROJECT) -f $(ROOT)/docker/docker-compose.monitoring.yaml down

type_check:
	uv run mypy src/


# api_start:
# 	uvicorn fastapi_main:app --host 0.0.0.0 --port 8000
	
# mlflow_local:
# 	${ROOT}/scripts/0_setup_mlflow.sh

# n8n_quick:
# 	docker run -it --rm -p 5678:5678 -v ~/.n8n:/home/node/.n8n n8nio/n8n

# text_prepare:
# 	python -m src.run_text_preparation

# text_extract:
# 	python -m src.run_text_extraction

# rag_prepare:
# 	python -m src.run_rag_preparation

	
# all: 
# 	docker compose -p $(PROJECT) -f $(ROOT)/docker-compose.yaml up --build -d

# stop: 
# 	docker compose -p $(PROJECT) -f $(ROOT)/docker-compose.yaml down

# evaluation:
# 	docker compose -p $(PROJECT)-f $(ROOT)/docker-compose.eval.yaml up --build -d

# fire-alert:
# 	docker compose -p $(PROJECT) -f $(ROOT)/docker-compose.yaml stop bike-api

# reports:
# 	python3 $(ROOT)/src/main_drift.py

