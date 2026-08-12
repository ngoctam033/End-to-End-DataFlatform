# Analytics Dashboard App

This service provides a lightweight BI-style dashboard for the mock ERP data platform.

```text
mock_erp_pg operational tables
-> transformation/sql/analytics_models.sql
-> analytics.dim_* / analytics.fact_* / analytics.mart_*
-> Python API
-> frontend dashboard
```

## Run

From `data_source/mock_erp_pg`:

```bash
docker compose -f docker-compose.mock_erp_pg.yml up -d --build
```

Open:

```text
http://localhost:8501
```

## API

```text
GET  /api/dashboard
POST /api/refresh
```

`GET /api/dashboard` refreshes the SQL analytical models before returning dashboard data.
