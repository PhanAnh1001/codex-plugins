---
name: hybrid-hands
description: Điều phối delegation theo vai của hybrid-hands cho repo có profile hybrid, gpt-mono hoặc claude-mono; dùng khi giao hand theo core policy hoặc gọi rõ $hybrid-hands.
---

# Hybrid Hands

Phiên brain lập phạm vi, giao packet và review; hand chỉ thực thi packet. Đọc
AGENTS.md/CLAUDE.md áp dụng trước khi làm. Skill này không thay luật nền của
repo và không tự cho phép sửa cấu hình hay cài runtime.

## Resolve core trước mỗi lượt giao

Resolve [bridge đi kèm](../../scripts/hybrid_codex.py) theo thư mục thật của
skill đang nạp, kể cả khi skill được symlink; không theo cwd repo làm việc.
Gọi Python với đường dẫn bridge tuyệt đối đã resolve:

```text
python3 ABS_BRIDGE profile --cwd ABS_REPO
python3 ABS_BRIDGE pick --cwd ABS_REPO --role code
python3 ABS_BRIDGE pick --cwd ABS_REPO --role collect --tier 1
python3 ABS_BRIDGE pick --cwd ABS_REPO --role chrome --tier 2
```

`ABS_REPO` là repo nhận công việc. Cả hai lệnh nhận `--core-cli ABS_EXE`.
Core resolve theo cờ đó, rồi `HYBRID_HANDS_CORE_CLI`, rồi
`~/app/claude-plugins/hybrid-hands/plugins/hybrid-hands/bin/hand-ext`.
Đó là source CLI, không phải bằng chứng plugin cache đã được nạp. Không dùng
PATH fallback hay sao chép policy/model từ core.

Trước **mỗi** delegation, lấy profile rồi pick mới cho đúng repo/vai/tier.
Thiếu profile: dừng và báo cần người dùng chốt; không tự đặt profile.
Chỉ collect/chrome nhận tier; áp dụng thang bậc/retry theo luật repo và core.
Giữ exit status và lỗi core: guard blocked hoặc exit 7 phải dừng, không biến
thành success; exit 8 đợi slot có giới hạn theo hướng dẫn core, không đổi
backend/account để né. Không đổi profile, account, model hay effort để thử lại.

## Chọn executor từ evidence

Chỉ spawn native khi `native` là boolean thật `true`, `guard_blocked` là
boolean thật `false`, provider/account có capability phù hợp, và metadata
runtime của executor đã nạp khớp **chính xác** model/effort của pick hiện tại.
Tên agent `hand` hay `hybrid-code` không chứng minh cấu hình. Parse/discovery
TOML cũng không chứng minh native invocation hay quyền account dùng model.
Nếu thiếu evidence hoặc cấu hình stale, không spawn native; báo điều kiện
thiếu. Chỉ chuyển external khi core cho phép tuyến đó, không tự fallback.

Native Codex dùng `fork_turns=none`, brief tự chứa và không truyền override
model/effort. Khi core chọn non-native, dùng core `hand-ext run` theo cùng
role/backend đã resolve; đọc `--help` của core để có cú pháp hiện hành, không
suy cờ từ interface của bridge. Bridge chỉ hỗ trợ profile/pick.

Agent generator đi kèm có interface:

```text
python3 ABS_INSTALLER --cwd ABS_REPO --codex-home ABS_CODEX_HOME
python3 ABS_INSTALLER --cwd ABS_REPO --codex-home ABS_CODEX_HOME --apply
```

Resolve `ABS_INSTALLER` từ `../../scripts/install_agents.py` cạnh bridge;
có thể thêm `--core-cli ABS_EXE`. Mặc định dry-run, chỉ ghi khi `--apply`.
Generator đọc `profile.roles.code`, `collect.1`, `collect.2`, chỉ sinh row có
provider `codex` với tên tương ứng `hybrid-code`, `hybrid-collect-1`,
`hybrid-collect-2`; provider khác được skip. Model/effort/account lấy từ JSON
core, không có bảng mặc định riêng. Generation không yêu cầu `pick.native`
và không xác nhận native eligibility; trước invocation vẫn phải lấy pick
mới và kiểm exact model/effort/account/native cùng cấu hình agent đang nạp.
Không ghi đè tên không thuộc quản lý hay sửa registry. Chỉ apply trong phạm
vi cài đặt được giao; kiểm metadata runtime sau khi nạp lại, không coi file
được tạo là agent đã được invoke. Plugin không tự đăng ký file agent static.

Cài plugin bằng CLI marketplace/add/list cho từng home được duyệt theo
hướng dẫn trong README của source adapter. `installedPath` và version/path cache
chứng minh cài đặt; phiên đang mở cần reload hoặc phiên mới rồi kiểm lại
version/path thực tế được nạp. Release 0.1.0 không có hook tự inject.

## Brief và bàn giao

Brief phải có objective, phạm vi ghi/ownership, non-goals, acceptance,
source liên quan và lệnh kiểm chứng hẹp. Các hand không cùng sửa file hay
phụ thuộc đồng thời. Ghi rõ hand không một mình, giữ thay đổi của người khác;
không delegation, quản lý/giao tiếp phiên khác, mở side-session, commit hay
push. Hand dừng sau implementation và verification, trả evidence cho brain.

Chép nguyên văn ba đoạn luật dữ liệu sau vào brief hand ngoài:

Không in/hiện giá trị `.env`, token, credential ở bất kỳ tầng nào; công cụ của plugin (`hand-ext doctor/run`, đọc hạn mức) được đọc file auth nội bộ, chỉ không được in giá trị. Brief giao hand ngoài chép nguyên văn luật này.
Không đọc `.env` bằng lệnh hay tool hiện giá trị: `cat`, `head`, `tail`, `grep`, `sed`, `awk`, `less`, `more`, `rg`, `Read`, kể cả có che phần sau dấu `=`.
Không đọc hay in token, auth.json, file credential. Không giao hand ngoài việc cần secret hay dữ liệu khách hàng. Chỉ dùng code và fixtures giả công khai được; không đọc transcript/log thật. Không gọi API trả phí, không tạo hay dùng API key.

Brain review diff và kết quả thật trước khi kết luận. Báo riêng source/test,
discovery, native invocation, home/version/path được nạp và nhu cầu reload;
thiếu evidence ghi chưa kiểm chứng. Native không tạo ledger hand-ext; không
suy quota từ token/USD hay bịa usage thiếu nguồn.
