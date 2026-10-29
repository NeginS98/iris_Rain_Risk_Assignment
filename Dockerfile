FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY iris_rain ./iris_rain
COPY tests ./tests
COPY config.example.yaml ./config.yaml
ENTRYPOINT ["python", "-m", "iris_rain.cli"]
