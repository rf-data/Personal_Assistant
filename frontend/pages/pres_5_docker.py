import streamlit as st
from pathlib import Path

# from src.utils import live_command_demo

make_extract = Path("/workspaces/oct25_bmlops_int_rakuten/streamlit/src/makefile_extract.md").read_text(encoding="utf-8")

docker_compose_api = Path("/workspaces/oct25_bmlops_int_rakuten/docker-compose.api.yaml").read_text(encoding="utf-8")
docker_file_api = Path("/workspaces/oct25_bmlops_int_rakuten/fastapi/Dockerfile").read_text(encoding="utf-8")
docker_airflow = Path("/workspaces/oct25_bmlops_int_rakuten/docker-compose.airflow.yaml").read_text(encoding="utf-8")
docker_monitoring = Path("/workspaces/oct25_bmlops_int_rakuten/docker-compose.monitoring.yaml").read_text(encoding="utf-8")
docker_compose_ml = Path("/workspaces/oct25_bmlops_int_rakuten/docker-compose.ml.yaml").read_text(encoding="utf-8")
docker_file_ml = Path("/workspaces/oct25_bmlops_int_rakuten/mlflow/Dockerfile").read_text(encoding="utf-8")

def show():
    st.header("📦 Docker and microservice architecture")
    st.markdown("""
    **What is the use of 'Docker'?**   
    - Containerized execution of services and applications   
    - Reproducible runtime environments across development and deployment   
    - Isolation of dependencies for API, UI, and other infrastructure components
    - Allows a microservice architecture and portability (**DockerHub**)

    --- 

    **How we used Docker?**
    - one docker-compose.yaml per 'microservice' and a Dockerfile if necessary   
    """)
   
    with st.expander("Docker-composes and Dockerfiles"):
        # col1, col2, col3, col4 = st.columns(4, border=True)

        with st.container(border=True):
            st.markdown("""
            **Docker 'Airflow'** covers:   
            - Airflow (incl. init, scheduler, webserver)   
            - PostgreSQL  
            """)
            
            with st.popover("ℹ️ **docker-compose.airflow.yaml**"):
                st.code(docker_airflow, language="python")


        with st.container(border=True):
            st.markdown("""
            **Docker 'APIs'** covers:   
            - FastAPI   
            - Streamlit  
            """)
            
            with st.popover("ℹ️ **docker-compose.api.yaml**"):
                st.code(docker_compose_api, language="python")
            
            with st.popover("ℹ️ **Dockerfile (API)**"):
                st.code(docker_file_api, language="python")
        
        with st.container(border=True):
            st.markdown("""
            **Docker 'ML'** covers:   
            - MLflow,   
            - SQLite/PostgreSQL if necessary,   
            - prospectively, W&B or similar 
            
            """)
            with st.popover("ℹ️ **docker-compose.ml.yaml**"):
                st.code(docker_compose_ml, language="python")
            
            with st.popover("ℹ️ **Dockerfile (MLflow)**"):
                st.code(docker_file_ml, language="python")
        
        with st.container(border=True):
            st.markdown("""
            **Docker 'Monitoring'** covers:   
            - Prometheus   
            - Grafana   
            - Node-explorer   
            - Promtail (*not yet fully integrated*)   
            - Loki (*not yet fully integrated*)
            
            """)
            with st.popover("ℹ️ **docker-compose.monitoring.yaml**"):
                st.code(docker_monitoring, language="python")
    
    st.markdown("""
    - automation by using Makefile   
    **-->** same project by default --> no network mismatches possible

    """)
    with st.popover("ℹ️ Extract from **Makefile**", width="stretch"):
        st.code(make_extract, language="python")

    st.markdown("""
    ---

    **⚡ Live Demos**
    """)

    LOGS = Path("/workspaces/oct25_bmlops_int_rakuten/streamlit/logs")
    LOGS.mkdir(parents=True, exist_ok=True)
    
    log_ml = LOGS / "build_ml"
    log_monitoring = LOGS / "build_monitoring"
    log_docker = LOGS / "docker_status"

    if "monitoring_running" not in st.session_state:
        st.session_state.monitoring_running = False
    
    top_left, top_middle, top_right = st.columns(3)
    bottom_left, bottom_middle, bottom_right = st.columns(3)

    status = st.status("Please, choose a button to build Docker containers...", 
                        state="complete",
                        expanded=True)

    # ------------
    # TOP ROW  
    # ------------ 
    # top right
    options_dict = {
        "append": "a",
        "write": "w"
    }
    sel = top_right.pills(
        "file edit mode",
        options = options_dict.keys(),
        selection_mode="single",
        default="append"
    )

    file_mode = options_dict[sel]

    if top_left.button(
                "build MLflow", 
                width="stretch", 
                key="ml",
                ): 

        cmd = ["make", "ml_docker"]

        status.update(label="Running MLflow build...", state="running")


        exit_code = live_command_demo(cmd, log_ml, mode=file_mode)

        if exit_code == 0:
            status.update(
                label="Building MLflow containers finished successfully.", 
                state="complete",
                expanded=False
                )
        else:
            status.update(
                label=f"Building MLflow containers failed (exit code {exit_code}).", 
                state="error",
                expanded=True,
                )
            st.error(f"Building MLflow containers failed (exit code {exit_code}).")

    if top_middle.button(
                    "build monitoring", 
                    width="stretch", 
                    key="monitoring",
                    ): 

        cmd = ["make", "monitoring_docker"]

        status.update(label="Running monitoring build...", state="running")
        exit_code = live_command_demo(cmd, log_monitoring, mode=file_mode)

        if exit_code == 0:
            status.update(
                label="Building monitoring containers finished successfully.", 
                state="complete",
                expanded=False
                )
        else:
            status.update(
                label=f"Building monitoring containers failed (exit code {exit_code}).", 
                state="error",
                expanded=True,
                )

        st.session_state.monitoring_running = True

    # ------------
    # BOTTOM ROW  
    # ------------ 
    if bottom_left.button(
                "remove MLflow", 
                width="stretch", 
                key="ml_remove",
                ): 

        cmd = ["make", "ml_stop"]

        status.update(label="Running MLflow removal...", state="running")

        exit_code = live_command_demo(cmd, log_ml, mode=file_mode)

        if exit_code == 0:
            status.update(
                label="Removing AMLflow containers finished successfully.", 
                state="complete",
                expanded=False
                )

        else:
            status.update(
                label=f"Removing MLflow containers failed (exit code {exit_code}).", 
                state="error",
                expanded=True,
                )

    if bottom_middle.button(
                    "remove monitoring", 
                    width="stretch", 
                    key="monitoring_remove",
                    ):

        cmd = ["make", "monitoring_stop"]

        status.update(label="Running monitoring removal...", state="running")
        exit_code = live_command_demo(cmd, log_monitoring, mode=file_mode)

        if exit_code == 0:
            status.update(
                label="Removing monitoring containers finished successfully.", 
                state="complete",
                expanded=False
                )
        else:
            status.update(
                label=f"Removing monitoring containers failed (exit code {exit_code}).", 
                state="error",
                expanded=True,
                )

        st.session_state.monitoring_running = False

    if bottom_right.button(
                        "docker check",
                        width="stretch",
                        key="docker_check"
                    ):

        cmd = ["docker", "ps", "-a"]

        status.update(label="Checking status of contaner, volumes, network,...", state="running")
        exit_code = live_command_demo(cmd, log_docker, mode=file_mode)

        if exit_code == 0:
            status.update(
                label="Docker status check completed.", 
                state="complete",
                expanded=False
                )
        else:
            status.update(
                label=f"Checking docker status failed (exit code {exit_code}).", 
                state="error",
                expanded=True,
                )
