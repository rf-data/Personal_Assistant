# Supply reviewed Python 3.12 and uv images by digest. No implicit image selection.
ARG PYTHON_IMAGE
ARG UV_IMAGE
FROM ${UV_IMAGE} AS uv
FROM ${PYTHON_IMAGE}
COPY --from=uv /uv /usr/local/bin/uv
WORKDIR /app
COPY deployment/runtime/pyproject.toml deployment/runtime/uv.lock /app/runtime/
ENV UV_PROJECT_ENVIRONMENT=/opt/venv UV_NO_CACHE=1 UV_PYTHON_DOWNLOADS=never
RUN uv sync --project /app/runtime --frozen --no-dev --no-install-project \
    && useradd --uid 10001 --create-home assistant
COPY src/ /app/src/
COPY scripts/deployment.py scripts/deployment_gate.py /app/scripts/
COPY scripts/cs50_material_quality.py /app/scripts/cs50_material_quality.py
COPY scripts/cs50_materials.py scripts/cs50_workflow.py scripts/cs50_batch.py scripts/cs50_worker.py /app/scripts/
ENV PATH=/opt/venv/bin:/usr/local/bin:/usr/bin:/bin \
    PYTHONNOUSERSITE=1 PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
USER 10001:10001
STOPSIGNAL SIGTERM
ENTRYPOINT ["python", "-m", "scripts.deployment"]
