import time
from datetime import datetime
import os
import logging

import requests
import numpy as np
from prometheus_client import Counter, Histogram, generate_latest, CollectorRegistry

from fastapi import FastAPI, HTTPException, Response, Request
from fastapi.responses import JSONResponse

import utils as utils


# --- Logging Configuration ---
logging.basicConfig(level=logging.DEBUG)

logger = logging.getLogger("API_demo")

# --- FastAPI App Initialization ---
app = FastAPI()

utils.load_env_vars(f_name=".env.fastapi")

# --- Prometheus Metrics Definitions ---
registry = CollectorRegistry()

api_request_total = Counter(name="api_requests_total", 
                            documentation="Total number of API requests", 
                            labelnames=['endpoint', 'method', 'status_code'],
                            registry=registry
                            )

api_request_duration_seconds = Histogram(name="api_request_duration_seconds", 
                                        documentation="API request duration in seconds", 
                                        labelnames=['endpoint', 'method', 'status_code'],
                                        registry=registry
                                        )


# --- Global Variables for Model and Data ---
AIRFLOW_URL = "http://airflow-webserver:8080/api/v1"
DAG_ID = "data_processing_pipeline"

# --- Pydantic Models for API Input/Output ---


# --- API middle ware --- exception handling ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception")
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )

@app.middleware("http")
async def log_requests(request: Request, call_next):
    logger.info(f"START {request.method} {request.url.path}")
    response = await call_next(request)
    logger.info(f"END {request.url.path} → {response.status_code}")
    return response

# --- API Endpoints ---
# Health Check Endpoint
@app.get("/")
def root():
    return {"message": "FastAPI ETL Trigger Active", 
            "status": "ok"}

# Sample French Texts Endpoint -- used in live demo (streamlit)
texts = ["Je vais bien. Comment allez-vous ?",
            "J’ai faim.", 
            "J’ai soif.",
            "Ça ne va pas très bien.",
            "Je m’ennuie. ",
            "Je n’ai plus envie. J’ai besoin d’une pause.", 
            "D’accord.", 
            "Pas d’accord.", 
            "Je comprends.",
            "Je ne comprends pas.", 
           " C’est facile."
            "C’est difficile.",
            "Pas de problème.",
            "Ça marche.",
            "On verra.",
            "J’ai oublié.",
            "Je suis pressé.",
            "À plus tard."
            ]

@app.get("/french")         # 
def french():
    start_time = time.time()
    status_code = "200"

    try:
        if not texts:
            raise RuntimeError("texts is empty")
        
        text = np.random.choice(texts, size=1)[0]
        
        return {
            # "status": "ok",
            "message": str(text)
            }

    except HTTPException as he:
        status_code = str(he.status_code)
        raise
    except requests.exceptions.RequestException as re:
        print(f"    - Error sending request {i+1}: {re}")

    except Exception as e:
        # print(f"Error during demo: {e}")
        logger.exception("French endpoint failed")
        status_code = "500"
        raise HTTPException(status_code=500, 
                    detail=f"Triggering '/french' failed due to an internal error: {e}")

    finally:
        end_time = time.time()
        duration = end_time - start_time
        api_request_duration_seconds.labels(
                                        endpoint="/french", 
                                        method="GET", 
                                        status_code=str(status_code)
                                        ).observe(duration)
        api_request_total.labels(
                            endpoint="/french", 
                             method="GET", 
                             status_code=str(status_code)
                             ).inc()

# ETL Pipeline Trigger Endpoint
@app.post("/trigger-etl")
def trigger_etl():
    status_code = "200"

    admin_user = os.getenv("AIRFLOW_ADMIN_USER", None)
    admin_password = os.getenv("AIRFLOW_ADMIN_PASSWORD", None)

    if not admin_user or not admin_password:
        logger.error("Error during trigger: missing airflow credentials in environment variables")
        status_code = "500"
        raise HTTPException(status_code=500, 
                            detail="Airflow admin credentials are not set in environment variables.")

    start_time = time.time()

    try:
        dag_run_id = f"api_trigger_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        response = requests.post(
            f"{AIRFLOW_URL}/dags/{DAG_ID}/dagRuns",
            auth=(admin_user, admin_password),                # Airflow credentials
            json={
                "dag_run_id": dag_run_id,
                "conf": {"comment": "PLACEHOLDER -- dynamic input"}
            })

        if response.status_code != 200:
            return {"error": response.text}

        return {
            "status": "Pipeline triggered",
            "dag_run_id": dag_run_id
        }
    
    except HTTPException as e:
        status_code = str(e.status_code)
        raise

    except Exception as e:
        logger.error(f"Error during trigger: {e}")
        status_code = "500"
        raise HTTPException(status_code=500, 
                            detail=f"Triggering ETL-pipeline failed due to an internal error: {e}")
    finally:
        end_time = time.time()
        duration = end_time - start_time
        api_request_duration_seconds.labels(
                                        endpoint="/trigger-etl", 
                                        method="POST", 
                                        status_code=str(status_code)
                                        ).observe(duration)
        api_request_total.labels(
                            endpoint="/trigger-etl", 
                             method="POST", 
                             status_code=str(status_code)
                             ).inc()

# Prometheus Metrics Endpoint
@app.get("/metrics")
async def metrics():
    """
    Expose Prometheus metrics.
    """
    return Response(content=generate_latest(registry), media_type="text/plain")

@router.post("/trigger")
def trigger_etl():
    """
    Triggers the ETL Airflow DAG via the Airflow REST API.

    Returns:
    - status: confirmation message
    - dag_run_id: unique ID of the triggered DAG run
    """
    start_time = time.time()
    status_code = "200"

    try:
        # Create a unique DAG run ID
        dag_run_id = f"api_trigger_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        # Trigger Airflow DAG
        response = requests.post(
            f"{AIRFLOW_URL}/dags/{DAG_ID}/dagRuns",
            auth=("airflow", "airflow"),
            json={
                "dag_run_id": dag_run_id,
                "conf": {"source": "knn-api"}
            },
            timeout=10
        )

        # Handle Airflow errors
        if response.status_code not in (200, 201):
            raise HTTPException(status_code=500, detail=response.text)

        # Successful trigger
        return {
            "status": "Pipeline triggered",
            "dag_run_id": dag_run_id
        }

    # Log and propagate errors
    except Exception as e:
        status_code = "500"
        logger.error(e)
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # Record request duration
        duration = time.time() - start_time
        api_request_duration_seconds.labels(
            "/etl/trigger", "POST", status_code
        ).observe(duration)

        api_request_total.labels(
            "/etl/trigger", "POST", status_code
        ).inc()

# Prometheus Metrics Endpoint
@router.get("/metrics")
def metrics():
    """
    Exposes Prometheus metrics for scraping.
    """
    return Response(generate_latest(), media_type="text/plain")
