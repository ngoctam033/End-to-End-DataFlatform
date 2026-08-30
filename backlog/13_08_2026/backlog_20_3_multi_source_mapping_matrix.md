---
id: BL-020.3
status: done
priority: P1
priority_rank: 20.3
category: platform
owner: unassigned
created_at: 2026-08-16
updated_at: 2026-08-28
progress: 100
effort: M
value: high
dependencies: [BL-020.2]
tags: [data-contract, mapping-matrix, source-systems, canonical-model]
target_release: null
---

# Backlog 20.3: Multi-Source Mapping Matrix

## Mục tiêu

Xây dựng ma trận ánh xạ dữ liệu từ các hệ thống nguồn đa dạng (OMS, WMS, OPS, PostgreSQL/Odoo, MongoDB, External API) về Canonical Data Model.

## Phạm vi

- Ánh xạ trường nguồn (Source Fields) sang trường chuẩn (Canonical Fields) cho cả 6 entities.
- Xử lý chuyển đổi kiểu dữ liệu (Timestamp format, Enum mapping, Nullable rules).
- Xác định quy tắc tạo `business_key` cho từng nguồn (ví dụ: `OMS-ORD-{id}`, `POS-{id}`).
- Tạo tài liệu `docs/data_contracts/03_source_mapping_matrix.md`.

## Kết quả mong muốn

Nhà phát triển ingestion pipeline có tài liệu hướng dẫn chuyển đổi rõ ràng từ bất kỳ source system nào về canonical model.

## Kết quả triển khai

- Đã tạo tài liệu `docs/data_contracts/03_source_mapping_matrix.md` cho 6 entity và 7 source profile.
- Đã tạo ma trận máy đọc `contracts/mappings/source_mapping_matrix.yaml` phiên bản `1.0.0`.
- Mapping `mock_erp_pg` dùng table/column thật và phủ toàn bộ canonical payload fields.
- Các nguồn chưa triển khai được đánh dấu `contract_only`, có ownership, logical interface và điều kiện chuyển sang `implemented`; không trình bày giả định như connector đang hoạt động.
- Đã định nghĩa conversion, nullable, enum, business key, grain, deduplication, quarantine và error code.
- Đã bổ sung consistency tests đối chiếu ma trận với canonical schema và source DDL.
- Chạy `python -m unittest -v tests.test_source_mapping_matrix`: 9 test thành công.
