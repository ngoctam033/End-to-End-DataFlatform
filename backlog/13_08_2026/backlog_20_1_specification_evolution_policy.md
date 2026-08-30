---
id: BL-020.1
status: done
priority: P1
priority_rank: 20.1
category: platform
owner: unassigned
created_at: 2026-08-16
updated_at: 2026-08-18
progress: 100
effort: S
value: high
dependencies: [BL-020]
tags: [data-contract, canonical-model, specification, schema-evolution]
target_release: null
---

# Backlog 20.1: Data Contract Envelope Specification & Schema Evolution Policy

## Mục tiêu

Quy chuẩn cấu trúc Envelope Metadata tiêu chuẩn cho mọi bản ghi trong data platform và thiết lập chính sách quản lý Schema Evolution.

## Phạm vi

- Định nghĩa envelope metadata bắt buộc: `business_key`, `source_key`, `source_system`, `event_time`, `ingestion_time`, `schema_version`.
- Quy định chính sách Semantic Versioning (`MAJOR.MINOR.PATCH`) cho data contracts.
- Quy chuẩn về Breaking Changes vs Non-breaking Changes, fallback values và quy trình deprecation.
- Tạo tài liệu `docs/data_contracts/01_canonical_model_spec.md` và `docs/data_contracts/02_schema_evolution_policy.md`.

## Kết quả mong muốn

Toàn bộ team có quy chuẩn chung về metadata envelope và quy tắc thay đổi schema mà không gây vỡ pipeline downstream.
