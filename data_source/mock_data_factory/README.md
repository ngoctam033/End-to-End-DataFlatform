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
docker compose --env-file ../../.env -f docker-compose.mock_erp_pg.yml down -v
docker compose --env-file ../../.env -f docker-compose.mock_erp_pg.yml up -d mock_erp_pg
```

## Run Continuous Producer

Start the mock ERP backend and the continuous producer:

```bash
cp .env.example .env
cd data_source/mock_erp_pg
docker compose --env-file ../../.env -f docker-compose.mock_erp_pg.yml up -d --build
```

Run the producer locally after exporting the variables from the local `.env` file:

```bash
set -a
. ./.env
set +a
python data_source/mock_data_factory/run_mock_data_producer.py
```

The producer builds its connection from these required environment variables:

```text
MOCK_ERP_POSTGRES_USER
MOCK_ERP_POSTGRES_PASSWORD
MOCK_ERP_POSTGRES_DB
MOCK_ERP_PG_EXTERNAL_PORT
```

`PIPELINE_SOURCE_DATABASE_URL` or `MOCK_DATA_PRODUCER_DATABASE_URL` may be used as an explicit connection URL override. Keep real credentials in `.env`; do not add them to documentation or source control.

Override non-secret producer settings when needed:

```bash
MOCK_DATA_PRODUCER_INTERVAL_SECONDS=5 \
MOCK_DATA_PRODUCER_MAX_BATCHES=1 \
python data_source/mock_data_factory/run_mock_data_producer.py
```

Or run it as a Docker Compose service:

```bash
cd data_source/mock_erp_pg
docker compose --env-file ../../.env -f docker-compose.mock_erp_pg.yml up -d --build
```

For a short smoke test, limit the number of batches:

```bash
MOCK_DATA_PRODUCER_INTERVAL_SECONDS=0 \
MOCK_DATA_PRODUCER_MAX_BATCHES=1 \
python data_source/mock_data_factory/run_mock_data_producer.py
```
