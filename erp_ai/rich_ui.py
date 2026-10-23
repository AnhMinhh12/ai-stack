"""Render reviewed ERP blocks as an isolated Open WebUI Rich UI embed."""
from __future__ import annotations

import json
import base64
from html import escape


# Pin the browser asset; the static fallback remains visible if it cannot load.
CHART_JS = "https://cdn.jsdelivr.net/npm/chart.js@4.5.1/dist/chart.umd.min.js"


def _text(value):
    return escape("—" if value is None or value == "" else str(value), quote=True)


def _script_json(value):
    return json.dumps(value, ensure_ascii=False, separators=(",", ":")).replace("<", "\\u003c").replace(">", "\\u003e").replace("&", "\\u0026")


def render_erp_embed(result, downloads=()):
    """Only backend-created blocks enter HTML; model prose never becomes markup."""
    blocks = result.get("blocks") or []
    if not any(b.get("type") == "table" for b in blocks):
        return None
    sections, chart_data = ['<p class="intro">Dưới đây là kết quả tra cứu ERP theo yêu cầu của bạn:</p>'], []
    if downloads:
        buttons = "".join(
            f'<button type="button" data-download-index="{index}">Tải {_text(item["name"].rsplit(".", 1)[-1].upper())}</button>'
            for index, item in enumerate(downloads)
        )
        sections.append(f'<div class="download-controls" role="group" aria-label="Tải báo cáo">{buttons}</div>')
    for block in blocks:
        kind = block.get("type")
        if kind == "summary":
            sections.append(f'<p class="summary">{_text(block.get("text"))}</p>')
        elif kind == "warning":
            sections.append(f'<p class="warning">{_text(block.get("text"))}</p>')
        elif kind == "table":
            columns = block.get("columns") or []
            headers = "".join(f'<th scope="col">{_text(c.get("label"))}</th>' for c in columns)
            rows = "".join("<tr>" + "".join(f'<td>{_text(row.get(c.get("key")))}</td>' for c in columns) + "</tr>"
                           for row in block.get("rows") or [])
            sections.append(f'<div class="table-scroll" role="region" aria-label="{_text(block.get("title"))}" tabindex="0"><table><thead><tr>{headers}</tr></thead><tbody>{rows}</tbody></table></div>')
        elif kind == "chart":
            index = len(chart_data)
            points = block.get("points") or []
            unit = (block.get("series") or [{}])[0].get("unit") or ""
            label = (block.get("series") or [{}])[0].get("label") or "Số lượng"
            chart_type = block.get("chart_type") if block.get("chart_type") in ("bar", "line", "pie") else "bar"
            allowed = [kind for kind in ("bar", "line", "pie") if kind in (block.get("allowed_chart_types") or [chart_type])]
            if chart_type not in allowed:
                allowed.insert(0, chart_type)
            chart_data.append({"labels": [str(p.get("category") or "") for p in points],
                               "values": [float(p["quantity"]) for p in points],
                               "label": label, "unit": unit, "kind": chart_type, "allowed": allowed,
                               "x_label": (block.get("x") or {}).get("label") or "Nhóm"})
            peak = max((abs(float(p["quantity"])) for p in points), default=0) or 1
            fallback = "".join(f'<li><span>{_text(p.get("category"))}</span><div class="bar-track"><span class="bar-fill" style="width:{round(abs(float(p["quantity"])) / peak * 100)}%"></span></div><strong>{_text(p.get("quantity"))} {_text(unit)}</strong></li>' for p in points)
            controls = ''.join(
                f'<button type="button" data-chart-index="{index}" data-chart-kind="{kind}" aria-pressed="{str(kind == chart_type).lower()}"'
                + ('' if kind in allowed else ' disabled title="Chỉ khả dụng khi dữ liệu đầy đủ, có 2–8 nhóm và số lượng không âm"')
                + f'>{title}</button>'
                for kind, title in (("bar", "Cột"), ("line", "Đường"), ("pie", "Tròn")))
            sections.append(f'<section class="chart"><h2>{_text(block.get("title"))}</h2><p class="scope">{_text(block.get("scope"))} · {_text(unit)}</p><div class="chart-controls" role="group" aria-label="Chọn loại biểu đồ">{controls}</div><div class="canvas-wrap"><canvas id="chart-{index}" role="img" aria-label="{_text(block.get("title"))}"></canvas></div><ul id="fallback-{index}" class="fallback" style="display:none">{fallback}</ul></section>')
    payload = _script_json(chart_data)
    download_payload = _script_json([
        {"name": item["name"], "mime": item["mime"], "base64": base64.b64encode(item["data"]).decode("ascii")}
        for item in downloads
    ])
    script = """<script>
const charts = PAYLOAD;
const downloads = DOWNLOADS;
const activeCharts = new Map();
const chartColors = ['#2563eb','#0d9488','#f59e0b','#dc2626','#7c3aed','#db2777','#65a30d','#0891b2'];
const formatNumber = value => new Intl.NumberFormat('vi-VN', {maximumFractionDigits: 2}).format(value);
function contrastColor(hex) {
  const rgb = [1, 3, 5].map(offset => parseInt(hex.slice(offset, offset + 2), 16) / 255);
  const luminance = rgb.map(v => v <= 0.04045 ? v / 12.92 : ((v + 0.055) / 1.055) ** 2.4);
  return luminance[0] * 0.2126 + luminance[1] * 0.7152 + luminance[2] * 0.0722 > 0.32 ? '#172033' : '#ffffff';
}
const valueLabelPlugin = {
  id: 'valueLabel',
  afterDatasetsDraw(chart) {
    const {ctx, data} = chart;
    const meta = chart.getDatasetMeta(0);
    if (!meta || !meta.data) return;
    const values = data.datasets[0].data || [];
    const total = values.reduce((sum, v) => sum + (Number(v) || 0), 0);
    meta.data.forEach((element, index) => {
      const val = Number(values[index]) || 0;
      if (val === 0) return;
      const pct = total > 0 ? ((val / total) * 100).toFixed(1) + '%' : '';
      ctx.save();
      ctx.font = 'bold 12px system-ui, -apple-system, sans-serif';
      ctx.textAlign = 'center';
      if (chart.config.type === 'pie') {
        const angle = (element.startAngle + element.endAngle) / 2;
        const radius = element.outerRadius * 0.65;
        const availableWidth = (element.endAngle - element.startAngle) * radius;
        const quantity = formatNumber(val);
        const showQuantity = availableWidth >= ctx.measureText(quantity).width + 12 && element.outerRadius >= 95;
        // Tiny slices retain their exact value and percentage in the legend.
        if (availableWidth >= ctx.measureText(pct).width + 10) {
          ctx.fillStyle = contrastColor(chartColors[index % chartColors.length]);
          ctx.textBaseline = 'middle';
          const x = element.x + Math.cos(angle) * radius;
          const y = element.y + Math.sin(angle) * radius;
          ctx.fillText(pct, x, y + (showQuantity ? -7 : 0));
          if (showQuantity) ctx.fillText(quantity, x, y + 8);
        }
      } else {
        ctx.fillStyle = '#1e293b';
        ctx.textBaseline = 'bottom';
        ctx.fillText(`${formatNumber(val)} (${pct})`, element.x, element.y - 4);
      }
      ctx.restore();
    });
  }
};
function showChart(index, kind) {
    const item = charts[index];
    if (!window.Chart || !item || !item.allowed.includes(kind)) return;
    const canvas = document.getElementById('chart-' + index);
    if (!canvas) return;
    activeCharts.get(index)?.destroy();
    canvas.parentElement.style.height = kind === 'pie' ? '340px' : '280px';
    const dataset = {label:item.label + (item.unit ? ' (' + item.unit + ')' : ''),data:item.values,backgroundColor:kind === 'pie' ? chartColors : '#2563eb',borderColor:'#1d4ed8',borderWidth:1,tension:0.2};
    const scales = kind === 'pie' ? {} : {
      y:{beginAtZero:true,grace:'15%',title:{display:true,text:item.unit || item.label}},
      x:{title:{display:true,text:item.x_label}}
    };
    activeCharts.set(index, new Chart(canvas, {
      type: kind,
      data: {labels:item.labels, datasets:[dataset]},
      plugins: [valueLabelPlugin],
      options: {
        responsive: true,
        maintainAspectRatio: false,
        animation:false,
        layout: {padding: {top: 18, bottom: 0}},
        plugins: {legend:{display:true,labels:{generateLabels(chart) {
          const defaults = kind === 'pie' ? Chart.overrides.pie.plugins.legend.labels : Chart.defaults.plugins.legend.labels;
          const labels = defaults.generateLabels(chart);
          if (kind !== 'pie') return labels;
          const total = item.values.reduce((sum, value) => sum + value, 0);
          return labels.map((label, i) => ({...label,
            text: `${item.labels[i]}: ${formatNumber(item.values[i])} ${item.unit} (${total ? (item.values[i] / total * 100).toFixed(1) : '0.0'}%)`
          }));
        }}}, tooltip:{enabled:true}},
        scales: scales
      }
    }));
    document.querySelectorAll('[data-chart-index="' + index + '"]').forEach(button => {
      button.setAttribute('aria-pressed', String(button.dataset.chartKind === kind));
    });
    reportHeight();
}
function drawCharts() {
  if (!window.Chart) {
    charts.forEach((item, index) => {
      const fb = document.getElementById('fallback-' + index);
      if (fb) fb.style.display = 'block';
    });
    document.querySelectorAll('.chart-controls button').forEach(button => { button.disabled = true; });
    reportHeight();
    return;
  }
  charts.forEach((item, index) => showChart(index, item.kind));
}
document.addEventListener('click', event => {
  const download = event.target.closest('button[data-download-index]');
  if (download) {
    const item = downloads[Number(download.dataset.downloadIndex)];
    if (!item) return;
    const bytes = Uint8Array.from(atob(item.base64), char => char.charCodeAt(0));
    const url = URL.createObjectURL(new Blob([bytes], {type:item.mime}));
    const link = document.createElement('a');
    link.href = url;
    link.download = item.name;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
    return;
  }
  const button = event.target.closest('button[data-chart-index]');
  if (!button || button.disabled) return;
  showChart(Number(button.dataset.chartIndex), button.dataset.chartKind);
});
function reportHeight() {
  const root = document.getElementById('erp-root') || document.body;
  // Measure content, not the iframe viewport, so resizing cannot grow it forever.
  const height = Math.ceil(Math.max(root.getBoundingClientRect().height, root.scrollHeight) + 32);
  parent.postMessage({type:'iframe:height', height: height}, '*');
}
reportHeight();
window.addEventListener('load', () => {drawCharts(); reportHeight(); setTimeout(reportHeight, 200);});
if (window.ResizeObserver) new ResizeObserver(reportHeight).observe(document.getElementById('erp-root') || document.body);
</script>""".replace("PAYLOAD", payload).replace("DOWNLOADS", download_payload)
    head = """<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>[hidden]{display:none!important}html,body{overflow-y:hidden}body{font:14px system-ui,sans-serif;color:#172033;margin:0;padding:8px 12px;background:#fff}p{line-height:1.5}.intro{margin:0 0 8px}.summary{font-weight:600;margin:0 0 8px}.warning{color:#9a3412}.table-scroll{overflow-x:auto;max-width:100%;border:1px solid #d8dee8;border-radius:8px}table{border-collapse:collapse;width:100%;table-layout:auto;box-sizing:border-box}th,td{text-align:left;padding:8px 10px;border-bottom:1px solid #e5e7eb;white-space:normal;word-break:break-word;vertical-align:top}th{background:#f1f5f9;font-size:12px;font-weight:600}td:nth-child(4),td:nth-child(5){text-align:right}.chart{margin-top:14px;margin-bottom:4px}.chart h2{font-size:16px;margin:0 0 3px}.scope{font-size:12px;color:#475569;margin:0 0 6px}.sources{font-size:12px;color:#475569;margin-top:8px;margin-bottom:0}.canvas-wrap{height:260px;max-width:760px;margin-bottom:4px}.fallback{padding:0;list-style:none;max-width:760px;margin:8px 0 0}.fallback li{display:grid;grid-template-columns:120px 1fr 90px;gap:8px;align-items:center;padding:5px 0;border-bottom:1px solid #e5e7eb}.bar-track{height:14px;background:#eff6ff}.bar-fill{display:block;height:100%;background:#2563eb}</style>
<style>.chart-controls{display:flex;gap:6px;margin:4px 0 8px}.chart-controls button{border:1px solid #cbd5e1;border-radius:6px;background:#fff;color:#334155;padding:5px 11px;font:inherit;cursor:pointer}.chart-controls button[aria-pressed="true"]{background:#2563eb;border-color:#2563eb;color:#fff}.chart-controls button:focus-visible{outline:2px solid #1d4ed8;outline-offset:2px}.chart-controls button:disabled{opacity:.45;cursor:not-allowed}</style>
<style>.download-controls{display:flex;flex-wrap:wrap;gap:6px;margin:8px 0 12px}.download-controls button{border:1px solid #2563eb;border-radius:6px;background:#2563eb;color:#fff;padding:6px 11px;font:inherit;cursor:pointer}.download-controls button:focus-visible{outline:2px solid #1d4ed8;outline-offset:2px}</style>
{chart_script}</head><body><div id="erp-root">""".replace("{chart_script}", f'<script defer src="{CHART_JS}"></script>' if chart_data else '')
    return head + "".join(sections) + "</div>" + script + "</body></html>"
