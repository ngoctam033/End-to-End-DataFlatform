"""Start mock ERP PostgreSQL and continuously write mock transactions."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from data_source.mock_data_factory.adapters.mock_erp_pg import (
    MockErpPgDockerPsqlTransactionWriter,
)
from data_source.mock_data_factory.producer import (
    DEFAULT_DAYS_PER_BATCH,
    DEFAULT_INTERVAL_SECONDS,
    run_producer,
)
from data_source.mock_data_factory.scenarios.omnichannel_fmcg import (
    OmnichannelFmcgScenarioProvider,
)

COMPOSE_FILE = PROJECT_ROOT / "data_source/mock_erp_pg/docker-compose.mock_erp_pg.yml"


def optional_int(value: str | None) -> int | None:
    if value is None or value == "":
        return None
    return int(value)


def ensure_mock_erp_pg_is_running() -> None:
    subprocess.run(
        ["docker", "network", "inspect", "end2end_data_network"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    subprocess.run(
        ["docker", "network", "create", "end2end_data_network"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        check=False,
    )
    subprocess.run(
        [
            "docker",
            "compose",
            "-f",
            str(COMPOSE_FILE),
            "up",
            "-d",
            "--wait",
            "mock_erp_pg",
        ],
        check=True,
    )


def main() -> None:
    interval_seconds = float(
        os.getenv("MOCK_DATA_PRODUCER_INTERVAL_SECONDS", DEFAULT_INTERVAL_SECONDS)
    )
    days_per_batch = int(
        os.getenv("MOCK_DATA_PRODUCER_DAYS_PER_BATCH", DEFAULT_DAYS_PER_BATCH)
    )
    max_batches = optional_int(os.getenv("MOCK_DATA_PRODUCER_MAX_BATCHES"))

    ensure_mock_erp_pg_is_running()

    run_producer(
        scenario_provider=OmnichannelFmcgScenarioProvider(days_per_batch=days_per_batch),
        transaction_writer=MockErpPgDockerPsqlTransactionWriter(COMPOSE_FILE),
        interval_seconds=interval_seconds,
        max_batches=max_batches,
    )


if __name__ == "__main__":
    main()
