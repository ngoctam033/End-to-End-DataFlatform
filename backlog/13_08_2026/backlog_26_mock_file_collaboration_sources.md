---
id: BL-026
status: backlog
priority: P3
priority_rank: 180
category: platform
owner: unassigned
created_at: 2026-08-15
updated_at: 2026-08-15
progress: 0
effort: L
value: medium
dependencies: [BL-011, BL-020, BL-025]
tags: [mock, sharepoint, google-drive, files, csv, excel]
target_release: null
---

# Backlog 26: Mock SharePoint and Google Drive Sources

## Muc tieu

Mo phong nguon file va tai lieu chia se cho cac quy trinh bao cao dang lam thu cong.

## Pham vi

- Tao local object/file source co cau truc tuong tu SharePoint va Google Drive.
- Ho tro CSV, Excel, JSON va file version.
- Theo doi file moi, file thay doi va file bi xoa.
- Kiem tra schema, encoding, duplicate file va malformed file.
- Dua file raw vao MinIO va ghi metadata ingestion.

## Ket qua mong muon

Co the kiem thu ingestion file-based va tien toi adapter that ma khong doi pipeline core.
