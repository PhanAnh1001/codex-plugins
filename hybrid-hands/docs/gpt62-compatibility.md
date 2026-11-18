# Tương thích Sol/Astra 6.2

## Tóm tắt

Adapter chuyển nguyên model/effort do core trả, bao gồm `gpt-6.2-sol` và `gpt-6.2-astra`; generator giữ nguyên metadata đó trong agent TOML. Cần core hỗ trợ hai model (core0.67.2) nếu muốn chọn qua profile/model CLI. Bản cập nhật này không đổi luật/default chọn model, không sửa cấu hình hay cài runtime.

## Contract không thay đổi

- Adapter không có allowlist, bảng giá hay lựa chọn model riêng. Quyết định provider/account/model/effort vẫn thuộc core.
- Mặc định hiện hành vẫn là Sol6.1 cho brain/code và Terra6.1 cho collect theo profile. Chỉ yêu cầu chọn tường minh mới dùng6.2; không tự thay các role sang model mới.
- Guard, exit7 và điều kiện native vẫn giữ nguyên. Agent được sinh không chứng minh quyền dùng model hay native invocation.
- Không thêm lệnh run, model fallback, quyền account hoặc đường vòng bỏ qua validator. Core cũ có thể từ chối6.2; adapter giữ lỗi đó.

## Kiểm chứng

Test fixture cho cả hai model với low/medium/high/xhigh kiểm nguyên vẹn profile → pick → agent TOML; collect vẫn Terra6.1 low. Có test giữ guard exit7 và kiểm lựa chọn6.1 low không tự nâng. Core có test riêng về capability, canonical price, model CLI, default/preset cũ và argv run bằng backend giả. Bộ adapter:32 test và19 subtest đạt. Kiểm CLI bridge/core thật trên cấu hình tạm cũng nhận cả hai model mới; cấu hình dự án thật vẫn chọn6.1 và giữ nguyên hash.

Để kiểm adapter, chạy từ root repo:

```sh
uv run --no-project --with pytest python -m pytest hybrid-hands/tests/test_bridge.py hybrid-hands/tests/test_install_agents.py hybrid-hands/tests/test_gpt62_compat.py -q
```

Không cần đổi bridge/generator production hoặc version adapter chỉ để nhận thêm tên model: hai thành phần đã lấy metadata từ core. Không cài/reload plugin hay ghi agent vào home thật trong đợt kiểm này; chỉ fixture tạm. Hỗ trợ model trong Codex runtime/tài khoản vẫn phải xác minh trước invocation.

## Nguồn và Social listening

[OpenAI công bố Sol/Astra6.2](https://openai.com/index/introducing-gpt-6-2-astra-sol/) (không hiện ngày bài, đọc18/11/2026) xác nhận tên model. [Thảo luận low effort](https://www.reddit.com/r/codex/comments/1wefmx7/low_effort_isnt_necessarily_cheaper/) (khoảng2 tháng trước theo trang, không rõ ngày; đọc18/11/2026) là trải nghiệm cá nhân, phụ thuộc task, không chứng minh cấu hình tối ưu. User yêu cầu chỉ thêm khả năng chạy model mới và giữ nguyên luật chọn cũ; vì vậy không cập nhật default/preset hoặc triển khai routing mới.
