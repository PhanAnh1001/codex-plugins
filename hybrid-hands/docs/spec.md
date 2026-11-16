# Spec: adapter hybrid-hands cho Codex

Ngày: 2026-11-16. Trạng thái: thiết kế cho executor; chưa là chứng nhận runtime.

## Contract sản phẩm

Người dùng có thể cài plugin Codex, gọi skill hybrid-hands và sử dụng executor
được đăng ký, trong khi core hiện có vẫn quyết định profile, provider,
account, model, effort và điều kiện native/guard. Adapter không quyết định
backend thay core và không tự đặt profile.

Các thành phần:

- `AGENTS.md` của repo làm việc giữ luật nền luôn áp dụng.
- Skill giữ workflow lấy profile, pick, giao packet, kiểm capability và review.
- Agent TOML giữ giới hạn executor, luật dữ liệu và cấu hình đã resolve.
- Plugin quản lý metadata, distribution và version.

Skill được nạp theo discovery/invocation, không thay toàn bộ luật nền bằng
một workflow chỉ được đọc khi được chọn. Không giả định file agent đặt trong
plugin sẽ tự được đăng ký.

## Bố trí nguồn

```text
hybrid-hands/
  docs/{plan,spec}.md
  .agents/plugins/marketplace.json
  plugins/hybrid-hands/
    .codex-plugin/plugin.json
    skills/hybrid-hands/SKILL.md
    skills/hybrid-hands/agents/openai.yaml
    scripts/hybrid_codex.py
  tests/test_bridge.py
  README.md
  CHANGELOG.md
```

CLI 0.169.0 đã được probe với fixture: dùng compatibility manifest
`.codex-plugin/plugin.json`; root-only portable manifest chưa cài được trên
binary này. Marketplace tên `hybrid-hands-local`, đăng ký package root
`hybrid-hands`, source path `./plugins/hybrid-hands`. Release 0.1.0 không
inject hook tự động. Không thay gói `parallel-subagents` hiện có.

## Interface bridge

```text
hybrid_codex.py profile --cwd ABS_REPO [--core-cli ABS_EXE]
hybrid_codex.py pick --cwd ABS_REPO --role code|collect|chrome
                     [--tier 1|2] [--core-cli ABS_EXE]
```

Resolve core theo thứ tự: cờ rõ ràng, biến đường dẫn
`HYBRID_HANDS_CORE_CLI`, rồi source checkout mặc định
`~/app/claude-plugins/hybrid-hands/plugins/hybrid-hands/bin/hand-ext`.
Phải chuyển thành đường dẫn tuyệt đối tới executable tồn tại; không import
core Python hay dùng PATH fallback. Không claim source path là plugin cache
đã được nạp.

Bridge gọi subprocess bằng argv, không shell; cwd tường minh, timeout hữu
hạn. Chỉ gọi hai CLI JSON đã xác minh. Không gọi run, usage hay auth commands.

`profile` cần profile thuộc `claude-mono|gpt-mono|hybrid`, `roles` là object.
`pick` cần các field `profile`, `role`, `tier`, `provider`, `account`, `model`,
`effort`, `backend`, `native`, `native_reason`, `guard_blocked`. Hai field
boolean phải là boolean thật. Chấp nhận field bổ sung. Không hardcode model
hay effort mặc định. Tier chỉ hợp lệ cho collect/chrome.

Giữ JSON hợp lệ và exit status core, gồm exit 7. Lỗi adapter trả thông báo
tối giản; không dump stderr/payload không tin cậy có thể chứa secret. Không
chuyển lỗi guard thành success, không tự thử backend khác.

## Contract workflow và agent

Trước mỗi lần giao việc: lấy profile và pick cho đúng cwd/vai/tier. Native
chỉ được dùng khi pick cho phép, account/capability đúng và role agent được
nạp có model/effort đúng với kết quả pick hiện tại. Không dùng tên role
thay cho chứng cứ cấu hình. Native Codex fork sạch; packet không chứa
model/effort override và không mang context thừa.

Nếu chưa chứng minh native capability hoặc cấu hình đã stale: không spawn
native, báo điều kiện thiếu và chỉ dùng tuyến external mà core cho phép.
Không suy native invocation từ việc parser chấp nhận TOML. Guard blocked
phải được giữ nguyên. Không nâng effort, đổi account hay profile để né lỗi.

Agent mới không ghi đè `hand` hoặc agent người dùng đang có. Scope và naming
cụ thể: generator `scripts/install_agents.py` đọc `profile.roles` cho code,
collect.1 và collect.2; chỉ sinh entry có provider Codex, lần lượt tên
`hybrid-code`, `hybrid-collect-1`, `hybrid-collect-2`. Model/effort/account
lấy từ core, không duy trì bảng model riêng. Generation không phải xác nhận
native eligibility: caller vẫn phải chạy pick và kiểm metadata trước spawn.

Generator dry-run mặc định, chỉ ghi khi `--apply`. Target home theo cờ
`--codex-home`, rồi `CODEX_HOME`, rồi `~/.codex`. Mọi destination phải được
preflight trước ghi: từ chối symlink hoặc file không có ownership marker của
adapter. File managed đã đổi cần backup và atomic replace, mode 0600; file
không đổi là no-op. Không ghi registry/config.toml. Thay đổi profile phải
làm rõ cấu hình stale và yêu cầu nạp lại nếu runtime không hot reload.

## Luật dữ liệu phải có trong brief/agent

Không in/hiện giá trị `.env`, token, credential ở bất kỳ tầng nào; công cụ của plugin (`hand-ext doctor/run`, đọc hạn mức) được đọc file auth nội bộ, chỉ không được in giá trị. Brief giao hand ngoài chép nguyên văn luật này.
Không đọc `.env` bằng lệnh hay tool hiện giá trị: `cat`, `head`, `tail`, `grep`, `sed`, `awk`, `less`, `more`, `rg`, `Read`, kể cả có che phần sau dấu `=`.
Không đọc hay in token, auth.json, file credential. Không giao hand ngoài việc cần secret hay dữ liệu khách hàng. Chỉ dùng code và fixtures giả công khai được; không đọc transcript/log thật. Không gọi API trả phí, không tạo hay dùng API key.

## Acceptance và bàn giao

Phải báo riêng: code/test đã qua, discovery đã qua, native invocation đã
qua hay chưa, plugin đã cài vào home nào, version/path nào được nạp và cần
reload hay không. Không coi JSON/TOML parse là runtime verification.

Executor trả raw evidence tiếng Việt: file thay đổi, command/exit/result,
giả định, phần chưa kiểm chứng và ngoài phạm vi. Không spawn/delegate,
không giao tiếp phiên khác, không tự mở rộng scope hay commit/push.
