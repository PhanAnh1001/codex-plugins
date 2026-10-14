# codex-plugins/parallel-subagents

**Điều phối subagent song song** cho Codex CLI, port từ plugin Claude Code `parallel-subagents` (trước đây tên `crew`) và tổng quát hoá để mọi
dự án có thể gắn luật riêng của mình. Plugin điều phối nhiều subagent `hand` chạy song song: phiên Codex gốc
là **brain** (bộ điều phối) chia việc thành các brief có giới hạn, giao cho các hand chạy đồng thời, rồi
review và tổng hợp kết quả; mỗi hand (worker subagent) thực thi đúng một brief và trả về báo cáo kèm bằng
chứng.

## Cấu trúc thư mục

```
.agents/plugins/marketplace.json                     marketplace local "parallel-subagents-local" (gốc = codex-plugins/parallel-subagents/)
plugins/parallel-subagents/
  .codex-plugin/plugin.json                          manifest của plugin
  hooks/hooks.json                                   hook SessionStart / UserPromptSubmit / SubagentStart
  scripts/subagents_policy.py                        sinh context cho hook; đọc <repo>/.codex/subagents.md
  scripts/install_hand.py                            chép agents/hand.toml vào một thư mục agents
  agents/hand.toml                                   định nghĩa custom agent `hand`
  templates/hand-brief.md                            khuôn brief (GOAL ... RETURN)
  skills/parallel-subagents/SKILL.md                 policy đầy đủ dưới dạng skill (dự phòng khi hook bị tắt)
  skills/parallel-subagents/agents/openai.yaml       metadata hiển thị của skill
examples/small-sequential/.codex/subagents.md        chạy tuần tự, không bắt buộc test đỏ trước
examples/test-first-bugfix/.codex/subagents.md       chạy song song, quy trình sửa lỗi bắt buộc test đỏ trước khi sửa
```

## Cài đặt (người dùng tự chạy)

```sh
codex plugin marketplace add ~/app/codex-plugins/parallel-subagents      # đăng ký marketplace "parallel-subagents-local"
codex plugin add parallel-subagents@parallel-subagents-local
python3 ~/app/codex-plugins/parallel-subagents/plugins/parallel-subagents/scripts/install_hand.py   # -> ~/.codex/agents/hand.toml
#   hoặc theo dự án: install_hand.py --project /path/to/repo   # -> repo/.codex/agents/hand.toml
```

Sau đó kiểm tra `[features] hooks = true` và `multi_agent = true` (cả hai mặc định `stable`/`true` theo
`codex features list`, codex-cli 0.150.1), mở phiên mới và trust các hook của plugin bằng `/hooks`.
`install_hand.py` từ chối ghi đè một `hand.toml` có nội dung khác (plugin brain-hand cũ có thể đã cài một
file như vậy); chỉ truyền `--force` khi bạn thật sự muốn thay nó.

## Cấu hình theo dự án: `.codex/subagents.md`

Không bắt buộc. Phần front matter gồm các dòng `key: value` nằm giữa hai dòng `---` (dòng bắt đầu bằng `#`
là chú thích), tiếp theo là phần thân Markdown chứa luật dự án; phần thân được bơm nguyên văn vào brain lúc
SessionStart và vào mọi hand lúc SubagentStart. File được đọc theo `cwd` trong payload của hook.

| khoá | giá trị | mặc định |
|---|---|---|
| `language` | văn bản tự do, ngôn ngữ báo cáo của hand | `Vietnamese` |
| `instruction_files` | danh sách phân tách bằng dấu phẩy | `AGENTS.md` |
| `parallelism` | `parallel` \| `sequential` (hand chạy song song hay lần lượt) | `parallel` |
| `bug_workflow` | `standard` \| `red-test-first` (quy trình sửa lỗi riêng của dự án) | `standard` |
| `verify` | mỗi dòng một lệnh, lặp lại được | không có |

Giá trị sai và khoá lạ được quay về mặc định, đồng thời hiện thành dòng `[parallel-subagents config warning]` trong
context được bơm. Không có file thì dùng toàn bộ mặc định. File không đọc được hoặc không phải UTF-8 cũng
quay về mặc định kèm cảnh báo; hook không bao giờ crash.

**Giữ phần thân luật ngắn (nên dưới khoảng 1000 ký tự).** Codex đẩy phần output hook vượt
`additionalContextLimit` ra đĩa (2500 / 1200 / 2500 cho SessionStart / UserPromptSubmit / SubagentStart trong
`hooks/hooks.json`, được sao lại trong `CONTEXT_LIMITS` của `subagents_policy.py` - phải giữ hai nơi khớp nhau).
Khi context ghép lại vượt giới hạn, script thay phần thân luật bằng một dòng -
`Project rules are too long to inline (N chars); read <absolute path to subagents.md> in full before starting.` -
nhưng vẫn bơm các thiết lập trong front matter. Giới hạn của Codex tính theo token, còn script so theo ký
tự, nên cách so này chặt hơn mức cần.

## Ánh xạ plugin Claude Code -> Codex

| thành phần Claude Code | tương đương trong Codex | trạng thái |
|---|---|---|
| `.claude-plugin/plugin.json` | `.codex-plugin/plugin.json` | port được |
| `agents/hand.md` (subagent) | custom agent `agents/hand.toml` | thay thế: manifest plugin không có trường agents được tài liệu hoá, nên `install_hand.py` chép file vào `~/.codex/agents/` hoặc `.codex/agents/` |
| `disallowedTools: Agent` của hand | chỉ dẫn "never spawn agents" trong `developer_instructions` | thay thế (chưa xác minh được danh sách cấm tool cho custom agent) |
| `model` / `effort` ghim cho hand | để trống; kế thừa `[agents].default_subagent_model` / `default_subagent_reasoning_effort` | thay thế |
| hook SessionStart (khuôn brief + luật tiếp việc + luật review) | hook SessionStart, `subagents_policy.py session-start` | port được |
| hook UserPromptSubmit (policy điều phối ngắn) | hook UserPromptSubmit, `subagents_policy.py user-prompt` | port được, bỏ qua lượt của hand (xem mục chưa xác minh) |
| "hand không nhận hook, phải chép luật vào brief" | hook SubagentStart bơm `.codex/subagents.md` vào từng hand | cải thiện |
| `templates/hand-brief.md` | cùng file, viết bằng tiếng Anh | port được |
| Tiếp việc qua `SendMessage` | gửi tin cho agent đã xong | chưa xác minh trong Codex; policy dự phòng bằng hand mới với phát hiện cũ đưa vào CONTEXT |
| Luật riêng của Bash (không `cd` trong lệnh ghép, `run_in_background`) | tổng quát thành "không viết vòng chờ không có trần"; luật `cd` là đặc thù bộ kiểm tra quyền của Claude Code | bỏ / dự án nào cần thì đưa vào `.codex/subagents.md` |
| Đặc thù tcp-assistant (tiếng Việt, `## Mandatory Bug Investigation...`) | `language`, `bug_workflow`, phần thân luật | chuyển thành cấu hình được |
| (không có) | `skills/parallel-subagents/SKILL.md` | thêm mới: policy đầy đủ, dùng được khi hook chưa trust hoặc bị tắt |

## Nguồn xác minh định dạng Codex

- `codex --version` -> `codex-cli 0.150.1`; `codex plugin --help` (add/list/marketplace/remove);
  `codex plugin marketplace add --help` (chấp nhận đường dẫn local); `codex features list` (`hooks`, `plugins`,
  `multi_agent` stable/true; cờ `plugin_hooks` đã bị gỡ).
- Một plugin local đang chạy được: `~/.codex/plugins/cache/personal/brain-hand/*/` (`.codex-plugin/plugin.json`
  có `skills`, `interface`; `hooks/hooks.json` có `${PLUGIN_ROOT}`, `statusMessage`, `additionalContextLimit`;
  `skills/*/agents/openai.yaml`), marketplace của nó `~/.agents/plugins/marketplace.json`, và
  `~/.codex/config.toml` (`[plugins."brain-hand@personal"]`, `[hooks.state.*] trusted_hash`).
- https://developers.openai.com/codex/plugins/build : bắt buộc `name`, `version`, `description`;
  marketplace ở `<root>/.agents/plugins/marketplace.json` với `name`, `source.path` (tương đối, bắt đầu bằng `./`),
  `policy.installation`, `policy.authentication`, `category`; không nhắc tới việc đóng gói agent.
- https://learn.chatgpt.com/docs/hooks (đích chuyển hướng của developers.openai.com/codex/hooks): các sự kiện
  gồm `SessionStart`, `UserPromptSubmit`, `SubagentStart`; stdin có `session_id`, `cwd`, `hook_event_name`, `model`;
  `hookSpecificOutput.additionalContext`; biến môi trường `PLUGIN_ROOT`; hook phải được trust qua `/hooks`.
- https://learn.chatgpt.com/docs/agent-configuration/subagents : agent đặt ở `~/.codex/agents/` hoặc
  `.codex/agents/`, bắt buộc `name`, `description`, `developer_instructions`; các khoá `[agents]`.

## Chưa xác minh

- Khoá stdin cho biết vai trò agent (`agent_type`?) ở UserPromptSubmit/SubagentStart; script kiểm
  `agent_type`, `agent_name`, `subagent_type`. Nếu Codex không gửi khoá nào, lượt của hand cũng sẽ nhận
  policy của brain ở UserPromptSubmit.
- Việc lọc theo vai trò ở SubagentStart dựa vào cùng khoá chưa xác minh đó: subagent có vai trò xác định và
  khác `hand` (ví dụ explorer dựng sẵn) không được bơm; khi không có khoá vai trò, context của hand vẫn được
  bơm (fail-safe), nên khi đó subagent không phải hand cũng có thể nhận.
- SessionStart của Codex có hỗ trợ `matcher` (startup/resume/compact) hay không; plugin không dùng matcher.
- Bố cục "portable" (`plugin.json` ở gốc + `extensions.com.openai`) trong tài liệu có chạy trên 0.150.1 hay
  không; plugin này dùng `.codex-plugin/plugin.json`, đúng bố cục của plugin brain-hand đang chạy trên máy.
- Gửi tin nhắn tiếp việc cho một hand đã xong.
- Chưa cài thử vào một `CODEX_HOME` tạm (sandbox từ chối lệnh); việc kiểm chứng gồm parse JSON, parse TOML
  của `hand.toml`, và chạy script hook với payload mẫu.
