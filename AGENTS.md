# AI Agent Rules

## Authority

- Được đọc, phân tích, review và cập nhật tài liệu, backlog, roadmap, runbook, cấu hình, fixture và test.
- Không tự sửa production business logic, business rule, KPI, mapping, state transition hoặc migration làm thay đổi ý nghĩa nghiệp vụ.
- Với production business logic: phân tích tác động, đề xuất snippet/patch và chờ người dùng phê duyệt trước khi ghi vào source code.
- Không tự commit nếu người dùng chưa yêu cầu.
- Bảo toàn thay đổi hiện có, không chỉnh file ngoài phạm vi và tránh destructive actions.

## Evidence

- Chỉ kết luận hoàn thành hoặc ổn định khi có bằng chứng từ metadata, acceptance criteria, test, log, healthcheck hoặc commit.
- Không tự đóng backlog chỉ dựa trên nội dung tài liệu.
- Test phải tái lập được; không dùng credential, PII hoặc dữ liệu production nhạy cảm.

## Project management

- Khi tạo, tách, cập nhật, thống kê, ưu tiên, lập lịch, review, đóng hoặc chuẩn bị commit backlog, phải dùng skill `$manage-project-backlog`.
- Metadata schema và quy ước cơ bản nằm trong `backlog/README.md`; không sao chép workflow backlog vào file này.
