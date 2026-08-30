# Backlog metadata

Mỗi backlog sử dụng YAML front matter ở đầu file để đánh dấu, theo dõi và sắp xếp ưu tiên.

## Schema

```yaml
id: BL-001
status: backlog       # backlog | ready | in_progress | blocked | done | dropped
priority: P1          # P0 critical | P1 high | P2 medium | P3 low
priority_rank: 10    # số nhỏ hơn được ưu tiên trước
category: platform    # platform | reliability | architecture | analytics | business
owner: unassigned
created_at: 2026-08-11
updated_at: 2026-08-13
progress: 0           # phần trăm, từ 0 đến 100
effort: M             # S | M | L | XL
value: high           # low | medium | high
dependencies: []
tags: []
target_release: null
workstream: core_platform       # nhom cong viec co the lap ke hoach/doc lap
execution_mode: sequential      # sequential | parallel
parallel_with: []               # cac workstream duoc phep chay song song
```

## Quy ước

- `status` dùng để theo dõi vòng đời công việc.
- `priority` thể hiện mức độ khẩn cấp; `priority_rank` là thứ tự thực hiện toàn cục, số nhỏ hơn được ưu tiên trước.
- `effort` là ước lượng tương đối, không phải số giờ cam kết.
- `dependencies` chứa ID của backlog phụ thuộc, ví dụ `BL-007`.
- `workstream` gom các backlog cùng một luồng triển khai hoặc cùng bounded context.
- `execution_mode: parallel` cho biết backlog thuộc luồng có thể triển khai đồng thời với các luồng trong `parallel_with`; trường này không làm mất hiệu lực của `dependencies`.
- `parallel_with` chứa tên workstream, không chứa backlog ID. Các dependency trong cùng workstream vẫn phải hoàn thành theo thứ tự.
- Khi cập nhật nội dung hoặc trạng thái, cập nhật `updated_at`.
- Metadata trong từng file là nguồn thông tin chính; có thể tạo index tự động sau này.
