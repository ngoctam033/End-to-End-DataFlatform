FROM python:3.12-slim

WORKDIR /app

COPY serving/dashboard_app/requirements.txt /tmp/dashboard_requirements.txt
RUN pip install --no-cache-dir -r /tmp/dashboard_requirements.txt

COPY serving/dashboard_app /app/serving/dashboard_app
COPY transformation/sql /app/transformation/sql

ENV DASHBOARD_HOST=0.0.0.0
ENV DASHBOARD_PORT=8501

CMD ["python", "-m", "serving.dashboard_app.app"]
