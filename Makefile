ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PROJECT := gmp_compliance

.PHONY: lint mlflow_local n8n_quick text_prepare text_extract rag_prepare type_check all fmt # test
# all stop evaluation fire-alert reports  

fmt:
	uv run ruff format .

lint:
	uv run ruff check . --fix

type_check:
	uv run mypy src/

all: fmt lint type_check

api_start:
	uvicorn fastapi_main:app --host 0.0.0.0 --port 8000
	
mlflow_local:
	${ROOT}/scripts/0_setup_mlflow.sh

n8n_quick:
	docker run -it --rm -p 5678:5678 -v ~/.n8n:/home/node/.n8n n8nio/n8n

text_prepare:
	python -m src.run_text_preparation

text_extract:
	python -m src.run_text_extraction

rag_prepare:
	python -m src.run_rag_preparation

	
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

