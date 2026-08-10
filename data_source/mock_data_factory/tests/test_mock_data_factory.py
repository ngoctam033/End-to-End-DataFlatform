from __future__ import annotations

import unittest

from data_source.mock_data_factory.adapters.mock_erp_pg import render_mock_erp_pg_sql
from data_source.mock_data_factory.scenarios.omnichannel_fmcg import build_scenario_set


class MockDataFactoryTest(unittest.TestCase):
    def test_omnichannel_scenario_has_business_orders(self) -> None:
        scenario_set = build_scenario_set()

        self.assertEqual(scenario_set.name, "omnichannel_d2c_fmcg")
        self.assertEqual(len(scenario_set.sales_orders), 2)
        self.assertTrue(all(order.lines for order in scenario_set.sales_orders))
        self.assertTrue(all(order.invoice_date for order in scenario_set.sales_orders))
        self.assertTrue(all(order.carrier_id for order in scenario_set.sales_orders))
        self.assertTrue(
            any(
                line.promotion_id is not None
                for order in scenario_set.sales_orders
                for line in order.lines
            )
        )

    def test_mock_erp_pg_adapter_uses_business_functions(self) -> None:
        sql = render_mock_erp_pg_sql(build_scenario_set())

        self.assertIn("erp_sales.create_sales_order", sql)
        self.assertIn("erp_sales.add_sales_order_line", sql)
        self.assertIn("erp_sales.confirm_order", sql)
        self.assertIn("erp_sales.fulfill_order", sql)
        self.assertIn("erp_finance.create_invoice_from_order", sql)
        self.assertIn("erp_finance.record_payment", sql)
        self.assertIn("NULL, 0, 1", sql)
        self.assertIn("DATE '2026-08-02', 2", sql)
        self.assertIn("DATE '2026-08-04', 5", sql)
        self.assertNotIn("INSERT INTO erp_sales.sales_orders", sql)


if __name__ == "__main__":
    unittest.main()
