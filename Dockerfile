FROM python:3.9

WORKDIR /app
COPY . .
RUN ["pip", "install", "-e", "."]


CMD ["python", "hemera.py", "stream"]