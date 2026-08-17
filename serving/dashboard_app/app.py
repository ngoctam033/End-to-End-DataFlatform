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

# Configuration guide: docs/operations/secrets_management.md
from shared.settings import settings

APP_DIR = Path(__file__).resolve().parent
STATIC_DIR = APP_DIR / "static"

def get_dashboard_database_url() -> str:
    return settings.dashboard_db.get_connection_url()


app = FastAPI(title="ERP Data Platform Dashboard")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")
app.mount("/assets", StaticFiles(directory=STATIC_DIR / "assets"), name="assets")


def json_value(value: Any) -> Any:
    if isinstance(value, Decimal):
        return float(value)
    if isinstance(value, date):
        return value.isoformat()
    return value


@contextmanager
def connection_cursor():
    with psycopg.connect(get_dashboard_database_url()) as connection:
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


def load_dashboard_payload() -> dict[str, Any]:
    with connection_cursor() as (_, cursor):
        cursor.execute("SELECT to_regclass('pipeline.pipeline_runs') IS NOT NULL")
        pipeline_table_exists = cursor.fetchone()[0]
        pipeline = (
            fetch_one(
                cursor,
                """
                SELECT pipeline_name, status, source_system, completed_at, copied_tables
                FROM pipeline.pipeline_runs
                ORDER BY completed_at DESC
                LIMIT 1
                """,
            )
            if pipeline_table_exists
            else {}
        )
        return {
            "data_source": "analytics_warehouse",
            "pipeline": pipeline,
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


@app.get("/api/dashboard")
def dashboard() -> dict[str, Any]:
    return load_dashboard_payload()


def main() -> None:
    import uvicorn

    host = settings.dashboard_server.host
    port = settings.dashboard_server.port
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
