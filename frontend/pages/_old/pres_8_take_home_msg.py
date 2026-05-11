import streamlit as st
from pathlib import Path

def show():
    st.header("📑 Take home message and future plans)")

    tabs = st.tabs(["Wrap-up", "Future plans"])

    with tabs[0]:
        st.subheader("Take home message")
        st.markdown("""
        
                        """)

    with tabs[1]:
        st.subheader("Future plans")
        st.markdown("""
        **Kubernetes**   
        - Orchestration of containerized services across multiple nodes   
        - Automated deployment, scaling, and lifecycle management of workloads   
        - Abstraction layer between application logic and underlying infrastructure

        **Optuna**   
        - Automated hyperparameter optimization using adaptive search strategies   
        - Efficient exploration of model configuration spaces   
        - Experiment tracking and comparison of optimization trials
                        """)
  