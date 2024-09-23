FROM python:3.9-slim AS builder

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

RUN pip install poetry && poetry config virtualenvs.in-project true

WORKDIR "/app"
COPY . .

RUN poetry install
RUN poetry build

FROM python:3.9-slim

WORKDIR "/app"

COPY --from=builder /app/migrations ./migrations
COPY --from=builder /app/dist/*.whl .
RUN pip install *.whl

ENTRYPOINT ["hemera"]