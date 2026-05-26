from pathlib import Path

import streamlit as st


def show():
    st.header("🔌 FastAPI")
    st.subheader("General Purpose")
    st.markdown("""
    - Python framework for quickly building web APIs   
    - Lightweight HTTP interface   
    - Decouples UI from orchestration
    """)

    # Bsp.-Dateien für Testzwecke
    img_etl_trigger = Path(
        "/workspaces/oct25_bmlops_int_rakuten/streamlit/src/screenshots/etl_trigger.png"
    )
    img_training = Path(
        "/workspaces/oct25_bmlops_int_rakuten/streamlit/src/screenshots/training.png"
    )
    img_recos = Path(
        "/workspaces/oct25_bmlops_int_rakuten/streamlit/src/screenshots/recommend.png"
    )

    st.subheader("Endpoints")
    with st.expander("trigger 'etl-pipeline'"):
        with st.expander("ETL-trigger"):
            st.image(str(img_etl_trigger), caption="ETL-trigger")

        st.divider()

        with st.expander("Code"):
            st.markdown("""query: 'curl -X POST http://localhost:8001/etl/trigger' """)
            st.markdown(
                """answer: '{"status":"Pipeline triggered","dag_run_id":"api_trigger_20260109_145704"}' """
            )

    with st.expander("trigger 'create similarity matrix'"):
        with st.expander("training trigger"):
            st.image(str(img_training), caption="training trigger")

        st.divider()

        with st.expander("Code"):
            st.markdown(
                """query: 'curl -X POST http://localhost:8001/train/trigger' """
            )
            st.markdown(
                """answer: '{"status":"Training DAG triggered","dag_run_id":"api_trigger_train_20260109_152032"}' """
            )

    with st.expander("ask for recommendations"):
        with st.expander("recommendations"):
            st.image(str(img_recos), caption="recommendations")

        st.divider()

        with st.expander("Code"):
            st.markdown("""query: 'curl "http://localhost:8001/recommend/4293237" ' """)
            st.markdown("""answer:
             '{"productid":4293237,"recommendations":
             [4293237,3226779852,4180534759,1807806498,73334276,2255444083,278528834,46540267,4229642138,4187799604]}' """)
