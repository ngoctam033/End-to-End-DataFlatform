from __future__ import annotations

import io
import unittest
from pathlib import Path
from unittest.mock import patch

from data_source.mock_data_factory.adapters.mock_erp_pg import (
    MockErpPgDockerPsqlTransactionWriter,
    render_mock_erp_pg_sql,
)
from data_source.mock_data_factory.interfaces import TransactionWriter
from data_source.mock_data_factory.models import BusinessScenarioSet
from data_source.mock_data_factory.producer import (
    format_scenario_record_log,
    parse_args,
    run_producer,
)
from data_source.mock_data_factory.scenarios.omnichannel_fmcg import (
    OmnichannelFmcgScenarioProvider,
    build_scenario_set,
)


class FakeWriter(TransactionWriter):
    def __init__(self) -> None:
        self.written_batches: list[BusinessScenarioSet] = []

    def write(self, scenario_set: BusinessScenarioSet) -> None:
        self.written_batches.append(scenario_set)


class FailingOnceWriter(TransactionWriter):
    def __init__(self) -> None:
        self.written_batches: list[BusinessScenarioSet] = []
        self._failed = False

    def write(self, scenario_set: BusinessScenarioSet) -> None:
        if not self._failed:
            self._failed = True
            raise RuntimeError("transient write failure")

        self.written_batches.append(scenario_set)


class MockDataFactoryTest(unittest.TestCase):
    def test_omnichannel_scenario_has_business_orders(self) -> None:
        scenario_set = build_scenario_set()

        self.assertEqual(scenario_set.name, "omnichannel_d2c_fmcg")
        self.assertEqual(len(scenario_set.sales_orders), 2)
        self.assertTrue(all(order.lines for order in scenario_set.sales_orders))
        self.assertTrue(all(order.invoice_date for order in scenario_set.sales_orders))
        self.assertTrue(all(order.carrier_code for order in scenario_set.sales_orders))
        self.assertTrue(
            any(
                line.promotion_code is not None
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
        self.assertIn("erp_inventory.replenish_demo_stock", sql)
        self.assertIn("customer_code = 'CUS-00001'", sql)
        self.assertIn("sku = 'TEA-LEM-330'", sql)
        self.assertIn("promotion_code = 'WEB-TEA-AUG10'", sql)
        self.assertIn("carrier_code = 'GHTK-EXP'", sql)
        self.assertNotIn("INSERT INTO erp_sales.sales_orders", sql)
        self.assertNotIn("v_order_id, 1, 1, 12", sql)

    def test_scenario_provider_shifts_transaction_dates_per_batch(self) -> None:
        provider = OmnichannelFmcgScenarioProvider(days_per_batch=1)

        first_batch = provider.next_batch()
        second_batch = provider.next_batch()

        self.assertEqual(
            second_batch.sales_orders[0].order_date,
            first_batch.sales_orders[0].order_date.replace(day=2),
        )
        self.assertEqual(
            second_batch.sales_orders[0].payments[0].payment_date,
            first_batch.sales_orders[0].payments[0].payment_date.replace(day=4),
        )

    def test_producer_writes_expected_number_of_batches(self) -> None:
        provider = OmnichannelFmcgScenarioProvider(days_per_batch=1)
        writer = FakeWriter()

        batch_count = run_producer(
            scenario_provider=provider,
            transaction_writer=writer,
            interval_seconds=0,
            max_batches=3,
            verbose=False,
        )

        self.assertEqual(batch_count, 3)
        self.assertEqual(len(writer.written_batches), 3)
        self.assertEqual(
            writer.written_batches[2].sales_orders[0].order_date.day,
            3,
        )

    def test_producer_skips_failed_batches_and_continues(self) -> None:
        provider = OmnichannelFmcgScenarioProvider(days_per_batch=1)
        writer = FailingOnceWriter()

        with patch("sys.stderr", new_callable=io.StringIO) as stderr:
            batch_count = run_producer(
                scenario_provider=provider,
                transaction_writer=writer,
                interval_seconds=0,
                max_batches=2,
                verbose=False,
            )

        self.assertEqual(batch_count, 2)
        self.assertEqual(len(writer.written_batches), 1)
        self.assertEqual(writer.written_batches[0].sales_orders[0].order_date.day, 2)
        self.assertIn("status=skipped", stderr.getvalue())
        self.assertIn("transient write failure", stderr.getvalue())

    def test_producer_can_start_without_cli_arguments(self) -> None:
        with patch("sys.argv", ["producer.py"]):
            args = parse_args()

        self.assertEqual(args.target, "mock_erp_pg")
        self.assertIsNone(args.database_url)
        self.assertEqual(args.interval_seconds, 10)
        self.assertEqual(args.days_per_batch, 1)
        self.assertIsNone(args.max_batches)

    def test_producer_defaults_can_be_overridden_by_environment(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "MOCK_DATA_PRODUCER_DATABASE_URL": "postgresql://user:pass@db:5432/demo",
                "MOCK_DATA_PRODUCER_INTERVAL_SECONDS": "2.5",
                "MOCK_DATA_PRODUCER_DAYS_PER_BATCH": "3",
                "MOCK_DATA_PRODUCER_MAX_BATCHES": "4",
            },
        ):
            with patch("sys.argv", ["producer.py"]):
                args = parse_args()

        self.assertEqual(args.database_url, "postgresql://user:pass@db:5432/demo")
        self.assertEqual(args.interval_seconds, 2.5)
        self.assertEqual(args.days_per_batch, 3)
        self.assertEqual(args.max_batches, 4)

    def test_docker_psql_writer_executes_payload_in_mock_erp_container(self) -> None:
        with patch.dict(
            "os.environ",
            {
                "MOCK_ERP_POSTGRES_USER": "mock_erp",
                "MOCK_ERP_POSTGRES_PASSWORD": "mock_erp_pass",
                "MOCK_ERP_POSTGRES_DB": "mock_erp",
            },
        ):
            writer = MockErpPgDockerPsqlTransactionWriter(Path("/tmp/mock-compose.yml"))

            with patch(
                "data_source.mock_data_factory.adapters.mock_erp_pg.subprocess.run"
            ) as run_mock:
                writer.write(build_scenario_set())

            run_mock.assert_called_once()
            command = run_mock.call_args.args[0]
            self.assertEqual(command[:5], ["docker", "compose", "-f", "/tmp/mock-compose.yml", "exec"])
            self.assertIn("mock_erp_pg", command)
            self.assertIn("psql", command)
            self.assertIn("erp_sales.create_sales_order", run_mock.call_args.kwargs["input"])
            self.assertTrue(run_mock.call_args.kwargs["check"])

    def test_producer_log_contains_record_level_values(self) -> None:
        log_text = format_scenario_record_log(1, build_scenario_set())

        self.assertIn("mock_transaction_batch=1", log_text)
        self.assertIn("sales_order index=1", log_text)
        self.assertIn("customer_code=CUS-00001", log_text)
        self.assertIn("sku=TEA-LEM-330", log_text)
        self.assertIn("quantity=12", log_text)
        self.assertIn("promotion_code=WEB-TEA-AUG10", log_text)
        self.assertIn("carrier_code=GHTK-EXP", log_text)
        self.assertIn("payment index=1 amount=100000", log_text)


if __name__ == "__main__":
    unittest.main()
