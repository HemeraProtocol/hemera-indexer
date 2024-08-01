FROM python:3.9-slim

LABEL org.opencontainers.image.title="Hemera Protocol"
LABEL org.opencontainers.image.created="$(date -u +'%Y-%m-%dT%H:%M:%SZ')"
LABEL org.opencontainers.image.source="https://github.com/HemeraProtocol/hemera-indexer"

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir .

ENV PYTHONPATH=/app:$PYTHONPATH

ENTRYPOINT ["hemera"]