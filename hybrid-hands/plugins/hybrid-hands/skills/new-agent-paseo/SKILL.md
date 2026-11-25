---
name: new-agent-paseo
description: Đổi profile hybrid-hands của repo sang gpt-mono, bật subagent native, rồi mở phiên Paseo "main brain" ở tab mới cùng workspace (phiên độc lập, không phải subagent); chọn loại agent GPT v1 (sol high), Claude v1 hoặc Claude v2 (Opus high), hỏi người dùng nếu chưa nói rõ. Dùng khi người dùng gọi $new-agent-paseo hoặc nói "new agent paseo", "mở agent paseo", "mở phiên brain", "mở brain sol", "mở brain claude v1/v2", "đổi sang gpt-mono".
---

# new-agent-paseo

**Tóm tắt:** skill mỏng gọi script canonical `new-agent-paseo` của core
hybrid-hands (không sao chép logic). Script làm đủ 3 việc: đặt profile
`gpt-mono`, bật `ext_hand.native.claude/codex = auto`, mở phiên Paseo main
brain ở tab mới cùng workspace rồi kiểm phiên không có phiên cha. Lỗi trước khi
mở được phiên thì script tự khôi phục `.claude/hybrid-hands.json`. Skill LUÔN
truyền `--brain`; người dùng chưa nói rõ loại agent thì hỏi trước khi chạy.

## 1. Chọn loại agent

Người dùng đã nói rõ (ví dụ "mở agent claude v2", "brain sol") thì dùng luôn,
không hỏi. Chưa rõ thì hỏi trước khi chạy, bằng công cụ hỏi người dùng của
Codex (`request_user_input`) nếu có; không có thì hỏi bằng một tin nhắn ngắn
và dừng chờ trả lời. Ba lựa chọn:

| Lựa chọn | Tham số | Brain |
|---|---|---|
| GPT v1 | `--brain gpt-v1` | gpt-6.1-sol high, provider Paseo codex |
| Claude v1 | `--brain claude-v1` | claude-opus-5-5 high, tài khoản v1 |
| Claude v2 | `--brain claude-v2` | claude-opus-5-5 high, tài khoản v2 |

## 2. Resolve script

- Resolve core `hand-ext` theo thứ tự: cờ người dùng đưa, rồi env
  `HYBRID_HANDS_CORE_CLI`, rồi
  `~/app/claude-plugins/hybrid-hands/plugins/hybrid-hands/bin/hand-ext`.
  Không dùng PATH fallback.
- `ABS_SCRIPT` = `$(dirname CORE_HAND_EXT)/new-agent-paseo` (đường dẫn tuyệt
  đối). Không có file đó thì dừng và báo, không tự làm thay.

## 3. Chạy đúng một lệnh

Đổi lời người dùng thành tham số rồi chạy tại repo đang làm việc:

```text
ABS_SCRIPT --cwd ABS_REPO --brain BRAIN [tham số khác]
```

- Không tự làm lại từng bước bằng tay, không sửa script khi lỗi; in nguyên
  thông báo lỗi cho người dùng.
- Lệnh cần gọi daemon Paseo cục bộ và ghi `.claude/hybrid-hands.json`: sandbox
  chặn thì xin quyền chạy escalated (ngoài sandbox).

## 4. Tham số

| Tham số | Ý nghĩa |
|---|---|
| `--brain gpt-v1\|claude-v1\|claude-v2` | Bắt buộc với skill (không có thì script báo lỗi khi stdin không phải TTY). Bí danh cũ: `gpt`/`sol` = `gpt-v1`, `v1`/`v2` = `claude-v1`/`claude-v2`. |
| `--model M`, `--effort E` | Ghi đè model hoặc mức thinking. |
| `--workspace WKS_ID` | Chọn workspace Paseo; bỏ trống thì script tự tìm theo phiên gọi hoặc `cwd`. |
| `--prompt "..."` | Việc đầu tiên giao cho brain. |
| `--title "..."` | Tên tab. |
| `--cwd DIR` | Repo nhận profile (luôn truyền `ABS_REPO`). |
| `--dry-run` | Chỉ in các bước, không ghi cấu hình, không mở phiên. |

## 5. Sau khi chạy

- Báo agentId, provider/model của phiên mới; phiên mới không báo kết quả về
  phiên đang gọi.
- Profile mới áp dụng cho phiên mở sau.
- Nhắc commit `.claude/hybrid-hands.json` theo luật repo.
- Quay lại: `hand-ext profile set claude-mono`.
