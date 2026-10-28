import sys, traceback
sys.path.insert(0, '/home/admin/ai-stack')
from erp_ai.export_files import blocks_from_rows, build_downloads, requested_formats
from erp_ai.rich_ui import render_erp_embed

payload = {"report": {"id": "ton-kho-theo-khuon", "title": "Tồn kho theo khuôn (Die)"}, "lookup": {"ma_vt": "QC7-5146-000"}, "rows": [{"die_no": "V1", "mold": "", "so_luong": 13860}, {"die_no": "V2", "mold": "", "so_luong": 940}]}
blocks = blocks_from_rows(payload)
print("Blocks ok:", len(blocks))
try:
    downloads = build_downloads(blocks, requested_formats("test"))
    print("Downloads ok:", len(downloads))
except Exception as e:
    print("Error in build_downloads:")
    traceback.print_exc()

try:
    html = render_erp_embed({"blocks": blocks}, downloads)
    print("HTML ok, length:", len(html))
except Exception as e:
    print("Error in render_erp_embed:")
    traceback.print_exc()
