import sys
sys.path.insert(0, '/app/backend')

from erp_ai.rich_ui import render_erp_embed

sample_data = {
    "blocks": [
        {
            "type": "summary",
            "text": "Toàn nhà máy HTMP hiện có tổng cộng 2,185 hồ sơ khuôn trong hệ thống ERP."
        },
        {
            "type": "table",
            "title": "Hồ sơ khuôn",
            "columns": [
                {"key": "stt", "label": "STT"},
                {"key": "ma_khuon", "label": "Mã khuôn"},
                {"key": "ten_khuon", "label": "Tên khuôn"},
                {"key": "tinh_trang_khuon", "label": "Tình trạng"}
            ],
            "rows": [
                {"stt": 1, "ma_khuon": "K_VGY1A061", "ten_khuon": "26HI1088", "tinh_trang_khuon": "OK"}
            ]
        }
    ]
}

html = render_erp_embed(sample_data, [])
print("HTML length:", len(html))
assert '--text-main: #f8fafc' in html, "Dark text-main token missing!"
assert '--table-bg: rgba(24, 24, 27, 0.65)' in html, "Dark table-bg token missing!"
assert 'getTheme()' in html, "Head theme detector missing!"
assert "type === 'erp:theme'" in html, "Theme message listener missing!"
print("ALL EMBED THEME ASSERTIONS PASSED!")
