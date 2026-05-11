import streamlit as st
from pathlib import Path

def show():
    st.header("🧪 MLflow")
    st.markdown("""   
    - Central tool for tracking ML experiments)   
    - Logs parameters, metrics, models, and artifacts  
    - Makes ML experiments reproducible and comparable
    """)
    img1 = Path("/workspaces/oct25_bmlops_int_rakuten/streamlit/src/screenshots/mlflow1.png")
    img2 = Path("/workspaces/oct25_bmlops_int_rakuten/streamlit/src/screenshots/mlflow2.png")
    st.image(str(img1), caption="MLflow Dashboard 1")
    st.image(str(img2), caption="MLflow Dashboard 2")