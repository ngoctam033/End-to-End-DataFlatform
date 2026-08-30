---
id: BL-036.4
status: backlog
priority: P1
priority_rank: 25.4
category: business
owner: unassigned
created_at: 2026-08-28
updated_at: 2026-08-28
progress: 0
effort: M
value: high
dependencies: [BL-036.3]
tags: [odoo, delivery, stock-picking, shipment, fulfillment, sla]
target_release: null
workstream: odoo_order_fulfillment
execution_mode: parallel
parallel_with: [core_platform, data_contracts]
---

# Backlog 36.4: Odoo Delivery and Fulfillment

## Mục tiêu

Hoàn thiện luồng picking/delivery và ánh xạ `stock.picking` cùng stock moves sang canonical `shipment`.

## Phạm vi

- Thực hiện picking, packing và delivery cho order đã xác nhận.
- Lưu planned date, completion time, carrier và tracking reference.
- Chuẩn hóa trạng thái shipment và fulfillment timestamps.
- Tính dữ liệu đầu vào cho fulfillment lead time và SLA.
- Tạo case delivered, partial delivery, cancelled và delayed.
- Viết contract/integration test cho quan hệ order–shipment–inventory movement.

## Kết quả mong muốn

Một order có thể đi từ xác nhận đến giao hàng và tạo canonical shipment truy vết được về order nguồn.
