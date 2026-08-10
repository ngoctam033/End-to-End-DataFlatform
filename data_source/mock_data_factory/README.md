# Mock Data Factory

This folder contains a source-agnostic mock data framework.

It generates business scenarios once, then exports them to concrete data sources through adapters.
Scenarios currently cover omnichannel FMCG orders with channel pricing, promotions, fulfillment carriers, invoices, and payments.

The factory does not define master data. It only references existing master data
by stable business codes such as `customer_code`, `channel_code`, `sku`,
`warehouse_code`, `promotion_code`, and `carrier_code`.

Current adapter:

- `mock_erp_pg`: exports SQL that calls PostgreSQL/PLpgSQL business functions in `data_source/mock_erp_pg`.

Future adapters can target:

- Odoo ORM/API.
- REST mock business API.
- CSV/JSON source extracts.

## Why This Exists

The project should not hard-code transaction inserts directly inside each data source. Instead:

```text
Mock Data Factory
-> transaction scenario objects
-> data-source adapter
-> lookup master data in PostgreSQL / Odoo / API / CSV
-> call source business functions or APIs
```

This keeps transaction scenarios reusable while allowing master data ownership to stay inside the source system.

## Generate SQL For mock_erp_pg

From the project root:

```bash
python -m data_source.mock_data_factory.cli \
  --target mock_erp_pg \
  --output data_source/mock_erp_pg/init/05_demo_transactions.sql
```

Then recreate the mock ERP database:

```bash
cd data_source/mock_erp_pg
docker compose -f docker-compose.mock_erp_pg.yml down -v
docker compose -f docker-compose.mock_erp_pg.yml up -d mock_erp_pg
```

## Run Continuous Producer

Start the mock ERP database:

```bash
docker network inspect end2end_data_network >/dev/null 2>&1 || docker network create end2end_data_network
cd data_source/mock_erp_pg
docker compose -f docker-compose.mock_erp_pg.yml up -d mock_erp_pg
```

Run the producer locally with default settings:

```bash
python data_source/mock_data_factory/run_mock_data_producer.py
```

The default connection is:

```text
postgresql://mock_erp:mock_erp@localhost:55432/mock_erp
```

Override defaults with environment variables when needed:

```bash
MOCK_DATA_PRODUCER_INTERVAL_SECONDS=5 \
MOCK_DATA_PRODUCER_MAX_BATCHES=1 \
python data_source/mock_data_factory/run_mock_data_producer.py
```

Or run it as a Docker Compose service:

```bash
cd data_source/mock_erp_pg
docker compose -f docker-compose.mock_erp_pg.yml up -d --build mock_data_producer
```

For a short smoke test, limit the number of batches:

```bash
MOCK_DATA_PRODUCER_INTERVAL_SECONDS=0 \
MOCK_DATA_PRODUCER_MAX_BATCHES=1 \
python data_source/mock_data_factory/run_mock_data_producer.py
```
