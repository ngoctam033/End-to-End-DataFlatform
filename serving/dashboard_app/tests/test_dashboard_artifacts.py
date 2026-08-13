from __future__ import annotations

import unittest
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[3]
ANALYTICS_SQL = PROJECT_ROOT / "transformation/sql/analytics_models.sql"
FRONTEND_SOURCE = PROJECT_ROOT / "serving/dashboard_app/frontend/src/main.jsx"
FRONTEND_CSS = PROJECT_ROOT / "serving/dashboard_app/frontend/src/styles.css"
FRONTEND_PACKAGE = PROJECT_ROOT / "serving/dashboard_app/frontend/package.json"
FRONTEND_COMPONENTS = PROJECT_ROOT / "serving/dashboard_app/frontend/src/components"


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
        source = FRONTEND_SOURCE.read_text(encoding="utf-8")

        self.assertIn("Daily Revenue Trend", source)
        self.assertIn("Revenue by Channel", source)
        self.assertIn("Top Products", source)
        self.assertIn("Inventory Health", source)
        self.assertIn("Logistics Performance", source)
        self.assertIn("Customer RFM", source)

    def test_frontend_uses_full_screen_responsive_layout(self) -> None:
        table_component = (FRONTEND_COMPONENTS / "DataTable.jsx").read_text(encoding="utf-8")
        css = FRONTEND_CSS.read_text(encoding="utf-8")

        self.assertIn('className="table-scroll"', table_component)
        self.assertIn("min-height: 100vh", css)
        self.assertIn("width: 100%", css)
        self.assertIn("repeat(auto-fit, minmax(190px, 1fr))", css)
        self.assertIn("@media (max-width: 760px)", css)
        self.assertNotIn("max-width: 1440px", css)

    def test_frontend_is_react_vite_app(self) -> None:
        package_json = FRONTEND_PACKAGE.read_text(encoding="utf-8")
        source = FRONTEND_SOURCE.read_text(encoding="utf-8")
        component_files = {path.name for path in FRONTEND_COMPONENTS.glob("*.jsx")}

        self.assertIn('"react"', package_json)
        self.assertIn('"vite"', package_json)
        self.assertIn("createRoot", source)
        self.assertIn("KpiCard.jsx", component_files)
        self.assertIn("ChartPanel.jsx", component_files)
        self.assertIn("DataTable.jsx", component_files)
        self.assertIn("Panel.jsx", component_files)


if __name__ == "__main__":
    unittest.main()
