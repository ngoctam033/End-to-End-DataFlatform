---
id: BL-036.5
status: backlog
priority: P1
priority_rank: 25.5
category: business
owner: unassigned
created_at: 2026-08-28
updated_at: 2026-08-28
progress: 0
effort: M
value: high
dependencies: [BL-036.4]
tags: [odoo, invoice, payment, reconciliation, order-to-cash]
target_release: null
workstream: odoo_order_fulfillment
execution_mode: parallel
parallel_with: [core_platform, data_contracts]
---

# Backlog 36.5: Odoo Invoice and Payment

## Mục tiêu

Nối sales fulfillment với invoice, payment và reconciliation để hoàn thiện happy path Order-to-Cash.

## Phạm vi

- Tạo/post customer invoice từ sales order.
- Đăng ký full payment và partial payment.
- Theo dõi invoice status, outstanding amount và payment method.
- Ánh xạ `account.payment` và quan hệ reconciliation sang canonical `payment`.
- Kiểm tra gross, discount, tax, net, invoiced và paid amount.
- Viết test cho unpaid, partial, paid và overpayment rejection.

## Kết quả mong muốn

Pipeline có thể đối soát order, invoice và payment từ Odoo với số tiền và trạng thái nhất quán.
