from erp_ai.rich_ui import render_erp_embed

sample = {"blocks": [{"type": "table", "columns": [{"key": "a", "label": "A"}], "rows": []}]}
html = render_erp_embed(sample, [])
idx = html.find('</head>')
print(html[:idx + len('</head>')])
