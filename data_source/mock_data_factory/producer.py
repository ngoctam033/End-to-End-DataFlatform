"""Continuously produce mock transactions into a source system."""

from __future__ import annotations

import argparse
import os
import time

from data_source.mock_data_factory.adapters.mock_erp_pg import MockErpPgTransactionWriter
from data_source.mock_data_factory.interfaces import (
    TransactionScenarioProvider,
    TransactionWriter,
)
from data_source.mock_data_factory.scenarios.omnichannel_fmcg import (
    OmnichannelFmcgScenarioProvider,
)
from data_source.mock_data_factory.models import BusinessScenarioSet

DEFAULT_TARGET = "mock_erp_pg"
DEFAULT_DATABASE_URL = "postgresql://mock_erp:mock_erp@localhost:55432/mock_erp"
DEFAULT_INTERVAL_SECONDS = 10
DEFAULT_DAYS_PER_BATCH = 1


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--target",
        choices=("mock_erp_pg",),
        default=os.getenv("MOCK_DATA_PRODUCER_TARGET", DEFAULT_TARGET),
    )
    parser.add_argument(
        "--database-url",
        default=os.getenv("MOCK_DATA_PRODUCER_DATABASE_URL", DEFAULT_DATABASE_URL),
    )
    parser.add_argument(
        "--interval-seconds",
        type=float,
        default=float(
            os.getenv("MOCK_DATA_PRODUCER_INTERVAL_SECONDS", DEFAULT_INTERVAL_SECONDS)
        ),
    )
    parser.add_argument(
        "--days-per-batch",
        type=int,
        default=int(os.getenv("MOCK_DATA_PRODUCER_DAYS_PER_BATCH", DEFAULT_DAYS_PER_BATCH)),
    )
    parser.add_argument(
        "--max-batches",
        type=int,
        default=_optional_int(os.getenv("MOCK_DATA_PRODUCER_MAX_BATCHES")),
    )
    return parser.parse_args()


def _optional_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def format_scenario_record_log(batch_count: int, scenario_set: BusinessScenarioSet) -> str:
    lines = [
        f"mock_transaction_batch={batch_count} scenario_set={scenario_set.name} "
        f"sales_orders={len(scenario_set.sales_orders)}"
    ]

    for order_index, order in enumerate(scenario_set.sales_orders, start=1):
        lines.append(
            "  sales_order "
            f"index={order_index} "
            f"scenario={order.name} "
            f"customer_code={order.customer_code} "
            f"channel_code={order.channel_code} "
            f"branch_code={order.branch_code} "
            f"order_date={order.order_date.isoformat()} "
            f"lines={len(order.lines)}"
        )

        for line_index, order_line in enumerate(order.lines, start=1):
            lines.append(
                "    sales_order_line "
                f"index={line_index} "
                f"sku={order_line.sku} "
                f"warehouse_code={order_line.warehouse_code} "
                f"quantity={order_line.quantity} "
                f"unit_price={order_line.unit_price if order_line.unit_price is not None else 'AUTO'} "
                f"discount_amount={order_line.discount_amount} "
                f"promotion_code={order_line.promotion_code or 'NONE'}"
            )

        if order.fulfillment_date is not None:
            lines.append(
                "    shipment "
                f"carrier_code={order.carrier_code} "
                f"fulfillment_date={order.fulfillment_date.isoformat()}"
            )

        if order.invoice_date is not None:
            lines.append(
                "    invoice "
                f"invoice_date={order.invoice_date.isoformat()} "
                f"due_days={order.due_days}"
            )

        for payment_index, payment in enumerate(order.payments, start=1):
            lines.append(
                "    payment "
                f"index={payment_index} "
                f"amount={payment.amount} "
                f"method={payment.method} "
                f"payment_date={payment.payment_date.isoformat()}"
            )

        for return_index, return_item in enumerate(order.returns, start=1):
            lines.append(
                "    return "
                f"index={return_index} "
                f"line_index={return_item.line_index} "
                f"quantity={return_item.quantity} "
                f"reason={return_item.reason} "
                f"return_date={return_item.return_date.isoformat()}"
            )

    return "\n".join(lines)


def run_producer(
    scenario_provider: TransactionScenarioProvider,
    transaction_writer: TransactionWriter,
    interval_seconds: float,
    max_batches: int | None = None,
    verbose: bool = True,
) -> int:
    if interval_seconds < 0:
        raise ValueError("interval_seconds must be zero or positive")

    batch_count = 0

    while max_batches is None or batch_count < max_batches:
        scenario_set = scenario_provider.next_batch()
        transaction_writer.write(scenario_set)
        batch_count += 1

        if verbose:
            print(format_scenario_record_log(batch_count, scenario_set), flush=True)

        if max_batches is None or batch_count < max_batches:
            time.sleep(interval_seconds)

    return batch_count


def main() -> None:
    args = parse_args()

    if args.target == "mock_erp_pg":
        writer = MockErpPgTransactionWriter(args.database_url)
    else:
        raise ValueError(f"Unsupported target: {args.target}")

    provider = OmnichannelFmcgScenarioProvider(days_per_batch=args.days_per_batch)
    run_producer(
        scenario_provider=provider,
        transaction_writer=writer,
        interval_seconds=args.interval_seconds,
        max_batches=args.max_batches,
    )


if __name__ == "__main__":
    main()
