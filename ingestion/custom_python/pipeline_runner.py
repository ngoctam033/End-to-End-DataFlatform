"""Small full-refresh pipeline for the learning environment.

The job extracts the ERP schemas from the operational PostgreSQL database,
loads them into the analytics warehouse, and builds the analytics models
there. The dashboard never executes transformation SQL; it only reads the
warehouse marts produced by this job.
"""

from __future__ import annotations

import os
import time
from contextlib import closing
from pathlib import Path

import psycopg
from psycopg import sql


# Configuration guide: docs/operations/secrets_management.md
from shared.settings import settings


def get_source_database_url() -> str:
    return settings.mock_erp_db.get_connection_url()


def get_warehouse_database_url() -> str:
    return settings.warehouse_db.get_connection_url()


ANALYTICS_SQL_PATH = settings.pipeline.analytics_sql_path
PIPELINE_INTERVAL_SECONDS = settings.pipeline.interval_seconds
STARTUP_RETRY_SECONDS = settings.pipeline.startup_retry_seconds
SOURCE_SCHEMAS = ("erp_core", "erp_sales", "erp_inventory", "erp_logistics", "erp_finance")


def quote_identifier(identifier: str) -> sql.Identifier:
    return sql.Identifier(identifier)


def source_tables(source_cursor) -> list[tuple[str, str]]:
    source_cursor.execute(
        """
        SELECT table_schema, table_name
        FROM information_schema.tables
        WHERE table_schema = ANY(%s)
          AND table_type = 'BASE TABLE'
        ORDER BY table_schema, table_name
        """,
        (list(SOURCE_SCHEMAS),),
    )
    return [(schema, table) for schema, table in source_cursor.fetchall()]


def table_columns(source_cursor, schema: str, table: str) -> list[tuple[str, str, bool]]:
    source_cursor.execute(
        """
        SELECT a.attname,
               pg_catalog.format_type(a.atttypid, a.atttypmod),
               a.attnotnull
        FROM pg_catalog.pg_attribute a
        JOIN pg_catalog.pg_class c ON c.oid = a.attrelid
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = %s
          AND c.relname = %s
          AND a.attnum > 0
          AND NOT a.attisdropped
        ORDER BY a.attnum
        """,
        (schema, table),
    )
    return source_cursor.fetchall()


def copy_table(source_connection, warehouse_connection, schema: str, table: str) -> None:
    with source_connection.cursor() as source_cursor, warehouse_connection.cursor() as warehouse_cursor:
        columns = table_columns(source_cursor, schema, table)
        column_definition = sql.SQL(", ").join(
            sql.SQL("{}").format(quote_identifier(name))
            + sql.SQL(" {}{}").format(sql.SQL(data_type), sql.SQL(" NOT NULL") if notnull else sql.SQL(""))
            for name, data_type, notnull in columns
        )
        warehouse_cursor.execute(
            sql.SQL("CREATE SCHEMA IF NOT EXISTS {};").format(quote_identifier(schema))
        )
        warehouse_cursor.execute(
            sql.SQL("DROP TABLE IF EXISTS {}.{};").format(
                quote_identifier(schema), quote_identifier(table)
            )
        )
        warehouse_cursor.execute(
            sql.SQL("CREATE TABLE {}.{} ({});").format(
                quote_identifier(schema), quote_identifier(table), column_definition
            )
        )

        source_cursor.execute(
            sql.SQL("SELECT {} FROM {}.{};").format(
                sql.SQL(", ").join(quote_identifier(name) for name, _, _ in columns),
                quote_identifier(schema),
                quote_identifier(table),
            )
        )
        insert_statement = sql.SQL("INSERT INTO {}.{} ({}) VALUES ({})").format(
            quote_identifier(schema),
            quote_identifier(table),
            sql.SQL(", ").join(quote_identifier(name) for name, _, _ in columns),
            sql.SQL(", ").join(sql.Placeholder() for _ in columns),
        )
        while rows := source_cursor.fetchmany(1000):
            warehouse_cursor.executemany(insert_statement, rows)


def record_pipeline_run(warehouse_connection, copied_tables: int) -> None:
    with warehouse_connection.cursor() as cursor:
        cursor.execute("CREATE SCHEMA IF NOT EXISTS pipeline")
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS pipeline.pipeline_runs (
                pipeline_name TEXT PRIMARY KEY,
                status TEXT NOT NULL,
                source_system TEXT NOT NULL,
                completed_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                copied_tables INTEGER NOT NULL
            )
            """
        )
        cursor.execute(
            """
            INSERT INTO pipeline.pipeline_runs
                (pipeline_name, status, source_system, completed_at, copied_tables)
            VALUES ('erp_to_analytics_warehouse', 'SUCCESS', 'mock_erp_pg', CURRENT_TIMESTAMP, %s)
            ON CONFLICT (pipeline_name) DO UPDATE SET
                status = EXCLUDED.status,
                source_system = EXCLUDED.source_system,
                completed_at = EXCLUDED.completed_at,
                copied_tables = EXCLUDED.copied_tables
            """,
            (copied_tables,),
        )


def run_once() -> int:
    source_url = get_source_database_url()
    warehouse_url = get_warehouse_database_url()
    with closing(psycopg.connect(source_url)) as source_connection:
        with closing(psycopg.connect(warehouse_url)) as warehouse_connection:
            with source_connection.cursor() as cursor:
                tables = source_tables(cursor)
            copied_tables = 0
            for schema, table in tables:
                copy_table(source_connection, warehouse_connection, schema, table)
                copied_tables += 1

            analytics_sql = ANALYTICS_SQL_PATH.read_text(encoding="utf-8")
            with warehouse_connection.cursor() as cursor:
                cursor.execute(analytics_sql)
            record_pipeline_run(warehouse_connection, copied_tables)
            warehouse_connection.commit()
            return copied_tables


def main() -> None:
    while True:
        try:
            copied_tables = run_once()
            print(f"Pipeline completed: copied {copied_tables} tables", flush=True)
        except Exception as error:  # keep the learning pipeline alive while dependencies start
            print(f"Pipeline waiting for dependencies: {error}", flush=True)
            time.sleep(STARTUP_RETRY_SECONDS)
            continue
        time.sleep(PIPELINE_INTERVAL_SECONDS)


if __name__ == "__main__":
    main()
