# Mock Data Factory

This folder contains a source-agnostic mock data framework.

It generates business scenarios once, then exports them to concrete data sources through adapters.
Scenarios currently cover omnichannel FMCG orders with channel pricing, promotions, fulfillment carriers, invoices, and payments.

Current adapter:

- `mock_erp_pg`: exports SQL that calls PostgreSQL/PLpgSQL business functions in `data_source/mock_erp_pg`.

Future adapters can target:

- Odoo ORM/API.
- REST mock business API.
- CSV/JSON source extracts.

## Why This Exists

The project should not hard-code sample data directly inside each data source. Instead:

```text
Mock Data Factory
-> scenario objects
-> data-source adapter
-> PostgreSQL / Odoo / API / CSV
```

This keeps the business scenarios reusable while allowing the source system implementation to evolve.

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
