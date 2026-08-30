---
id: BL-030
status: done
priority: P1
priority_rank: 30
category: reliability
owner: unassigned
created_at: 2026-08-16
updated_at: 2026-08-30
progress: 100
effort: L
value: high
dependencies: [BL-020.5]
tags: [source-validation, business-rules, data-quality, quarantine, testing]
target_release: null
---

# Backlog 30: Source Business Rule Validation

## Muc tieu

Kiem tra logic nghiep vu ngay tai source/ingestion boundary de ngan du lieu sai di tiep vao raw, staging va analytics layer.

## Pham vi

- Dinh nghia business rules cho order, order line, payment, inventory, shipment va return.
- Kiem tra trang thai hop le va state transition cua order/shipment/payment.
- Kiem tra cong thuc so tien: gross, discount, net, invoice, payment va refund.
- Kiem tra ton kho, stock movement, so luong xuat/nhap va khong cho gia tri am khong hop le.
- Kiem tra quan he giua source key, business key va cac entity lien quan.
- Kiem tra moc thoi gian: order, shipment, delivery, payment, return va SLA.
- Phan loai record thanh accepted, rejected hoac quarantined.
- Luu validation error code, error message, source system, source record key va validation time.
- Tao bo test cho record hop le, record sai va cac truong hop bien.

## Nguyen tac xu ly loi

- Loi nghiem trong khong duoc ghi vao canonical/raw accepted dataset.
- Record loi phai duoc luu vao quarantine/dead-letter area de dieu tra va replay.
- Validation phai deterministic va co the chay lai ma khong tao duplicate.
- Business rule phai co version de theo doi thay doi theo thoi gian.

## Ket qua mong muon

Du lieu sai nghiep vu duoc phat hien truoc khi vao cac tang downstream, co the truy vet ly do va tai xu ly sau khi duoc sua.

## Kết quả triển khai

- Đã tạo rule catalog có version tại `contracts/rules/business_rules.yaml`.
- Đã tạo `SourceBusinessRuleValidator` cho order, order line, inventory, shipment, payment và return.
- Đã kiểm tra business-key derivation, related-entity context và state transition cho order/shipment/payment.
- Đã đối soát order/order-line/invoice/payment/refund amounts.
- Đã kiểm tra inventory balance, lot expiration và stock-movement sign/value.
- Đã kiểm tra chronology order/shipment/delivery attempt/payment/return và carrier SLA policy.
- Kết quả được phân loại `ACCEPTED`, `REJECTED` hoặc `QUARANTINED`; record không accepted đi quarantine/DLQ.
- Mỗi lỗi có code, message, path, disposition, source system, source record key, validation time và rule version.
- `validation_id` được tạo xác định từ identity của record và rule version để replay/upsert không tạo duplicate.
- Đã bổ sung context contract, hướng dẫn replay và 12 unit tests gồm valid, invalid, missing context và edge cases.
- Chạy toàn bộ suite: 45/45 pytest cases và 53/53 unittest cases thành công.
