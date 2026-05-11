##
# imports

from src.run_text_extraction import run_text_extraction
from 
# --- API Endpoints ---
# Health Check Endpoint
@app.get("/")
def root():
    return {"message": "FastAPI Trigger Active", 
            "status": "ok"}

            
@app.post("/extract_pdf")
async def extract_pdf(file_name: str,
                      folder: str,
                      config: dict):

    result = run_text_extraction(config, file_name, folder)

    return result
