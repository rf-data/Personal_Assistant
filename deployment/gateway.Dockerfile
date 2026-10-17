ARG PYTHON_IMAGE
ARG CADDY_IMAGE
FROM ${CADDY_IMAGE} AS caddy
FROM ${PYTHON_IMAGE}
COPY --from=caddy /usr/bin/caddy /usr/local/bin/caddy
COPY deployment/gateway_health.py /opt/gateway_health.py
RUN useradd --uid 10001 --create-home gateway
ENV XDG_CONFIG_HOME=/tmp/config XDG_DATA_HOME=/tmp/data PYTHONDONTWRITEBYTECODE=1
USER 10001:10001
STOPSIGNAL SIGTERM
ENTRYPOINT ["caddy"]
CMD ["run", "--config", "/etc/caddy/Caddyfile", "--adapter", "caddyfile"]
