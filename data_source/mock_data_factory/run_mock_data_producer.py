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
from data_source.mock_data_factory.producer import run_producer
from data_source.mock_data_factory.scenarios.omnichannel_fmcg import (
    OmnichannelFmcgScenarioProvider,
)
# Configuration guide: docs/operations/secrets_management.md
from shared.settings import settings

COMPOSE_FILE = PROJECT_ROOT / "data_source/mock_erp_pg/docker-compose.mock_erp_pg.yml"


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
    ensure_mock_erp_pg_is_running()

    run_producer(
        scenario_provider=OmnichannelFmcgScenarioProvider(days_per_batch=settings.producer.days_per_batch),
        transaction_writer=MockErpPgDockerPsqlTransactionWriter(COMPOSE_FILE),
        interval_seconds=settings.producer.interval_seconds,
        max_batches=settings.producer.max_batches,
    )


if __name__ == "__main__":
    main()
