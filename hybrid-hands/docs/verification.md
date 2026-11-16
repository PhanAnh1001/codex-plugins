# Kiểm chứng adapter 0.1.0

Ngày 2026-11-16. Phạm vi: cài qua CLI chính thức vào hai home đã được duyệt; không sửa source, profile, account hay model.

## Cài đặt thực tế

Với từng `CODEX_HOME=/Users/anhtp/.codex` và `/Users/anhtp/.codex-hand`, các lệnh sau đều exit 0 (timeout hữu hạn 30 giây mỗi lệnh):

```sh
codex plugin marketplace list --json
codex plugin marketplace add /Users/anhtp/app/codex-plugins/hybrid-hands --json
codex plugin add hybrid-hands@hybrid-hands-local --json
codex plugin list --json --marketplace hybrid-hands-local
```

Trước khi add, hai home chưa có marketplace `hybrid-hands-local`; không có conflict tên. Sau cài, CLI list báo `hybrid-hands`, version `0.1.0`, enabled `true` ở cả hai home. CLI add trả installedPath tương ứng:

- `/Users/anhtp/.codex/plugins/cache/hybrid-hands-local/hybrid-hands/0.1.0`
- `/Users/anhtp/.codex-hand/plugins/cache/hybrid-hands-local/hybrid-hands/0.1.0`

Đối chiếu byte source/cache thành công cho `.codex-plugin/plugin.json`, `scripts/hybrid_codex.py`, `scripts/install_agents.py`, `skills/hybrid-hands/SKILL.md` ở cả hai home. Manifest parse JSON hợp lệ, version 0.1.0. SHA-256 chung theo thứ tự trên:

```text
380feb6b099432b4dd0e1a615cbc8f8387294b80af910ac66e52f9aecc787b6a
42d2999122370393a99f99be06cc277306b1544e731855bc2dd93b29867b9743
624ef5bfad2e627125cc541b9248111f786a6b589d0408bc8e746bf0defed3db
ab15390387c72c6eedc425156bcf52e70f23145950e405b09eb5a6763d1e9d9c
```

## Discovery từ runtime mới

Cho từng home, khởi động `codex app-server --stdio -c analytics.enabled=false`, gửi RPC `initialize` (experimentalApi true), `skills/list` với `cwds=["/Users/anhtp/app/claude-plugins"]`, forceReload true. Cả hai initialize và skills/list thành công, error count discovery bằng 0. Skill được runtime discover:

- name: `hybrid-hands:hybrid-hands`
- enabled: `true`
- pluginId: `hybrid-hands@hybrid-hands-local`
- path: `<installedPath>/skills/hybrid-hands/SKILL.md` đúng từng home ở trên.

Lượt đầu bộ lọc so khớp tên `hybrid-hands` nên hiển thị rỗng; lượt kiểm tiếp lọc theo tên/path có prefix đã xác nhận skill thực tế. `plugin/list` mới cũng thành công, xác nhận plugin enabled và marketplace path `/Users/anhtp/app/codex-plugins/hybrid-hands/.agents/plugins/marketplace.json`; field version của RPC này là null, version được xác nhận riêng qua CLI/cache manifest. Mọi app-server do lượt kiểm này tạo đều đóng và exit 0. Không thread/turn/model invocation hay API trả phí.

## Bridge và generator đã cài

Trong mỗi home, chạy script từ installedPath, không từ source:

```sh
python3 <installedPath>/scripts/hybrid_codex.py profile --cwd /Users/anhtp/app/claude-plugins
python3 <installedPath>/scripts/install_agents.py --cwd /Users/anhtp/app/claude-plugins --codex-home <home>
```

Cả bốn lệnh exit 0. Profile `claude-mono`, tất cả role provider `claude`. Generator dry-run báo code, collect tier 1 và tier 2 đều `skipped: provider is not codex` ở mỗi home. Không chạy `--apply`, không tạo agent hybrid, không đổi profile để ép generation. Native invocation chưa chạy; discovery không chứng minh invocation/model capability.

`/Users/anhtp/.codex/agents/hand.toml` được parse whitelist trước và sau cài: model `gpt-6.1-sol`, model_reasoning_effort `low`; SHA-256 giữ nguyên `98872ba1fa8cfd59f3c1604ac4f9565b1082f9afd0337c8f1982ba72520e0c1a`. Home `.codex-hand` không có hand.toml tại đường dẫn tương ứng. Không ghi thủ công registry/settings/config, không gọi enable/disable cho plugin khác. Không có baseline toàn bộ settings/plugin để chứng minh mọi byte ngoài phạm vi bất biến.

## Giới hạn và kiểm tra còn lại

Lệnh thăm dò ban đầu `CODEX_HOME=/Users/anhtp/.codex codex plugin list --json` (không giới hạn marketplace) timeout sau 25 giây; subprocess đã dừng, không dùng kết quả để chứng nhận toàn bộ plugin khác. Các lệnh list có filter marketplace sau đó đều exit 0.

Không chạy lại 8 bridge + 13 generator tests vì packet nêu brain đã review và tests đạt, không có thay đổi code. Báo cáo này chỉ chứng nhận cài đặt và discovery từ app-server mới. Chưa chứng minh phiên parent hiện đang mở đã hot reload plugin; mở phiên mới/reload để dùng skill đã cài. Không commit/push; source repo ban đầu `git status --short` là `?? hybrid-hands/`.

Kiểm cuối: `git diff --check` exit 0 (không bao phủ file untracked); `git status --short` vẫn `?? hybrid-hands/`. Kiểm whitespace trực tiếp trên báo cáo: không có trailing whitespace.
