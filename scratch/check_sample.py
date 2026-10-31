from erp_ai.rich_ui import render_erp_embed

sample = {"blocks": [{"type": "table", "columns": [{"key": "a", "label": "A"}], "rows": []}]}
sample_html = render_erp_embed(sample, [])
print("sample_html[:300]:\n", repr(sample_html[:300]))
idx = sample_html.find('<script>')
print("Index of <script>:", idx)
if idx != -1:
    print("From <script>:\n", sample_html[idx:idx+200])
