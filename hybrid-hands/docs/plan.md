# Plan: adapter hybrid-hands cho Codex

Trạng thái: source đã triển khai, brain review và cài/discover bản 0.1.0;
native invocation của các role sinh ra chưa được kiểm chứng.
Ngày: 2026-11-16.

## Mục tiêu và phạm vi

Đóng gói workflow hybrid thành skill, custom agent và plugin Codex tại
`~/app/codex-plugins/hybrid-hands`. Core tiếp tục ở
`~/app/claude-plugins/hybrid-hands`; adapter chỉ gọi CLI bằng đường dẫn tuyệt
đối và đọc JSON. Không sao chép thư viện, bảng model/effort hay policy động.

Phiên chính chỉ lập plan/spec, quyết định phạm vi, review và tổng hợp.
Executor được người dùng yêu cầu: subagent `gpt-6.1-sol`, effort `low`, fork
sạch. Không coi role mang tên `hand` là bằng chứng về model/effort thực tế.

## Evidence đã có

- Core được kiểm tra ở version 0.66.0. Contract read-only:
  `hand-ext profile --cwd REPO --json` và
  `hand-ext pick --cwd REPO --role code|collect|chrome [--tier 1|2] --json`.
- Core chưa có public CLI render policy; không gọi renderer hook nội bộ như API.
- Codex CLI 0.169.0 probe offline đã discover custom agent ở
  `$CODEX_HOME/agents/*.toml`; project `.codex/agents/*.toml` cần trusted repo.
- Skill user theo `$HOME/.agents/skills`, không theo `$CODEX_HOME`.
  Probe fixture đã xác nhận repo skill và symlink skill.
- Discovery hiển thị model/effort từ TOML nhưng còn chấp nhận effort giả;
  chưa chứng minh native invocation dùng đúng cấu hình hoặc quyền dùng model.
- Chưa kiểm chứng home thật `~/.codex-hand` và chưa cài adapter.
- Repo đích có gói mẫu `parallel-subagents`; không sửa/bật gói này.

## Giai đoạn và ownership

1. **Brain: chốt spec.** Tài liệu này và `spec.md` thuộc brain.
2. **Executor Sol 6.1 low: baseline và probe.** Kiểm model/effort thực của
   executor trước khi giao source; đọc instructions hiện hành, ghi git status,
   kiểm kê artifact có thể còn từ packet `build_bridge` đã bị ngắt. Không xoá
   hay ghi đè artifact chưa xác định ownership. Xác minh CLI cài/update chính
   thức, discovery ở đúng home và giới hạn reload. Không gọi model/API chỉ
   để probe khi chưa xác định rõ cách tính chi phí/phạm vi được phép.
3. **Executor Sol 6.1 low: CLI bridge.** Ownership duy nhất:
   `plugins/hybrid-hands/scripts/hybrid_codex.py`, `tests/test_bridge.py`.
4. **Executor Sol 6.1 low mới: package và workflow.** Ownership:
   manifest, marketplace, skill, metadata UI, README và changelog. Chỉ bắt
   đầu sau khi brain chốt interface của bridge; không sửa scripts/tests.
5. **Executor Sol 6.1 low mới: đăng ký agent.** Ownership: installer/generator
   và test của installer. Thiết kế cụ thể chỉ giao sau probe; không ghi đè
   `hand` đã có, không đổi preference profile hay account.
6. **Brain review; executor mới kiểm chứng.** Kiểm source diff và các test
   hẹp có ý nghĩa. Đọc lại model/effort và đường dẫn/version nạp thực tế.
7. **Cài qua công cụ chính thức.** Chỉ các home/repo được xác nhận thuộc
   phạm vi dùng hybrid. Không sửa thủ công registry/settings/credential;
   không tự bật plugin ở repo khác. Ghi rõ cần phiên mới/reload nếu có.

Các packet không ghi chung file có thể chạy song song. Không giao lại cho
hand đã xong; một packet tự chứa cho mỗi hand. Chưa commit/push ở repo Codex
khi chưa có chỉ dẫn áp dụng cho việc đó.

## Kiểm chứng tối thiểu

- Bridge: fake core executable, argv/path có khoảng trắng, cwd forwarding,
  JSON sai kiểu, thiếu profile, guard exit 7, tier sai và không tự fallback.
- Installer: home đích, file ownership/collision, stale model/effort,
  không ghi ngoài phạm vi; chỉ fixtures giả.
- Manifest: parse JSON/TOML và kiểm link nội bộ; không thêm test cho prose.
- Runtime: exact home, skill/agent/plugin discovery, plugin version/path;
  tách parse/discovery khỏi native invocation trong báo cáo.
- Không chạy full suite, không suy token/USD thành quota.

## Kết quả review source

- Brain đã đọc raw source bridge và generator, đối chiếu spec: subprocess
  argv không shell, timeout hữu hạn, JSON type/role/tier checks, guard được
  giữ nguyên, generator không ghi đè `hand` hoặc file không quản lý.
- Bridge: 8 test hẹp đạt. Generator: 13 test hẹp đạt với fixtures giả.
  Manifest JSON, skill YAML/frontmatter và links nội bộ đã kiểm.
- Core thật qua bridge trả `claude-mono` tại repo `claude-plugins`; generator
  phải skip các role không phải Codex. Không đổi profile để ép tạo agent.
- Không có hooks tự inject ở bản đầu; không sửa core hoặc plugin cũ.
- Chưa chứng minh native invocation của các role `hybrid-*`; không dùng
  parse/discovery thay cho evidence này. Installation/discovery ghi riêng
  trong `verification.md`: CLI chính thức đã cài 0.1.0 ở `~/.codex` và
  `~/.codex-hand`; app-server mới discover đúng skill cache ở cả hai home,
  không lỗi. Parent session chưa được chứng minh hot reload; mở phiên mới
  hoặc reload để dùng plugin. Generator dry-run skip cả ba vai ở profile
  `claude-mono`; chưa apply và không đổi profile. Commit/push lên `main`
  là bước bàn giao đã được người dùng yêu cầu sau kiểm chứng.

## Điều kiện mở lại triển khai

Đã hoàn thành: người dùng cho phép sửa cấu hình global; chỉ model trong
`~/.codex/agents/hand.toml` được đổi sang `gpt-6.1-sol`, effort giữ `low`, có
backup. Metadata công cụ runtime đã cập nhật đúng model/effort. Hand mới đã
kiểm tra độc lập file và metadata; không còn blocker model của executor.
Hai packet cũ đã bị ngắt; inventory xác nhận chưa có source/test bridge dở
dang. Triển khai tiếp bằng hand mới đúng role, không model override trong packet.
