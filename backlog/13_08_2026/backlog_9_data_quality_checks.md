---
id: BL-009
status: backlog
priority: P1
priority_rank: 60
category: reliability
owner: unassigned
created_at: 2026-08-13
updated_at: 2026-08-13
progress: 0
effort: M
value: high
dependencies: [BL-008]
tags: [data-quality, validation, testing]
target_release: null
---

# Backlog 9: Data Quality Checks

Ngay ghi nhan: 13/08/2026
Trang thai: backlog, chua trien khai

## Muc tieu

Phat hien du lieu loi truoc khi ghi vao analytics marts hoac phuc vu dashboard.

## Pham vi du kien

- Kiem tra not-null, uniqueness va referential integrity.
- Kiem tra schema drift va data type.
- Kiem tra so luong ban ghi, freshness va duplicate.
- Kiem tra business rules cho don hang, thanh toan, ton kho va shipment.

## Ket qua mong muon

Pipeline fail co kiem soat khi du lieu khong dat chat luong va luu duoc ket qua kiem tra.
