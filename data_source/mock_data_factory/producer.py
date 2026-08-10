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
            print(
                f"Wrote mock transaction batch {batch_count}: {scenario_set.name}",
                flush=True,
            )

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
