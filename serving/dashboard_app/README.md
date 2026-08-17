# Analytics Dashboard App

This service provides a lightweight BI-style dashboard for the mock ERP data platform.

```text
mock_erp_pg operational tables
-> ingestion/custom_python pipeline
-> data_warehouse_pg
-> transformation/sql/analytics_models.sql
-> analytics.dim_* / analytics.fact_* / analytics.mart_*
-> Python API
-> frontend dashboard
```

## Run

Create the local environment file from the repository root and replace every `change-me` value:

```bash
cp .env.example .env
```

Create the shared Docker network if it does not exist:

```bash
docker network create end2end_data_network
```

Start the mock ERP PostgreSQL source first:

```bash
docker compose --env-file .env -f data_source/mock_erp_pg/docker-compose.mock_erp_pg.yml up -d --build
```

Start the analytics warehouse and pipeline:

```bash
docker compose --env-file .env -f storage/data_warehouse_pg/docker-compose.data_warehouse_pg.yml up -d
docker compose --env-file .env -f ingestion/custom_python/docker-compose.custom_python.yml up -d --build
```

The pipeline performs a full refresh every 30 seconds by default. It copies
the `erp_*` source schemas into `data_warehouse_pg`, builds the analytics
models there, and records the latest successful run in
`pipeline.pipeline_runs`.

Start the dashboard service:

```bash
docker compose --env-file .env -f serving/dashboard_app/docker-compose.dashboard_app.yml up -d --build
```

Open:

```text
http://localhost:8501
```

## Frontend

The dashboard frontend is built with React and Vite.

Run the React dev server:

```bash
cd serving/dashboard_app/frontend
npm install
npm run dev
```

The Vite dev server proxies `/api` requests to the FastAPI backend at `http://localhost:8501`.

Build the static frontend served by FastAPI:

```bash
cd serving/dashboard_app/frontend
npm run build
```

## API

```text
GET  /api/dashboard
```

`GET /api/dashboard` only reads the marts already produced in the analytics warehouse.
The dashboard API does not connect to the operational ERP database and does not run transformation SQL.
During first startup, the `pipeline` field may be empty briefly while the pipeline creates its first warehouse tables.

## Configuration

The dashboard reads the warehouse connection from either `DASHBOARD_DATABASE_URL` or these variables:

```text
WAREHOUSE_POSTGRES_USER
WAREHOUSE_POSTGRES_PASSWORD
WAREHOUSE_POSTGRES_DB
```

Keep the real values in the local `.env` file. The Docker Compose service constructs its internal connection URL without storing credentials in this document.

Override the external dashboard port:

```bash
DASHBOARD_EXTERNAL_PORT=8601 \
docker compose --env-file .env -f serving/dashboard_app/docker-compose.dashboard_app.yml up -d --build
```
