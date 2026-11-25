# Changelog

## 0.3.0 — 2026-11-25

- Đổi tên skill `$open-gpt-brain` thành `$new-agent-paseo`, gọi script canonical
  `new-agent-paseo`; tên cũ `$open-gpt-brain` không còn.
- Thêm bước chọn loại agent (GPT v1, Claude v1, Claude v2): chưa nói rõ thì hỏi
  người dùng; skill luôn truyền `--brain`.

## 0.2.1 — 2026-11-25

- Source-only: hand mặc định không commit/push; chỉ packet rõ ràng của brain
  cấp quyền theo repository/action/branch và remote cho push, luôn giữ luật
  ưu tiên cao hơn/runtime ban. Không cài hay reload runtime hiện tại.

- Nạp đầy đủ skill qua hook Codex SessionStart startup/resume, resolve từ plugin
  thực tế; bỏ qua payload sai và subagent, lỗi đọc skill không chặn phiên.
- Giữ profile/pick và cài agent theo luồng hiện có; không sửa hook global.
- Soạn ngày 17/11/2026 ở thư mục chính dưới tên 0.1.1, chưa commit; đưa lên trên 0.2.0 và commit ngày 25/11/2026.

## 0.2.0 — 2026-11-25

- Thêm skill `$open-gpt-brain`: gọi script canonical `open-gpt-brain` cạnh
  core `hand-ext` (không sao chép logic) để đổi profile sang gpt-mono, bật
  subagent native và mở phiên Paseo main brain (GPT sol hoặc Claude v1/v2).

## 0.1.0 — 2026-11-16

- Thêm skill `$hybrid-hands` và metadata UI cho workflow profile/pick,
  kiểm guard, capability account và model/effort runtime trước delegation.
- Thêm bridge mỏng gọi JSON core; core tiếp tục quyết định policy và routing.
- Thêm generator agent có dry-run, tên riêng và bảo vệ tên không thuộc quản lý;
  model/effort lấy từ core, không duy trì bảng riêng.
- Ghi luật brief dữ liệu và tách source, discovery, native invocation cùng
  home/version/path runtime trong bàn giao.
- Ghi contract cài local qua CLI Codex 0.169.0 với compatibility manifest,
  marketplace/add/list theo từng home và cập nhật bằng tăng version rồi add lại.
- Generator chỉ sinh row provider Codex từ profile; generation không xác nhận
  native eligibility. Release đầu không có hook tự inject; cài đặt, discovery
  và native invocation ở home thật cần evidence riêng.
