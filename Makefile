SHELL := /bin/bash
.SHELLFLAGS := -eu -o pipefail -c

ROOT := $(dir $(abspath $(lastword $(MAKEFILE_LIST))))
PROJECT := personal_assistence
LOG_DIR := $(ROOT)/logs
# TODAY := $(shell date +%Y-%m-%d)

.PHONY: \
		ai_code_review \
		clean_linux \
		dependency_check \
		knowledge_extraction \
		litellm_start \
		monitoring_docker \
		monitoring_stop \
		mlflow_fingerprint \
		mlflow_start \
		mlflow_stop \
		pre_commit_update \
		pre_commit_check \
		pre_push_check \
		streamlit

# mlflow_local n8n_quick text_prepare text_extract rag_prepare  # test
# all stop evaluation fire-alert reports

# all:
# 	uv run ruff format
# 	uv run ruff check . --fix
# 	uv run mypy src/

# fmt:
# 	uv run ruff format .

# lint:
# 	uv run ruff check . --fix

# type_check:
# 	uv run mypy src/

# ai_code_review:
# 	uv run pre-commit run ai-review --hook-stage manual


clean_linux:
	bash scripts/clean_linux.sh


dependency_check:
	uv run python src/run_dependency_check.py


# litellm_start:
# 	uv run litellm \
# 		--config \
# 		/workspaces/gmp_compliance/configuration/litellm_config.yaml
# 	# --detailed_debug


mlflow_fingerprint:
	bash scripts/create_experiment.sh

mlflow_start:
	bash scripts/0_setup_mlflow.sh


mlflow_stop:
	pkill -f "mlflow server" || true


knowledge_extraction:
	# tmux new -s knowledge
	PYTHONUNBUFFERED=1 \
	uv run python -m src.run_knowledge_consolidation \
	2>&1 | tee logs/knowledge_consolidation.log

	# tmux attach -t knowledge


monitoring_docker:
	docker compose \
		-p $(PROJECT) \
		-f $(ROOT)/docker/docker-compose.monitoring.yaml \
		up --build -d


monitoring_stop:
	docker compose \
		-p $(PROJECT) \
		-f $(ROOT)/docker/docker-compose.monitoring.yaml \
		down


pre_commit_update:
	@mkdir -p "$(LOG_DIR)"; \
	LOGFILE="$(LOG_DIR)/pre_commit_manual.log"; \
	{ \
		echo "=== pre-commit update ($$(date '+%Y-%m-%d %H:%M:%S')) ==="; \
		uv run pre-commit autoupdate; \
		uv run pre-commit run --all-files; \
		echo " "; \
	} 2>&1 | tee -a "$$LOGFILE"


pre_commit_check:
	@mkdir -p "$(LOG_DIR)"; \
	LOGFILE="$(LOG_DIR)/pre_commit_manual.log"; \
	{ \
		echo "=== 'manual' pre-commit run ($$(date '+%Y-%m-%d %H:%M:%S')) ==="; \
		uv run pre-commit run --all-files; \
		echo " "; \
	} 2>&1 | tee -a "$$LOGFILE"


pre_push_check:
	@mkdir -p "$(LOG_DIR)"; \
	LOGFILE="$(LOG_DIR)/pre_push_manual.log"; \
	{ \
		echo "=== 'manual' pre-push run ($$(date '+%Y-%m-%d %H:%M:%S')) ==="; \
		uv run pre-commit run --hook-stage pre-push --all-files; \
		echo " "; \
	} 2>&1 | tee -a "$$LOGFILE"


streamlit:
	uv run streamlit run streamlit_app.py


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
