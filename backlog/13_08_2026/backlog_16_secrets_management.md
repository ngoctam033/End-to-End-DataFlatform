---
id: BL-016
status: done
priority: P0
priority_rank: 10
category: platform
owner: unassigned
created_at: 2026-08-13
updated_at: 2026-08-16
progress: 100
effort: S
value: high
dependencies: []
tags: [security, secrets, credentials, docker]
target_release: null
---

# Backlog 16: Secrets Management

Ngay ghi nhan: 13/08/2026
Trang thai: done, da hoan thanh

## Muc tieu

Loai bo credential hard-code khoi Docker Compose, source code va tai lieu cong khai.

## Pham vi du kien

- Dua database credentials vao `.env` local khong commit.
- Bo sung `.env.example` voi gia tri mau.
- Tach secret theo service va moi truong.
- Nghien cuu Docker secrets hoac secret manager cho deployment.

## Ket qua mong muon

Credential duoc quan ly an toan va co the thay doi ma khong sua code.
