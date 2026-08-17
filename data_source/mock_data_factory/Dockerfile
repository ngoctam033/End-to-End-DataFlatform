FROM python:3.12-slim

WORKDIR /app

COPY data_source/mock_data_factory/requirements.txt /tmp/mock_data_factory_requirements.txt
RUN pip install --no-cache-dir -r /tmp/mock_data_factory_requirements.txt

COPY shared /app/shared
COPY data_source /app/data_source

CMD ["python", "-m", "data_source.mock_data_factory.producer"]
