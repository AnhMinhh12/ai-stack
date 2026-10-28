import json
import base64
from erp_ai.export_files import blocks_from_rows, build_downloads, requested_formats

# Mock payload
payload = {
    'report': {'id': 'ton-kho-theo-khuon', 'title': 'Tồn kho theo khuôn (Die)'},
    'lookup': {'ma_vt': 'QC7-5146-000'},
    'rows': [
        {'die_no': 'V1', 'mold': '', 'so_luong': 13920},
        {'die_no': 'V2', 'mold': '', 'so_luong': 940}
    ]
}

blocks = blocks_from_rows(payload)
print("Blocks types:", [b['type'] for b in blocks])
chart_block = next(b for b in blocks if b['type'] == 'chart')
print("Chart allowed:", chart_block.get('allowed_chart_types'))
