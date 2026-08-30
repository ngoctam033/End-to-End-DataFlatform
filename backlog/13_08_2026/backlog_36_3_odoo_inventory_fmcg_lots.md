---
id: BL-036.3
status: backlog
priority: P1
priority_rank: 25.3
category: business
owner: unassigned
created_at: 2026-08-28
updated_at: 2026-08-28
progress: 0
effort: M
value: high
dependencies: [BL-036.2]
tags: [odoo, inventory, reservation, lot, expiration, fmcg]
target_release: null
workstream: odoo_order_fulfillment
execution_mode: parallel
parallel_with: [core_platform, data_contracts]
---

# Backlog 36.3: Odoo Inventory, FMCG Lots and Expiration

## Mục tiêu

Mô hình hóa tồn kho FMCG, reservation và lot expiration trong Odoo, đồng thời tạo canonical inventory records.

## Phạm vi

- Khởi tạo tồn kho theo warehouse/location, product và lot.
- Quản lý manufacturing/expiration date cho lot.
- Xác minh reservation khi xác nhận order và release khi hủy.
- Ánh xạ stock quantity, reservation và movement sang canonical `inventory`.
- Tạo case đủ hàng, thiếu hàng, gần hết hạn và hết hạn.
- Kiểm thử chống overselling và tính nhất quán số lượng.

## Kết quả mong muốn

Odoo cung cấp dữ liệu tồn kho và lot có thể dùng để kiểm thử availability, reservation và cảnh báo hạn sử dụng.
