---
id: BL-020.5
status: done
priority: P1
priority_rank: 20.5
category: platform
owner: unassigned
created_at: 2026-08-16
updated_at: 2026-08-28
progress: 100
effort: S
value: high
dependencies: [BL-020.4]
tags: [data-contract, pytest, unit-tests, verification]
target_release: null
---

# Backlog 20.5: Automated Test Suite & Multi-Source Contract Verification

## Mục tiêu

Xây dựng bộ unit test tự động đảm bảo Validator Engine và 6 Canonical Schemas hoạt động chính xác trên toàn bộ nguồn dữ liệu.

## Phạm vi

- Tạo file unit test `tests/test_contracts.py`.
- Tạo fixture dữ liệu mẫu chuẩn từ OMS, WMS, OPS, Postgres/Odoo, MongoDB, External API.
- Test case kiểm tra:
  1. Payload hợp lệ đi qua validator thành công và được bổ sung đầy đủ metadata envelope.
  2. Payload thiếu trường bắt buộc (`business_key`, `event_time`) bị bẫy lỗi chính xác.
  3. Payload sai kiểu dữ liệu (vd: `quantity` dạng string thay vì int) bị từ chối.
  4. Cấu trúc 6 schema YAML luôn load đúng cú pháp JSON Schema.

## Kết quả mong muốn

Bộ test pytest chạy qua 100% test cases đảm bảo tính sẵn sàng cao của hệ thống hợp đồng dữ liệu.

## Kết quả triển khai

- Đã tạo entry point `tests/test_contracts.py` theo yêu cầu backlog.
- Đã tạo `tests/fixtures/contracts/multi_source_records.yaml` với 7 case đại diện cho Mock ERP PostgreSQL, Odoo, OMS, WMS, OPS, MongoDB Catalog và External API.
- Fixture phủ đủ 6 canonical entity và được đối chiếu với source profile, ownership/routing trong mapping matrix.
- Đã kiểm tra payload hợp lệ nhận đủ envelope và route tới Silver.
- Đã kiểm tra thiếu `business_key`, thiếu `event_time` và quantity sai datatype bị bắt đúng error code/path và route tới quarantine.
- Đã kiểm tra đủ 6 YAML entity schema load đúng JSON Schema Draft 2020-12 và version `1.0.0`.
- Đã bổ sung `pytest` vào development dependencies và chuyển reference resolution sang API `referencing.Registry` không deprecated.
- Chạy `pytest -q tests/test_contracts.py`: 6/6 test thành công.
- Chạy toàn bộ contract suites bằng pytest: 33/33 test thành công; toàn bộ unittest repository: 41/41 test thành công.
