# Mock ERP PostgreSQL Source

This service is a lightweight ERP-like business source for the data platform.

It uses PostgreSQL tables, constraints, and PL/pgSQL functions to validate business logic before data is extracted into ingestion and analytical pipelines.

## Purpose

The goal is not to replace a real ERP forever. The goal is to provide a controlled business layer for the current demo:

```text
Mock ERP PostgreSQL
-> business-valid operational data
-> ingestion
-> storage
-> transformation
-> BI / analytics
```

Later, this source can be replaced by Odoo or another ERP backend while keeping the downstream data platform boundaries similar.

## Business Rules Covered

- Products, customers, branches, warehouses, and sales channels must exist before transactions.
- Carriers, price lists, and promotions act as ERP master data for logistics and commercial policy.
- Sales order lines use channel-valid price lists when no manual unit price is provided.
- Promotions must match the order channel and order date before discount calculation is allowed.
- Stock reservation cannot exceed available stock.
- Sales order line quantity and unit price must be positive.
- Confirming an order reserves stock and changes the order status.
- Fulfillment creates shipment and delivery attempt records.
- Delivery attempts cannot happen before the planned ship date.
- Invoicing is only allowed for confirmed orders.
- Payments cannot exceed invoice outstanding amount.
- Return quantity cannot exceed sold quantity minus previous returns.
- FMCG lot expiration date must be after manufacturing date.

## Run

From this folder:

```bash
docker compose -f docker-compose.mock_erp_pg.yml up -d mock_erp_pg
```

Run business-rule tests:

```bash
docker compose -f docker-compose.mock_erp_pg.yml down -v
docker compose -f docker-compose.mock_erp_pg.yml up --abort-on-container-exit mock_erp_pg_tests
```

Run the continuous transaction producer:

```bash
docker compose -f docker-compose.mock_erp_pg.yml up -d --build mock_data_producer
```

Run the producer locally with one Python file:

```bash
cd ../..
python data_source/mock_data_factory/run_mock_data_producer.py
```

Optional producer tuning:

```bash
MOCK_DATA_PRODUCER_INTERVAL_SECONDS=5 \
MOCK_DATA_PRODUCER_DAYS_PER_BATCH=1 \
docker compose -f docker-compose.mock_erp_pg.yml up -d --build mock_data_producer
```

Connection:

```text
host: localhost
port: 55432
database: mock_erp
user: mock_erp
password: mock_erp
```
