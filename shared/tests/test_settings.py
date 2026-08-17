from __future__ import annotations

import os
import unittest
from unittest.mock import patch

from shared.settings import ConfigurationError
from shared.settings import DashboardServerSettings
from shared.settings import MinioSettings
from shared.settings import PostgresSettings
from shared.settings import ProducerSettings
from shared.settings import PipelineSettings
# Configuration guide: docs/operations/secrets_management.md
from shared.settings import settings


class PostgresSettingsTest(unittest.TestCase):
    def test_from_env_reads_connection_parameters(self) -> None:
        with patch.dict(
            os.environ,
            {
                "TEST_DB_USER": "warehouse_user",
                "TEST_DB_PASSWORD": "warehouse_password",
                "TEST_DB_NAME": "warehouse",
                "TEST_DB_HOST": "warehouse-db",
                "TEST_DB_PORT": "55433",
            },
            clear=True,
        ):
            postgres = PostgresSettings.from_env("TEST_DB")

        self.assertEqual(postgres.user, "warehouse_user")
        self.assertEqual(postgres.password, "warehouse_password")
        self.assertEqual(postgres.database, "warehouse")
        self.assertEqual(postgres.host, "warehouse-db")
        self.assertEqual(postgres.port, 55433)
        self.assertEqual(
            postgres.get_connection_url(),
            "postgresql://warehouse_user:warehouse_password@warehouse-db:55433/warehouse",
        )

    def test_from_env_accepts_name_alias_for_database(self) -> None:
        with patch.dict(
            os.environ,
            {
                "TEST_DB_USER": "user",
                "TEST_DB_PASSWORD": "password",
                "TEST_DB_NAME": "database",
            },
            clear=True,
        ):
            postgres = PostgresSettings.from_env("TEST_DB")

        self.assertEqual(postgres.database, "database")

    def test_from_env_rejects_missing_required_parameters(self) -> None:
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaisesRegex(ConfigurationError, "TEST_DB_USER"):
                PostgresSettings.from_env("TEST_DB")

    def test_url_override_is_used_without_requiring_split_parameters(self) -> None:
        with patch.dict(
            os.environ,
            {"TEST_DATABASE_URL": "postgresql://user:password@db:5432/app"},
            clear=True,
        ):
            postgres = PostgresSettings.from_env(
                "TEST_DB",
                url_env_override="TEST_DATABASE_URL",
            )

        self.assertEqual(
            postgres.get_connection_url(),
            "postgresql://user:password@db:5432/app",
        )


class MinioSettingsTest(unittest.TestCase):
    def test_from_env_reads_credentials_and_builds_endpoint(self) -> None:
        with patch.dict(
            os.environ,
            {
                "MINIO_ROOT_USER": "minio_user",
                "MINIO_ROOT_PASSWORD": "minio_password",
                "MINIO_HOST": "minio",
                "MINIO_PORT": "9000",
            },
            clear=True,
        ):
            minio = MinioSettings.from_env()

        self.assertEqual(minio.user, "minio_user")
        self.assertEqual(minio.password, "minio_password")
        self.assertEqual(minio.endpoint_url, "http://minio:9000")

    def test_from_env_rejects_missing_password(self) -> None:
        with patch.dict(os.environ, {"MINIO_ROOT_USER": "minio_user"}, clear=True):
            with self.assertRaisesRegex(ConfigurationError, "MINIO_ROOT_PASSWORD"):
                MinioSettings.from_env()


class ApplicationSettingsTest(unittest.TestCase):
    def test_pipeline_dashboard_and_producer_settings_read_environment(self) -> None:
        with patch.dict(
            os.environ,
            {
                "PIPELINE_ANALYTICS_SQL_PATH": "/app/models.sql",
                "PIPELINE_INTERVAL_SECONDS": "45",
                "PIPELINE_STARTUP_RETRY_SECONDS": "7",
                "DASHBOARD_HOST": "127.0.0.1",
                "DASHBOARD_PORT": "8510",
                "MOCK_DATA_PRODUCER_TARGET": "mock_erp_pg",
                "MOCK_DATA_PRODUCER_INTERVAL_SECONDS": "2.5",
                "MOCK_DATA_PRODUCER_DAYS_PER_BATCH": "3",
                "MOCK_DATA_PRODUCER_MAX_BATCHES": "4",
            },
            clear=True,
        ):
            pipeline = PipelineSettings.from_env()
            dashboard = DashboardServerSettings.from_env()
            producer = ProducerSettings.from_env()

        self.assertEqual(str(pipeline.analytics_sql_path), "/app/models.sql")
        self.assertEqual(pipeline.interval_seconds, 45)
        self.assertEqual(pipeline.startup_retry_seconds, 7)
        self.assertEqual(dashboard.host, "127.0.0.1")
        self.assertEqual(dashboard.port, 8510)
        self.assertEqual(producer.target, "mock_erp_pg")
        self.assertEqual(producer.interval_seconds, 2.5)
        self.assertEqual(producer.days_per_batch, 3)
        self.assertEqual(producer.max_batches, 4)

    def test_system_settings_use_service_specific_database_prefixes(self) -> None:
        with patch.dict(
            os.environ,
            {
                "MOCK_ERP_POSTGRES_USER": "source_user",
                "MOCK_ERP_POSTGRES_PASSWORD": "source_password",
                "MOCK_ERP_POSTGRES_DB": "source_db",
                "WAREHOUSE_POSTGRES_USER": "warehouse_user",
                "WAREHOUSE_POSTGRES_PASSWORD": "warehouse_password",
                "WAREHOUSE_POSTGRES_DB": "warehouse_db",
                "AIRFLOW_DB_USER": "airflow_user",
                "AIRFLOW_DB_PASSWORD": "airflow_password",
                "AIRFLOW_DB_NAME": "airflow_db",
                "ODOO_DB_USER": "odoo_user",
                "ODOO_DB_PASSWORD": "odoo_password",
                "ODOO_DB_NAME": "odoo_db",
            },
            clear=True,
        ):
            self.assertEqual(settings.mock_erp_db.user, "source_user")
            self.assertEqual(settings.warehouse_db.database, "warehouse_db")
            self.assertEqual(settings.dashboard_db.password, "warehouse_password")
            self.assertEqual(settings.airflow_db.user, "airflow_user")
            self.assertEqual(settings.odoo_db.database, "odoo_db")


if __name__ == "__main__":
    unittest.main()
