---
id: BL-036.2
status: backlog
priority: P1
priority_rank: 25.2
category: business
owner: unassigned
created_at: 2026-08-28
updated_at: 2026-08-28
progress: 0
effort: M
value: high
dependencies: [BL-036.1, BL-020.2]
tags: [odoo, sales-order, order-line, extraction, canonical]
target_release: null
workstream: odoo_order_fulfillment
execution_mode: parallel
parallel_with: [core_platform, data_contracts]
---

# Backlog 36.2: Odoo Sales Order and Canonical Extraction

## Mục tiêu

Triển khai happy path tạo/xác nhận sales order và ánh xạ dữ liệu Odoo sang canonical `order` và `order_line`.

## Phạm vi

- Tạo đơn hàng theo customer, channel, pricelist, order line và delivery address.
- Xác nhận order và lưu các timestamp/trạng thái cần thiết.
- Định nghĩa mapping từ `sale.order` và `sale.order.line` sang canonical contract.
- Xây extractor có checkpoint, idempotency và ingestion metadata tối thiểu.
- Tạo fixture cho order hợp lệ, bị hủy và cập nhật sau xác nhận.
- Viết contract test cho mapping và payload đầu ra.

## Kết quả mong muốn

Đơn hàng Odoo được trích xuất thành canonical `order`/`order_line` hợp lệ mà không làm lộ coupling Odoo vào schema chung.
