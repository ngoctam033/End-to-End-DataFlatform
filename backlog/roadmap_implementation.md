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

## Definition of Done chung

- Có metadata cập nhật đúng trong file backlog.
- Có test tự động và dữ liệu test tái lập được.
- Có tài liệu contract/schema và dependency.
- Có logging, metrics hoặc pipeline status phù hợp.
- Có hướng dẫn chạy local và xử lý lỗi thường gặp.
- Không commit credential thật.
