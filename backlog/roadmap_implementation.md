# Implementation roadmap

Roadmap nay gom cac backlog hien co va cac backlog moi thanh cac phase co the trien khai lan luot. Dependency la rang buoc chinh; `priority_rank` trong front matter dung de sap xep trong tung phase.

## Phase 0 — Baseline và an toàn

1. `BL-016` — Secrets Management
2. `BL-020` — Source Contracts and Canonical Data Model

Mục tiêu là thống nhất contract, business key và cách quản lý credential trước khi mở rộng thêm nguồn.

## Phase 1 — Data platform foundation

1. `BL-011` — Raw/Staging Layer on MinIO
2. `BL-007` — Incremental Load/CDC
3. `BL-008` — Airflow Orchestration
4. `BL-009` — Data Quality Checks
5. `BL-014` — dbt Models, Tests and Documentation
6. `BL-010` — Logging, Monitoring and Alerting
7. `BL-017` — CI/CD and Integration Tests
8. `BL-018` — Data Lineage and Metadata
9. `BL-019` — Dashboard Pipeline Health

## Phase 2 — Nguồn nghiệp vụ độc lập

1. `BL-021` — Mock OMS Service
2. `BL-022` — Mock WMS Service
3. `BL-023` — Mock OPS Service
4. `BL-024` — Mock MongoDB Source
5. `BL-025` — Mock External API Source
6. `BL-026` — Mock SharePoint and Google Drive Sources

Mỗi source cần có contract, test data, healthcheck, adapter ingestion và test failure trước khi đưa vào pipeline chung.

## Phase 3 — Mở rộng processing

1. `BL-012` — Kafka Streaming
2. `BL-013` — Spark Processing
3. `BL-004` — Kafka/Spark Learning Branch
4. `BL-015` — Slowly Changing Dimension Type 2
5. `BL-003` — Master Data Changes/SCD Scenario
6. `BL-005` — Expand Transaction Volume

## Phase 4 — Production runtime

1. `BL-027` — Kubernetes Data Runtime

Chỉ chuyển sang Kubernetes sau khi pipeline đã có retry, quality checks, observability, tests và secrets management ở mức dùng được.

## Phase 5 — Business data products

1. `BL-001` — Target/Budget Data
2. `BL-002` — Purchase/Supplier Data
3. `BL-006` — Visualization Dim Date
4. `BL-028` — Business Data Products and Reporting Automation

## Phase 6 — Technical ownership

1. `BL-029` — Production Standards and Runbooks

## Backlog mới — Source validation và data models

Các backlog sau được bổ sung, không thay thế backlog cũ:

1. `BL-030` — Source Business Rule Validation
2. `BL-031` — Market Basket Analysis Model
3. `BL-032` — FMCG Expiry and Lot Health Model
4. `BL-033` — Customer Churn and Purchase Cycle Model
5. `BL-034` — Failed Delivery and Return Analytics Model
6. `BL-035` — Seasonal Demand and Out-of-Stock Forecast Model

## Backlog mới — Source Odoo Sales, Order và Fulfillment

1. `BL-036` — Odoo Sales, Order and Fulfillment Source
2. `BL-036.1` — Odoo Foundation Master Data
3. `BL-036.2` — Odoo Sales Order Extraction
4. `BL-036.3` — Odoo Inventory and FMCG Lots
5. `BL-036.4` — Odoo Delivery and Fulfillment
6. `BL-036.5` — Odoo Invoice and Payment
7. `BL-036.6` — Odoo Return and Refund

## Backlog mới — CRM data platform

1. `BL-046` — CRM Source and Canonical Model
2. `BL-047` — CRM Mock Source and Event Generator
3. `BL-048` — Customer 360 and Identity Resolution
4. `BL-049` — CRM Lead and Opportunity Funnel Model
5. `BL-050` — CRM Activity and Interaction Model
6. `BL-051` — CRM Campaign and Marketing Attribution Model
7. `BL-052` — Customer Lifetime Value and Retention Model
8. `BL-053` — CRM Data Quality and Reconciliation
9. `BL-054` — CRM KPI and Semantic Layer
10. `BL-055` — CRM PII Governance and Access Control

Các backlog CRM phụ thuộc vào data platform foundation, source contract và customer identity resolution. `BL-049`, `BL-050` và `BL-051` có thể triển khai song song sau `BL-048`; `BL-052` phụ thuộc thêm `BL-033`.

## Definition of Done chung

- Có metadata cập nhật đúng trong file backlog.
- Có test tự động và dữ liệu test tái lập được.
- Có tài liệu contract/schema và dependency.
- Có logging, metrics hoặc pipeline status phù hợp.
- Có hướng dẫn chạy local và xử lý lỗi thường gặp.
- Không commit credential thật.
