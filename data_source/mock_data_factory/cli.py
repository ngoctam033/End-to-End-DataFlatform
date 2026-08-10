"""Generate mock data payloads for project data sources."""

from __future__ import annotations

import argparse
from pathlib import Path

from data_source.mock_data_factory.adapters.mock_erp_pg import render_mock_erp_pg_sql
from data_source.mock_data_factory.scenarios.omnichannel_fmcg import build_scenario_set


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--target", choices=("mock_erp_pg",), default="mock_erp_pg")
    parser.add_argument("--output", type=Path, required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    scenario_set = build_scenario_set()

    if args.target == "mock_erp_pg":
        payload = render_mock_erp_pg_sql(scenario_set)
    else:
        raise ValueError(f"Unsupported target: {args.target}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(payload, encoding="utf-8")
    print(f"Generated {args.target} mock data payload: {args.output}")


if __name__ == "__main__":
    main()

