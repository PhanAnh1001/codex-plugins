---
name: open-gpt-brain
description: Đổi profile hybrid-hands của repo sang gpt-mono, bật subagent native, rồi mở phiên Paseo "main brain" ở tab mới cùng workspace (phiên độc lập, không phải subagent); brain mặc định GPT sol high, chọn được Claude v1/v2 (Opus high). Dùng khi người dùng gọi $open-gpt-brain hoặc nói "mở brain sol", "mở brain claude v1/v2", "mở phiên main brain", "đổi sang gpt-mono", "chuyển brain sang GPT".
---

# open-gpt-brain

**Tóm tắt:** skill mỏng gọi script canonical `open-gpt-brain` của core
hybrid-hands (không sao chép logic). Script làm đủ 3 việc: đặt profile
`gpt-mono`, bật `ext_hand.native.claude/codex = auto`, mở phiên Paseo main
brain ở tab mới cùng workspace rồi kiểm phiên không có phiên cha. Lỗi trước khi
mở được phiên thì script tự khôi phục `.claude/hybrid-hands.json`.

## 1. Resolve script

- Resolve core `hand-ext` theo thứ tự: cờ người dùng đưa, rồi env
  `HYBRID_HANDS_CORE_CLI`, rồi
  `~/app/claude-plugins/hybrid-hands/plugins/hybrid-hands/bin/hand-ext`.
  Không dùng PATH fallback.
- `ABS_SCRIPT` = `$(dirname CORE_HAND_EXT)/open-gpt-brain` (đường dẫn tuyệt
  đối). Không có file đó thì dừng và báo, không tự làm thay.

## 2. Chạy đúng một lệnh

Đổi lời người dùng thành tham số (ví dụ "claude v2" → `--brain claude-v2`,
"brain sol" → `--brain gpt`), rồi chạy tại repo đang làm việc:

```text
ABS_SCRIPT --cwd ABS_REPO [tham số]
```

- Không tự làm lại từng bước bằng tay, không sửa script khi lỗi; in nguyên
  thông báo lỗi cho người dùng.
- Lệnh cần gọi daemon Paseo cục bộ và ghi `.claude/hybrid-hands.json`: sandbox
  chặn thì xin quyền chạy escalated (ngoài sandbox).

## 3. Tham số

| Tham số | Ý nghĩa |
|---|---|
| `--brain gpt\|claude-v1\|claude-v2` | Loại brain. `gpt` (mặc định, viết tắt `sol`) theo vai brain của gpt-mono; `claude-v1`/`claude-v2` (viết tắt `v1`/`v2`) mở Opus high trên tài khoản đó. |
| `--model M`, `--effort E` | Ghi đè model hoặc mức thinking. |
| `--workspace WKS_ID` | Chọn workspace Paseo; bỏ trống thì script tự tìm theo phiên gọi hoặc `cwd`. |
| `--prompt "..."` | Việc đầu tiên giao cho brain. |
| `--title "..."` | Tên tab. |
| `--cwd DIR` | Repo nhận profile (luôn truyền `ABS_REPO`). |
| `--dry-run` | Chỉ in các bước, không ghi cấu hình, không mở phiên. |

## 4. Sau khi chạy

- Báo agentId, provider/model của phiên mới; phiên mới không báo kết quả về
  phiên đang gọi.
- Profile mới áp dụng cho phiên mở sau.
- Nhắc commit `.claude/hybrid-hands.json` theo luật repo.
- Quay lại: `hand-ext profile set claude-mono`.
