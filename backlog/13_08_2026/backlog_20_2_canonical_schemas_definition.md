---
id: BL-020.2
status: done
priority: P1
priority_rank: 20.2
category: platform
owner: unassigned
created_at: 2026-08-16
updated_at: 2026-08-28
progress: 100
effort: M
value: high
dependencies: [BL-020.1]
tags: [data-contract, canonical-model, yaml-schema, core-entities]
target_release: null
---

# Backlog 20.2: Canonical Schemas Definition for 6 Core Entities

## Mục tiêu

Xây dựng các file YAML JSON Schema chính thức cho 6 thực thể dữ liệu cốt lõi của nền tảng.

## Phạm vi

- Định nghĩa YAML Schema tương thích JSON Schema Draft 2020-12 cho:
  1. `order.yaml` (Thông tin đơn hàng, tổng tiền, trạng thái, kênh bán)
  2. `order_line.yaml` (Chi tiết dòng hàng, số lượng, đơn giá, lô date FMCG)
  3. `inventory.yaml` (Tồn kho theo kho/vị trí, SKU, khả dụng, giữ chỗ)
  4. `shipment.yaml` (Vận chuyển, đối tác logistics, mã vận đơn, lead time)
  5. `return.yaml` (Hàng hoàn, lý do hoàn, số lượng, tiền hoàn)
  6. `payment.yaml` (Thanh toán, phương thức, mã giao dịch, trạng thái)
- Đặt các file schema tại thư mục `contracts/schemas/`.

## Kết quả mong muốn

Có bộ 6 hợp đồng dữ liệu dạng YAML schema chuẩn xác làm nền tảng kiểm tra dữ liệu đầu vào.

## Kết quả triển khai

- Đã tạo 6 schema tại `contracts/schemas/` và schema dùng chung cho metadata envelope.
- Đã tạo fixture hợp lệ đại diện cho cả 6 entity.
- Đã bổ sung test Draft 2020-12, `$ref`, required fields, datatype, enum, UTC timestamp, schema drift và contract version.
- Chạy `python -m unittest -v tests.test_contract_schemas`: 8 test thành công.
