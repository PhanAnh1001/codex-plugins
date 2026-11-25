# Startup skill — 0.2.1

Hook `SessionStart` nạp đầy đủ `skills/hybrid-hands/SKILL.md` vào
`hookSpecificOutput.additionalContext` khi `source` là `startup` hoặc `resume`.
Đường dẫn skill resolve từ `__file__` của script trong plugin cache, không từ
cwd; context ghi đường dẫn tuyệt đối để giải relative link. Không gọi core,
không gọi Claude Skill/Agent API, không đổi profile hoặc agent registration.
Skill không tự cho phép delegation hay cài runtime.

Manifest khai báo `hooks: ./hooks/hooks.json`; hook dùng `${PLUGIN_ROOT}`,
Python 3 và giới hạn 16000 ký tự. Test kiểm context chứa nguyên skill và còn
nằm trong giới hạn. Payload sai, sự kiện/source khác, metadata subagent rõ ràng
và skill không đọc được trả `{}`/exit 0; lỗi đọc ghi tên loại lỗi vào stderr.
Không đọc transcript hay credential. Không thêm hook vào home global.

## Contract đã đọc — 2026-11-17

Binary local báo `codex-cli 0.169.0`, package metadata cũng là `0.169.0`.
Đối chiếu nguồn chính thức đúng tag `rust-v0.169.0`:

- [session_start.rs](https://github.com/openai/codex/blob/rust-v0.169.0/codex-rs/hooks/src/events/session_start.rs):
  source startup/resume/clear/compact/fork; subagent dispatch `SubagentStart`
  riêng. Plugin chỉ đăng ký SessionStart startup/resume.
- [schema.rs](https://github.com/openai/codex/blob/rust-v0.169.0/codex-rs/hooks/src/schema.rs)
  và [output JSON schema](https://github.com/openai/codex/blob/rust-v0.169.0/codex-rs/hooks/schema/generated/session-start.command.output.schema.json):
  input snake_case, output camelCase. SessionStart input không có trường
  agent_type; guard metadata là phòng vệ cho adapter, không giả định runtime
  truyền trường đó.
- [manifest.rs](https://github.com/openai/codex/blob/rust-v0.169.0/codex-rs/core-plugins/src/manifest.rs)
  hỗ trợ đường dẫn hooks;
  [protocol hooks.rs](https://github.com/openai/codex/blob/rust-v0.169.0/codex-rs/protocol/src/hooks.rs)
  định nghĩa timeout/statusMessage/additionalContextLimit.
- Mẫu local `parallel-subagents/plugins/parallel-subagents/hooks/hooks.json`
  được đọc để tái dùng cấu trúc command và `${PLUGIN_ROOT}`; không sửa plugin đó.

## Social listening

Luật áp dụng: “Bạn quản lý source code repo này, khi đưa ra một giải pháp hoặc workflow cần tham khảo thêm nguồn social listening về lĩnh vực, quy trình đó.”

- [Codex #54353](https://github.com/openai/codex/issues/54353), 2026-10-15,
  đã đọc nội dung ngày 2026-11-17: báo CLI chạy SessionStart
  còn app-server bỏ qua. Đây là báo cáo cộng đồng chưa kiểm chứng tại đây.
- [Codex #35863](https://github.com/openai/codex/issues/35863), 2026-07-29,
  đã đọc nội dung ngày 2026-11-17: Desktop discovery không
  bảo đảm execution. Đây là báo cáo cộng đồng chưa kiểm chứng tại đây.

Ngày đối chiếu 2026-11-17. Vì vậy parse manifest/skill discovery không được
coi là hook đã thực thi; phải kiểm ở phiên mới của đúng CLI/Desktop đang dùng.

## Kiểm chứng và giới hạn

Test subprocess chạy script từ cwd `/`, kiểm startup/resume chứa nguyên skill,
payload malformed/non-object, event/source khác, metadata hand/subagent và
missing skill. Output được đối chiếu JSON schema chính thức của tag 0.169.0.
Profile bridge và generator tests tiếp tục chạy trong bộ test hiện có.

Không cài plugin hoặc đổi home config trong phần triển khai này. Sau refresh
release 0.2.1 bằng CLI add ở home đã duyệt, mở phiên mới/resume và kiểm context
thực tế. Chưa có evidence execution trong Codex Desktop hoặc phiên đang mở.

Kết quả: pytest 25 passed, 29 subtests passed; JSON schema output PASS cho
startup, resume, malformed và hand; context đầy đủ 5583 ký tự dưới limit
16000. Lần unittest bằng Python hệ thống không import được pytest; kiểm
lại toàn bộ bằng venv tạm có pytest đã đạt.
