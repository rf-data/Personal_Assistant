FROM python:3.11-slim

WORKDIR /app

COPY streamlit/requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY streamlit/ /app/

CMD ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
