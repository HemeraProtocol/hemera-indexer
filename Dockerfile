FROM python:3.9-slim AS builder

WORKDIR /app
COPY . .

RUN pip install --no-cache-dir build && \
    python -m build --wheel --no-isolation

FROM python:3.9-slim

LABEL org.opencontainers.image.title="Hemera Protocol"
LABEL org.opencontainers.image.created="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
LABEL org.opencontainers.image.source="https://github.com/HemeraProtocol/hemera-indexer"

WORKDIR /app

COPY --from=builder /app/dist/*.whl .

RUN pip install --no-cache-dir *.whl && \
    rm *.whl

COPY hemera.py .

CMD ["python", "hemera.py", "stream"]
