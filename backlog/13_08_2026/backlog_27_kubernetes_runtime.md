---
id: BL-027
status: backlog
priority: P1
priority_rank: 250
category: architecture
owner: unassigned
created_at: 2026-08-15
updated_at: 2026-08-15
progress: 0
effort: XL
value: high
dependencies: [BL-008, BL-011, BL-013, BL-016, BL-017]
tags: [kubernetes, airflow, spark, flink, helm, production]
target_release: null
---

# Backlog 27: Kubernetes Data Runtime

## Muc tieu

Chuyen cac workload du lieu tu Docker Compose sang runtime co kha nang van hanh production.

## Pham vi

- Deploy Airflow voi Kubernetes Executor.
- Deploy Spark job voi Spark Operator.
- Chuan bi Flink deployment va checkpoint storage.
- Cau hinh namespace, service account, RBAC va network policy.
- Cau hinh resource request/limit, persistent volume va secrets.
- Tao Helm chart hoac manifest co the deploy lap lai.

## Ket qua mong muon

Pipeline co the chay tren Kubernetes voi resource isolation, storage va permission ro rang.
