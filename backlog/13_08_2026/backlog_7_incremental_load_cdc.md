# Backlog 7: Incremental Load/CDC

Ngay ghi nhan: 13/08/2026
Trang thai: backlog, chua trien khai

## Muc tieu

Thay the full-refresh bang incremental load hoac CDC de chi xu ly du lieu moi va du lieu da thay doi.

## Pham vi du kien

- Xac dinh watermark theo `updated_at`, transaction time hoac log sequence.
- Xu ly insert, update, delete va late-arriving data.
- Dam bao idempotency khi pipeline chay lai.
- Ghi nhan batch/run metadata.

## Ket qua mong muon

Pipeline nhanh hon, khong can tao lai toan bo bang va co the phuc vu du lieu lon.
