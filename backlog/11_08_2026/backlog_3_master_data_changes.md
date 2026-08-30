---
id: BL-003
status: backlog
priority: P2
priority_rank: 230
category: analytics
owner: unassigned
created_at: 2026-08-11
updated_at: 2026-08-13
progress: 0
effort: M
value: medium
dependencies: [BL-015]
tags: [master-data, scd, testing]
target_release: null
---

# Backlog 3: Master Data Changes/SCD Scenario

Ngay ghi nhan: 11/08/2026
Trang thai: backlog, chua trien khai

## Muc tieu

Tai hien thay doi thuc te cua master data theo thoi gian, phuc vu hoc va kiem thu Slowly Changing Dimension.

## Kich ban du kien

Can thiet ke mot kich ban co moc thoi gian chinh xac:

1. Tao ban ghi master data ban dau.
2. Phat sinh giao dich truoc khi thay doi.
3. Cap nhat mot thuoc tinh nghiep vu.
4. Phat sinh giao dich sau khi thay doi.
5. Ngung hieu luc hoac thay the ban ghi neu phu hop.

## Loai thay doi can xac dinh

- Type 1: cap nhat truc tiep, khong luu lich su.
- Type 2: luu phien ban lich su voi `valid_from`, `valid_to`, `is_current`.

## Doi tuong co the dung lam vi du

- Customer thay doi segment.
- Product thay doi category hoac brand.
- Branch thay doi khu vuc phu trach.
- Sales channel thay doi ten hien thi hoac nhom kenh.

## Ket qua mong muon

Co the truy van dung thong tin master data tai thoi diem phat sinh giao dich va kiem thu logic SCD Type 2 mot cach on dinh.

## Ghi chu

Hang muc nay can di kem tai lieu kich ban va bo test de dam bao ket qua co the tai hien chinh xac.
