---
id: BL-020.4
status: done
priority: P1
priority_rank: 20.4
category: platform
owner: unassigned
created_at: 2026-08-16
updated_at: 2026-08-28
progress: 100
effort: M
value: high
dependencies: [BL-020.2, BL-020.3]
tags: [data-contract, python, validator, schema-enforcement]
target_release: null
---

# Backlog 20.4: Data Contract Validation Engine (Python Module)

## Mục tiêu

Phát triển module Python validator để thực thi kiểm tra tính hợp lệ của data payload và bổ sung metadata envelope trước khi lưu trữ vào Raw/Staging layer.

## Phạm vi

- Tạo module `contracts/validator.py` với khả năng:
  - Load và cache các file YAML schema trong `contracts/schemas/`.
  - Validate payload bằng `jsonschema` library.
  - Tự động gán metadata envelope (`ingestion_time`, `schema_version`, validation status).
  - Trả về danh sách chi tiết lỗi schema validation nếu record không đạt chuẩn.

## Kết quả mong muốn

Ingestion pipeline (Python/Spark) có thể dễ dàng import và gọi validator engine để lọc hoặc chuyển các bản ghi rác vào Dead Letter Queue (DLQ).

## Kết quả triển khai

- Đã tạo package `contracts` và module `contracts/validator.py`.
- Validator load và cache YAML schemas, kiểm tra Draft 2020-12 và resolve schema references.
- API `validate_payload` tự tạo metadata envelope, UTC `ingestion_time`, contract version và processing status.
- Record hợp lệ được route tới `silver`; record lỗi giữ nguyên payload, chuyển `QUARANTINED` và route tới `quarantine`.
- Lỗi validation có code, JSON path, message, validator và schema path để ghi DLQ.
- Có API kiểm tra envelope sẵn có, fail-fast cho entity/schema configuration không hợp lệ và không mutate input.
- Image ingestion đã cài runtime dependencies và copy package `contracts` để pipeline có thể import validator.
- Đã bổ sung tài liệu sử dụng và 10 unit tests cho envelope, valid/invalid payload, error detail, UTC, cache và configuration errors.
- Chạy `python -m unittest -v tests.test_contract_validator`: 10 test thành công.
