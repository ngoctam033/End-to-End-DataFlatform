---
id: BL-036.6
status: backlog
priority: P2
priority_rank: 25.6
category: business
owner: unassigned
created_at: 2026-08-28
updated_at: 2026-08-28
progress: 0
effort: M
value: high
dependencies: [BL-036.5]
tags: [odoo, return, refund, credit-note, reverse-logistics]
target_release: null
workstream: odoo_order_fulfillment
execution_mode: parallel
parallel_with: [core_platform, data_contracts]
---

# Backlog 36.6: Odoo Return and Refund

## Mục tiêu

Mô hình hóa reverse logistics từ hàng trả về đến restock/scrap và refund.

## Phạm vi

- Tạo return picking liên kết shipment và order gốc.
- Ghi nhận return reason, returned quantity và disposition.
- Hỗ trợ restock hoặc scrap theo tình trạng hàng.
- Tạo credit note/refund và liên kết payment gốc.
- Ánh xạ dữ liệu sang canonical `return` và cập nhật inventory liên quan.
- Kiểm thử partial return, multiple returns và không cho trả vượt số lượng đã bán.

## Kết quả mong muốn

Vòng đời order được khép kín đến return/refund, có thể truy vết và phân tích nguyên nhân hoàn hàng.
