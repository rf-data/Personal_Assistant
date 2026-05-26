##
# imports
import os
import shutil
from pathlib import Path

from fastapi import FastAPI

from src.core.memory import session
from src.run_text_extraction import run_text_extraction
from src.utils.general_helper import load_env_vars

# --- FastAPI App Initialization ---
app = FastAPI()

load_env_vars(name=".env.frontend")

FILE_FOLDER = Path(os.getenv("FOLDER_FILES"))

# --- Logging Configuration ---
# logging.basicConfig(level=logging.DEBUG)

logger = session.logger  # logging.getLogger("API_demo")


# --- API Endpoints ---
# Health Check Endpoint
@app.get("/")
def root():
    return {"message": "FastAPI Trigger Active", "status": "ok"}


@app.post("/extract_pdf")
async def extract_pdf(data: dict) -> dict:
    file_name = data["file_name"]
    folder = data["folder"]
    config = data["config"]

    result_path = run_text_extraction(config, file_name, folder)

    shutil.move(src=f"{folder}/{file_name}", dst=f"{FILE_FOLDER}/{file_name}")

    return {"status": "success", "result_path": result_path}
