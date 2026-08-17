FROM python:3.12-slim

WORKDIR /app

COPY ingestion/custom_python/requirements.txt /tmp/pipeline_requirements.txt
RUN pip install --no-cache-dir -r /tmp/pipeline_requirements.txt

COPY shared /app/shared
COPY ingestion/custom_python /app/ingestion/custom_python
COPY transformation/sql /app/transformation/sql

CMD ["python", "-m", "ingestion.custom_python.pipeline_runner"]
