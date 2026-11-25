# Hybrid Hands cho Codex

Adapter 0.2.1 đóng gói workflow skill và script mỏng cho core hybrid-hands
0.66.0. Source adapter ở `~/app/codex-plugins/hybrid-hands`; core tiếp tục ở
`~/app/claude-plugins/hybrid-hands`. Adapter không sao chép policy hay bảng
model, không đổi profile/account. Hook SessionStart nạp đầy đủ skill khi
startup/resume ở phiên gốc; xem [contract và kiểm chứng](docs/startup-hook.md).

Gọi `$hybrid-hands` để lấy profile/pick trước delegation. Workflow đầy đủ ở
[SKILL.md](plugins/hybrid-hands/skills/hybrid-hands/SKILL.md).
Gọi `$open-gpt-brain` để đổi repo sang gpt-mono và mở phiên Paseo main brain
([SKILL.md](plugins/hybrid-hands/skills/open-gpt-brain/SKILL.md)).
[Plan](docs/plan.md) và [spec](docs/spec.md) ghi phạm vi và điều kiện kiểm
chứng; [changelog](CHANGELOG.md) ghi thay đổi release.

## Sử dụng source

Từ source checkout, dùng đường dẫn tuyệt đối:

```sh
python3 "$HOME/app/codex-plugins/hybrid-hands/plugins/hybrid-hands/scripts/hybrid_codex.py" profile --cwd /absolute/repo
python3 "$HOME/app/codex-plugins/hybrid-hands/plugins/hybrid-hands/scripts/hybrid_codex.py" pick --cwd /absolute/repo --role code
python3 "$HOME/app/codex-plugins/hybrid-hands/plugins/hybrid-hands/scripts/hybrid_codex.py" pick --cwd /absolute/repo --role collect --tier 1
```

Cả hai subcommand nhận `--core-cli /absolute/hand-ext`. Thứ tự resolve:
cờ này, `HYBRID_HANDS_CORE_CLI`, source CLI mặc định
`~/app/claude-plugins/hybrid-hands/plugins/hybrid-hands/bin/hand-ext`.
Bridge chỉ đọc JSON profile/pick; chạy source không chứng minh plugin đã
cài hay runtime đang dùng source đó. Guard/lỗi core được giữ nguyên.

## Agent và home runtime

Generator `plugins/hybrid-hands/scripts/install_agents.py` mặc định dry-run:

```sh
python3 /absolute/plugin/scripts/install_agents.py --cwd /absolute/repo --codex-home /absolute/codex-home
python3 /absolute/plugin/scripts/install_agents.py --cwd /absolute/repo --codex-home /absolute/codex-home --apply
```

Có thể thêm `--core-cli /absolute/hand-ext`. Generator chỉ tạo
`hybrid-code`, `hybrid-collect-1`, `hybrid-collect-2` từ các row
`profile.roles.code`, `collect.1`, `collect.2` có provider `codex`; row của
provider khác được skip. Model/effort/account lấy từ core. Generation không
yêu cầu `pick.native` và không xác nhận native eligibility. Không ghi đè
agent không thuộc quản lý hoặc sửa registry. Trước invocation, brain vẫn
phải lấy pick mới, kiểm exact model/effort/account/native và cấu hình agent
đang được runtime nạp. File được tạo chưa chứng minh agent đã được invoke.

`~/.codex` và `~/.codex-hand` là hai home runtime riêng; chọn `--codex-home`
tường minh, không suy cài ở home này đã có ở home kia. User skills nằm dưới
`$HOME/.agents/skills`, không dưới `$CODEX_HOME`. Không tự bật ở repo/home
chưa dùng. Sau khi đổi agent/profile hoặc cài plugin, mở phiên mới hoặc
reload theo khả năng runtime rồi kiểm lại đường dẫn/version và model/effort
được nạp; phiên đang mở chưa nhận thay đổi phải được báo rõ.

## Cài plugin

CLI Codex 0.169.0 đã được probe với compatibility manifest
`.codex-plugin/plugin.json`; root-only portable manifest báo thiếu
`plugin.json` trên binary này. Marketplace local tên `hybrid-hands-local`,
đăng ký package root `hybrid-hands`, source `./plugins/hybrid-hands`. Plugin
không tự đăng ký agent từ file static; dùng generator ở trên cho home được
phép. Release 0.2.1 có hook tự nạp skill cho startup/resume.

Cho từng home đã được duyệt, dùng CLI chính thức (không chép registry):

```sh
CODEX_HOME="$HOME/.codex" codex plugin marketplace add "$HOME/app/codex-plugins/hybrid-hands" --json
CODEX_HOME="$HOME/.codex" codex plugin add hybrid-hands@hybrid-hands-local --json
CODEX_HOME="$HOME/.codex" codex plugin list --json --marketplace hybrid-hands-local

CODEX_HOME="$HOME/.codex-hand" codex plugin marketplace add "$HOME/app/codex-plugins/hybrid-hands" --json
CODEX_HOME="$HOME/.codex-hand" codex plugin add hybrid-hands@hybrid-hands-local --json
CODEX_HOME="$HOME/.codex-hand" codex plugin list --json --marketplace hybrid-hands-local
```

Điều chỉnh đường dẫn package root nếu checkout ở nơi khác. Cập nhật local
bằng cách tăng version trong source rồi chạy lại `codex plugin add` cho từng
home đã được duyệt; không dùng `plugin update` hoặc `--scope project`.
`installedPath` từ kết quả add và version/path cache là evidence cài đặt,
chưa chứng minh phiên đang mở đã nạp bản đó. Mở phiên mới hoặc reload rồi
kiểm version/path thực tế được nạp, skill discovery và cấu hình agent.

Các lệnh trên là hướng dẫn, không chứng nhận đã cài ở home thật. Báo riêng
kết quả cài đặt, discovery và native invocation; không suy invocation từ
file agent đã sinh hoặc plugin đã cài.

## Tương thích model mới

Sol/Astra6.2 được chuyển nguyên từ core sang pick/agent; cần core0.67.2
để chọn qua profile/model CLI. Không đổi default hoặc luật chọn model cũ,
không thêm bảng model ở adapter. Xem [phạm vi và kiểm thử](docs/gpt62-compatibility.md).

## Uỷ quyền Git cho hand (0.2.1)

Hand mặc định dừng sau sửa code và kiểm chứng. Brain muốn hand commit/push
phải giao packet rõ repository, hành động commit và/hoặc push, nhánh đích và
remote cho push. Test đạt hoặc yêu cầu “finish” không cấp quyền. Chỉ stage
file thuộc packet; không stage thay đổi của người khác. Luật ưu tiên cao hơn
và lệnh cấm runtime vẫn áp dụng; merge, force push, viết lại lịch sử và thao
tác phá huỷ vẫn cấm. Hand báo lệnh/kết quả, SHA, nhánh, remote/kết quả push.
Đây là thay đổi source; không chứng nhận quyền của phiên đang chạy hay tự
cài/reload runtime. Contract chi tiết ở [spec](docs/spec.md).

### Social listening

Nguồn do brain cung cấp, đọc ngày 2026-11-17: cộng đồng báo việc push ngoài
uỷ quyền tại [#67060](https://github.com/anthropics/claude-code/issues/67060)
(2026-06-10) và [#59498](https://github.com/anthropics/claude-code/issues/59498)
(2026-05-15). Đây là báo cáo cộng đồng chưa kiểm chứng, không phải bằng chứng
trực tiếp về Codex. Vì vậy chính sách tách quyền commit/push thành hành động
phải ghi rõ trong packet; test thành công không được xem là quyền push.
