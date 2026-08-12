"""Python API and static frontend for the BI dashboard."""

from __future__ import annotations

import os
from contextlib import contextmanager
from datetime import date
from decimal import Decimal
from pathlib import Path
from typing import Any

import psycopg
from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"
DEFAULT_SQL_PATH = Path("transformation/sql/analytics_models.sql")
DEFAULT_DATABASE_URL = "postgresql://mock_erp:mock_erp@localhost:55432/mock_erp"

DATABASE_URL = os.getenv("DASHBOARD_DATABASE_URL", DEFAULT_DATABASE_URL)
ANALYTICS_SQL_PATH = Path(os.getenv("ANALYTICS_SQL_PATH", str(DEFAULT_SQL_PATH)))

app = FastAPI(title="ERP Data Platform Dashboard")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


def json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, date):
        return value.isoformat()
    return value


@contextmanager
def connection_cursor():
    with psycopg.connect(DATABASE_URL) as connection:
        with connection.cursor() as cursor:
            yield connection, cursor


def fetch_all(cursor, sql: str) -> list[dict[str, Any]]:
    cursor.execute(sql)
    columns = [column.name for column in cursor.description]
    return [
        {column: json_value(value) for column, value in zip(columns, row)}
        for row in cursor.fetchall()
    ]


def fetch_one(cursor, sql: str) -> dict[str, Any]:
    rows = fetch_all(cursor, sql)
    return rows[0] if rows else {}


def refresh_analytics_models() -> None:
    sql = ANALYTICS_SQL_PATH.read_text(encoding="utf-8")
    with connection_cursor() as (connection, cursor):
        cursor.execute(sql)
        connection.commit()


def load_dashboard_payload() -> dict[str, Any]:
    refresh_analytics_models()

    with connection_cursor() as (_, cursor):
        return {
            "kpis": fetch_one(cursor, "SELECT * FROM analytics.mart_dashboard_kpis"),
            "daily_sales": fetch_all(
                cursor,
                """
                SELECT date_key, orders, net_revenue, units_sold, gross_margin
                FROM analytics.mart_daily_sales
                ORDER BY date_key
                """,
            ),
            "sales_by_channel": fetch_all(
                cursor,
                """
                SELECT channel_code, channel_name, channel_type, orders, net_revenue, units_sold, gross_margin
                FROM analytics.mart_sales_by_channel
                ORDER BY net_revenue DESC
                """,
            ),
            "top_products": fetch_all(
                cursor,
                """
                SELECT sku, product_name, category_name, units_sold, net_revenue, gross_margin
                FROM analytics.mart_top_products
                ORDER BY net_revenue DESC
                LIMIT 8
                """,
            ),
            "inventory_alerts": fetch_all(
                cursor,
                """
                SELECT warehouse_code, sku, product_name, available_qty, reorder_point,
                       avg_daily_sales_14d, days_of_inventory, stock_status, shelf_life_status
                FROM analytics.mart_inventory_alerts
                ORDER BY
                    CASE stock_status
                        WHEN 'OUT_OF_STOCK' THEN 1
                        WHEN 'REORDER' THEN 2
                        ELSE 3
                    END,
                    available_qty ASC
                LIMIT 10
                """,
            ),
            "logistics": fetch_all(
                cursor,
                """
                SELECT carrier_code, carrier_name, service_level, shipments,
                       avg_fulfillment_lead_days, avg_delivery_lead_days,
                       on_time_delivery_rate, shipping_fee
                FROM analytics.mart_logistics_performance
                ORDER BY shipments DESC
                """,
            ),
            "customers": fetch_all(
                cursor,
                """
                SELECT customer_code, customer_name, segment_name, last_order_date,
                       recency_days, frequency_orders, monetary_value, customer_status
                FROM analytics.mart_customer_rfm
                ORDER BY monetary_value DESC
                LIMIT 8
                """,
            ),
        }


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.post("/api/refresh")
def refresh() -> dict[str, str]:
    refresh_analytics_models()
    return {"status": "ok"}


@app.get("/api/dashboard")
def dashboard() -> dict[str, Any]:
    return load_dashboard_payload()


def main() -> None:
    import uvicorn

    host = os.getenv("DASHBOARD_HOST", "0.0.0.0")
    port = int(os.getenv("DASHBOARD_PORT", "8501"))
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
