import sys, json
sys.path.insert(0, '/home/admin/ai-stack')
from erp_ai.export_files import blocks_from_rows

payload = {"report": {"id": "ton-kho-theo-khuon", "title": "Tồn kho theo khuôn (Die)"}, "lookup": {"ma_vt": "QC7-5146-000"}, "rows": [{"die_no": "V1", "mold": "", "so_luong": 13860}, {"die_no": "V2", "mold": "", "so_luong": 940}]}
blocks = blocks_from_rows(payload)
print("Blocks count:", len(blocks))
for b in blocks:
    print("Block type:", b.get("type"))
    if b.get("type") == "chart":
        print("Chart:", json.dumps(b, ensure_ascii=False, indent=2))
