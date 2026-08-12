from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ANALYTICS_SQL = PROJECT_ROOT / "transformation/sql/analytics_models.sql"
FRONTEND_HTML = PROJECT_ROOT / "serving/dashboard_app/static/index.html"


class DashboardArtifactsTest(unittest.TestCase):
    def test_analytics_sql_defines_dim_fact_and_mart_models(self) -> None:
        sql = ANALYTICS_SQL.read_text(encoding="utf-8")

        expected_models = [
            "analytics.dim_customer",
            "analytics.dim_product",
            "analytics.dim_channel",
            "analytics.dim_warehouse",
            "analytics.fact_sales_order_lines",
            "analytics.fact_inventory_balance",
            "analytics.fact_logistics_shipments",
            "analytics.mart_dashboard_kpis",
            "analytics.mart_sales_by_channel",
            "analytics.mart_inventory_alerts",
            "analytics.mart_logistics_performance",
            "analytics.mart_customer_rfm",
        ]

        for model in expected_models:
            self.assertIn(model, sql)

    def test_frontend_contains_business_dashboard_sections(self) -> None:
        html = FRONTEND_HTML.read_text(encoding="utf-8")

        self.assertIn("Daily Revenue Trend", html)
        self.assertIn("Revenue by Channel", html)
        self.assertIn("Top Products", html)
        self.assertIn("Inventory Health", html)
        self.assertIn("Logistics Performance", html)
        self.assertIn("Customer RFM", html)


if __name__ == "__main__":
    unittest.main()
