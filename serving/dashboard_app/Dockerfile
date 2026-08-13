FROM node:20-slim AS frontend

WORKDIR /app

COPY serving/dashboard_app/frontend/package*.json /app/serving/dashboard_app/frontend/
WORKDIR /app/serving/dashboard_app/frontend
RUN npm ci

COPY serving/dashboard_app/frontend /app/serving/dashboard_app/frontend
RUN npm run build

FROM python:3.12-slim

WORKDIR /app

COPY serving/dashboard_app/requirements.txt /tmp/dashboard_requirements.txt
RUN pip install --no-cache-dir -r /tmp/dashboard_requirements.txt

COPY serving/dashboard_app /app/serving/dashboard_app
COPY --from=frontend /app/serving/dashboard_app/static /app/serving/dashboard_app/static
COPY transformation/sql /app/transformation/sql

ENV DASHBOARD_HOST=0.0.0.0
ENV DASHBOARD_PORT=8501

CMD ["python", "-m", "serving.dashboard_app.app"]
