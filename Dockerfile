# Build stage
FROM python:3.9-slim as builder

WORKDIR /app

COPY pyproject.toml .
COPY README.md .
COPY src ./src

RUN pip install --no-cache-dir build && \
    python -m build

# Final stage
FROM python:3.9-slim

LABEL org.opencontainers.image.title="Hemera Protocol"
LABEL org.opencontainers.image.created="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
LABEL org.opencontainers.image.source="https://github.com/HemeraProtocol/hemera-indexer"

WORKDIR /app

COPY --from=builder /app/dist/*.whl .

RUN pip install --no-cache-dir *.whl && \
    rm *.whl

ENV PYTHONPATH=/app:$PYTHONPATH

ENTRYPOINT ["hemera"]