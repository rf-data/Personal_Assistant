import streamlit as st


def show():
    st.header("📑 Conclusion")
    st.markdown("""
    #### What is the Status Quo of our project?
    """)

    size = st.slider("image size", min_value=500, max_value=5000, value=2500, step=100)
    # path_img_infra = "/workspaces/oct25_bmlops_int_rakuten/streamlit/src/screenshots/Infra_complete.png"
    # st.image(path_img_infra,
    #         caption="Overview infrastructure, made with Mermaid",
    #         width=size)

    with st.expander("**(1) Automated processes**"):
        st.markdown("""
        ✅ Pipelines and orchestration are available
        ✅ Can be triggered by API
        🟡 Adding a FileSensor or similar (--> increase automation)
        """)

    with st.expander("**(2) User interactions possible**"):
        st.markdown("""
        ✅ API endpoints 'etl_trigger', 'create SimMatrix' and 'recommendation' available
        🔴 Basic Auth or OAuth2 no yet implemented
        """)

    with st.expander("**(3) File and Data storage**"):
        st.markdown("""
        ✅ Product data: MongoDB
        ✅ Airflow: PostgreSQL
        🔜 MLflow: SQLite or PotsgreSQL possible
        🔜 use additional and more specialised/optimised DBs (e.g. SQL, vector DB)
        """)

    with st.expander("**(4) 'Best' Model available and ensured**"):
        st.markdown("""
        ✅ Suitable model at hand
        ✅ Tracked its building (**MLflow**)
        🟡 Model selection: also tried FAISS but not completed (*Facebook AI Similarity Search*)
        🔴 Model optimisation: try **Optuna**
        🔴 Selection and optimisation not semi-automated
        🔴 Adding further data on 'products' (unlabelled Rakuten set, AI generated) then agreement-filtered pseudo-labelling
        🔴 Adding AI generated data on 'customers', 'baskets' and/or 'orders'
        --> creating an hybrid-approach recommendation system
        """)

    with st.expander("**(5) Monitoring & Maintenance**"):
        st.markdown("""
        ✅ Prometheus, Node-exporter and Grafana are available and interconnected
        🟡 Loki: available but not yet fully configured and integrated
        🔜 centralised logging to faciliate debugging and troubleshooting
        🔜 connect to other tools, e.g. MLflow, Airflow
        """)

    with st.expander("**(6) Reliability**"):
        st.markdown("""
        - ci.yaml and milestone.yaml
        ✅ both: creation started
        ✅ ci: sucessfully triggered by 'pull_request'
        🟡 milestone: supposed to be triggered by change in tag 'version' (subversion: v1.1 --> v1.2)
        🟡 Debug status: not yet ready and unclear, respectively
        🟡 Unit Tests: more to be added
        🔴 pre-commit hooks: not yet started (i.e. black, flake8,..)
        - release
        🔴 not yet started
        🔴 supposed to be triggered by change in tag 'version' (version: v1.* --> v2.0)
    """)

    with st.expander("**(7) Availability, Portability and Scalability**"):
        st.markdown("""
        - Docker
        ✅ all tools dockerized so far
        ✅ Compose and decompose w/o errors
        ✅ Makefile: semi-automated processes and SAME network ensured
        ✅ Docker-compose + Dockerfile: ensures portability and scalability
        🔜 Better overview: use 'Portainer'or 'ContainerTools' (VSCode extension, see below)
        - Kubernetes
        🔴 not yet started
        - Terraform (i.e. IaC wrt EC2, subnets, security groups, routing tables, NAT-/IGW,...)
        🔴 not yet started
        - Amazon Machine Image (AMI):
        🟡 MLOps base image available, additional AMIs possible as backup or when production ready (--> autoscaling)
        - Grafana
        ✅ dashboards: DataViz and Monitoring as IaC
        - ZenML
        🔜 figure out if reasonable to use
    """)

    with st.popover("ℹ️ **Container Tools**"):
        ct_path = "/workspaces/oct25_bmlops_int_rakuten/streamlit/src/screenshots/ContainerTools.png"
        st.image(ct_path)

    with st.popover("ℹ️  **'Kubernetes'** and **'Optuna'**"):
        st.markdown("""
        **What is the use of 'Kubernetes'?**
        - Orchestration of containerized services across multiple nodes
        - Automated deployment, scaling, and lifecycle management of workloads
        - Abstraction layer between application logic and underlying infrastructure

        **What is the use of 'Optuna'?**
        - Automated hyperparameter optimization using adaptive search strategies
        - Efficient exploration of model configuration spaces
        - Experiment tracking and comparison of optimization trials

        """)

    with st.expander("ℹ️ AMI 'MLOps base'"):
        st.markdown("""
        #### AMI 'MLOps base'

This project uses a **custom AWS AMI** as a reproducible base for an MLOps environment.
The AMI provides a clean, Docker-enabled Ubuntu system, while all application-level
services are deployed using Docker Compose.

---

## Base Image Overview

The base AMI includes:
- Ubuntu 22.04 LTS
- Docker Engine + Docker Compose plugin
- Git
- tmux incl. code server (semi-automated setup)
- AWS SSM-based access (no SSH required)
- Local development via code-server (VS Code in browser, accessed through SSM port forwarding)

The AMI is intentionally kept **lightweight** and does **not** include any running services.
All MLOps components are deployed on top of this base image by pulling a GitHub repository.

---

## Architecture Philosophy
- **AMI** → Operating system & tooling baseline
- **Docker Compose** → Runtime services (monitoring, training, orchestration)
- **No services baked into the AMI**
- **No secrets stored in the image**

This separation ensures:
- reproducibility
- flexibility
- easy recovery by re-launching instances from the AMI

---

## Instance Access

Access is handled exclusively via **AWS Systems Manager (SSM)**.

Example port forwarding for local development:

```bash
aws ssm start-session \
  --target <instance-id> \
  --document-name AWS-StartPortForwardingSession \
  --parameters '{"portNumber":["8443"],"localPortNumber":["8443"]}'

        """)
