"""Centralized System Parameters & Settings for End-to-End Data Platform.

Loads environment variables, validates system parameters, and provides
strongly-typed configuration objects and connection string builders.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class ConfigurationError(ValueError):
    """Raised when a required system parameter or secret is missing or invalid."""

    pass


@dataclass(frozen=True)
class PostgresSettings:
    """System parameters for a PostgreSQL database instance."""

    user: str
    password: str
    database: str
    host: str
    port: int
    custom_url: Optional[str] = None

    @classmethod
    def from_env(
        cls,
        prefix: str,
        default_host: str = "localhost",
        default_port: int = 5432,
        url_env_override: Optional[str] = None,
    ) -> PostgresSettings:
        url = os.getenv(url_env_override) if url_env_override else None
        if url:
            return cls(
                user="",
                password="",
                database="",
                host="",
                port=default_port,
                custom_url=url,
            )

        user = os.getenv(f"{prefix}_USER")
        password = os.getenv(f"{prefix}_PASSWORD")
        database = os.getenv(f"{prefix}_DB") or os.getenv(f"{prefix}_NAME")
        host = os.getenv(f"{prefix}_HOST", default_host)
        port_str = os.getenv(f"{prefix}_PORT") or os.getenv(f"{prefix}_EXTERNAL_PORT")
        port = int(port_str) if port_str else default_port

        if not (user and password and database):
            missing = []
            if not user:
                missing.append(f"{prefix}_USER")
            if not password:
                missing.append(f"{prefix}_PASSWORD")
            if not database:
                missing.append(f"{prefix}_DB / {prefix}_NAME")
            raise ConfigurationError(
                f"Missing required system parameters for {prefix}: {', '.join(missing)}"
            )

        return cls(
            user=user,
            password=password,
            database=database,
            host=host,
            port=port,
        )

    def get_connection_url(
        self,
        default_host_override: Optional[str] = None,
        default_port_override: Optional[int] = None,
    ) -> str:
        if self.custom_url:
            return self.custom_url
        host = default_host_override or self.host
        port = default_port_override or self.port
        return f"postgresql://{self.user}:{self.password}@{host}:{port}/{self.database}"


@dataclass(frozen=True)
class MinioSettings:
    """System parameters for MinIO Object Storage."""

    user: str
    password: str
    host: str
    port: int

    @classmethod
    def from_env(cls) -> MinioSettings:
        user = os.getenv("MINIO_ROOT_USER")
        password = os.getenv("MINIO_ROOT_PASSWORD")
        host = os.getenv("MINIO_HOST", "minio1")
        port = int(os.getenv("MINIO_PORT") or os.getenv("MINIO_API_EXTERNAL_PORT") or "9000")

        missing = []
        if not user:
            missing.append("MINIO_ROOT_USER")
        if not password:
            missing.append("MINIO_ROOT_PASSWORD")

        if missing:
            raise ConfigurationError(
                f"Missing required system parameters for MinIO: {', '.join(missing)}"
            )

        return cls(user=user, password=password, host=host, port=port)

    @property
    def endpoint_url(self) -> str:
        return f"http://{self.host}:{self.port}"


@dataclass(frozen=True)
class PipelineSettings:
    """System parameters for custom Python ETL pipelines."""

    analytics_sql_path: Path
    interval_seconds: int
    startup_retry_seconds: int

    @classmethod
    def from_env(cls) -> PipelineSettings:
        sql_path = Path(
            os.getenv("PIPELINE_ANALYTICS_SQL_PATH", "transformation/sql/analytics_models.sql")
        )
        interval = int(os.getenv("PIPELINE_INTERVAL_SECONDS", "30"))
        retry = int(os.getenv("PIPELINE_STARTUP_RETRY_SECONDS", "5"))
        return cls(
            analytics_sql_path=sql_path,
            interval_seconds=interval,
            startup_retry_seconds=retry,
        )


@dataclass(frozen=True)
class DashboardServerSettings:
    """System parameters for the Dashboard API / Web server."""

    host: str
    port: int

    @classmethod
    def from_env(cls) -> DashboardServerSettings:
        host = os.getenv("DASHBOARD_HOST", "0.0.0.0")
        port = int(os.getenv("DASHBOARD_PORT") or os.getenv("DASHBOARD_EXTERNAL_PORT") or "8501")
        return cls(host=host, port=port)


@dataclass(frozen=True)
class ProducerSettings:
    """System parameters for the Mock Transaction Data Producer."""

    target: str
    database_url: Optional[str]
    interval_seconds: float
    days_per_batch: int
    max_batches: Optional[int]

    @classmethod
    def from_env(cls) -> ProducerSettings:
        target = os.getenv("MOCK_DATA_PRODUCER_TARGET", "mock_erp_pg")
        database_url = os.getenv("MOCK_DATA_PRODUCER_DATABASE_URL")
        interval = float(os.getenv("MOCK_DATA_PRODUCER_INTERVAL_SECONDS", "10"))
        days = int(os.getenv("MOCK_DATA_PRODUCER_DAYS_PER_BATCH", "1"))
        max_b_str = os.getenv("MOCK_DATA_PRODUCER_MAX_BATCHES")
        max_b = int(max_b_str) if max_b_str and max_b_str.strip() else None
        return cls(
            target=target,
            database_url=database_url,
            interval_seconds=interval,
            days_per_batch=days,
            max_batches=max_b,
        )


class SystemSettings:
    """Central registry of all system parameters across platform services."""

    @property
    def mock_erp_db(self) -> PostgresSettings:
        return PostgresSettings.from_env(
            prefix="MOCK_ERP_POSTGRES",
            default_host="localhost",
            default_port=55432,
            url_env_override="PIPELINE_SOURCE_DATABASE_URL",
        )

    @property
    def warehouse_db(self) -> PostgresSettings:
        return PostgresSettings.from_env(
            prefix="WAREHOUSE_POSTGRES",
            default_host="localhost",
            default_port=55433,
            url_env_override="PIPELINE_WAREHOUSE_DATABASE_URL",
        )

    @property
    def dashboard_db(self) -> PostgresSettings:
        return PostgresSettings.from_env(
            prefix="WAREHOUSE_POSTGRES",
            default_host="localhost",
            default_port=55433,
            url_env_override="DASHBOARD_DATABASE_URL",
        )

    @property
    def airflow_db(self) -> PostgresSettings:
        return PostgresSettings.from_env(
            prefix="AIRFLOW_DB",
            default_host="af_db",
            default_port=5432,
        )

    @property
    def odoo_db(self) -> PostgresSettings:
        return PostgresSettings.from_env(
            prefix="ODOO_DB",
            default_host="db",
            default_port=5432,
        )

    @property
    def minio(self) -> MinioSettings:
        return MinioSettings.from_env()

    @property
    def pipeline(self) -> PipelineSettings:
        return PipelineSettings.from_env()

    @property
    def dashboard_server(self) -> DashboardServerSettings:
        return DashboardServerSettings.from_env()

    @property
    def producer(self) -> ProducerSettings:
        return ProducerSettings.from_env()


settings = SystemSettings()
