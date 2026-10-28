import sys
sys.path.insert(0, '/app/backend')
from erp_ai.export_files import blocks_from_rows, build_downloads, requested_formats
from erp_ai.rich_ui import render_erp_embed

payload = {'report': {'id': 'ton-kho-theo-khuon', 'title': 'Tồn kho theo khuôn (Die)'}, 'lookup': {'ma_vt': 'QC7-5146-000'}, 'rows': [{'die_no': 'V1', 'mold': '', 'so_luong': 13920}, {'die_no': 'V2', 'mold': '', 'so_luong': 940}]}
blocks = blocks_from_rows(payload)
print('Blocks count:', len(blocks))
downloads = build_downloads(blocks, requested_formats('test'))
html = render_erp_embed({'blocks': blocks}, downloads)
print('HTML length:', len(html))
print('Has canvas chart in html:', 'canvas id="chart-' in html)
print('Has btn-xlsx in html:', 'btn-xlsx' in html)
