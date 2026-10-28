"""Render reviewed ERP blocks as an isolated Open WebUI Rich UI embed."""
from __future__ import annotations

import json
import base64
from html import escape


# Use local static asset first for fast offline loading, fallback to jsdelivr CDN
CHART_JS_TAG = '<script src="/static/chart.umd.min.js" onerror="this.onerror=null;this.src=\'https://cdn.jsdelivr.net/npm/chart.js@4.5.1/dist/chart.umd.min.js\'"></script>'


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
            f'<button type="button" class="btn-dl btn-{_text(item["name"].rsplit(".", 1)[-1].lower())}" data-download-index="{index}">Tải {_text(item["name"].rsplit(".", 1)[-1].upper())}</button>'
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
            allowed = [k for k in ("bar", "line", "pie") if k in (block.get("allowed_chart_types") or [chart_type])]
            if chart_type not in allowed:
                allowed.insert(0, chart_type)
            chart_data.append({"labels": [str(p.get("category") or "") for p in points],
                               "values": [float(p["quantity"]) for p in points],
                               "label": label, "unit": unit, "kind": chart_type, "allowed": allowed,
                               "x_label": (block.get("x") or {}).get("label") or "Nhóm"})
            peak = max((abs(float(p["quantity"])) for p in points), default=0) or 1
            fallback = "".join(f'<li><span>{_text(p.get("category"))}</span><div class="bar-track"><span class="bar-fill" style="width:{round(abs(float(p["quantity"])) / peak * 100)}%"></span></div><strong>{_text(p.get("quantity"))} {_text(unit)}</strong></li>' for p in points)
            controls = ''.join(
                f'<button type="button" data-chart-index="{index}" data-chart-kind="{k}" aria-pressed="{str(k == chart_type).lower()}"'
                + ('' if k in allowed else ' disabled')
                + f'>{title}</button>'
                for k, title in (("bar", "Cột"), ("line", "Đường"), ("pie", "Tròn")))
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

function applyTheme() {
  try {
    const parentDoc = window.parent && window.parent.document;
    if (parentDoc && parentDoc.documentElement) {
      const isDark = parentDoc.documentElement.classList.contains('dark');
      document.documentElement.setAttribute('data-theme', isDark ? 'dark' : 'light');
      return isDark;
    }
  } catch (e) {}
  document.documentElement.setAttribute('data-theme', 'light');
  return false;
}

const valueLabelPlugin = {
  id: 'valueLabel',
  afterDatasetsDraw(chart) {
    const {ctx, data} = chart;
    const meta = chart.getDatasetMeta(0);
    if (!meta || !meta.data) return;
    const values = data.datasets[0].data || [];
    const total = values.reduce((sum, v) => sum + (Number(v) || 0), 0);
    const isDark = document.documentElement.getAttribute('data-theme') === 'dark';

    meta.data.forEach((element, index) => {
      const val = Number(values[index]) || 0;
      if (val === 0) return;
      const pct = total > 0 ? ((val / total) * 100).toFixed(1) + '%' : '';

      ctx.save();
      ctx.font = 'bold 11px system-ui, -apple-system, sans-serif';
      ctx.textAlign = 'center';

      if (chart.config.type === 'pie') {
        const angle = (element.startAngle + element.endAngle) / 2;
        const radius = element.outerRadius * 0.65;
        const availableWidth = (element.endAngle - element.startAngle) * radius;
        const quantity = formatNumber(val);
        const showQuantity = availableWidth >= ctx.measureText(quantity).width + 12 && element.outerRadius >= 95;

        if (availableWidth >= ctx.measureText(pct).width + 10) {
          ctx.fillStyle = contrastColor(chartColors[index % chartColors.length]);
          ctx.textBaseline = 'middle';
          const x = element.x + Math.cos(angle) * radius;
          const y = element.y + Math.sin(angle) * radius;
          ctx.fillText(pct, x, y + (showQuantity ? -7 : 0));
          if (showQuantity) ctx.fillText(quantity, x, y + 8);
        }
      } else if (chart.config.type === 'bar') {
        ctx.fillStyle = isDark ? '#f1f5f9' : '#1e293b';
        ctx.textBaseline = 'bottom';
        if (element.y != null && element.x != null) {
          ctx.fillText(`${formatNumber(val)} (${pct})`, element.x, element.y - 4);
        }
      } else if (chart.config.type === 'line') {
        ctx.fillStyle = isDark ? '#f1f5f9' : '#1e293b';
        ctx.textBaseline = 'bottom';
        if (element.y != null && element.x != null) {
          ctx.fillText(`${formatNumber(val)}`, element.x, element.y - 8);
        }
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

  const isDark = applyTheme();
  const textColor = isDark ? '#f1f5f9' : '#0f172a';
  const subColor = isDark ? '#94a3b8' : '#64748b';
  const gridColor = isDark ? 'rgba(255,255,255,0.08)' : 'rgba(0,0,0,0.06)';

  if (activeCharts.has(index)) {
    activeCharts.get(index).destroy();
    activeCharts.delete(index);
  }

  canvas.parentElement.style.height = kind === 'pie' ? '320px' : '260px';

  let dataset;
  if (kind === 'pie') {
    dataset = {
      data: item.values,
      backgroundColor: chartColors,
      borderWidth: 2,
      borderColor: isDark ? '#1e293b' : '#ffffff'
    };
  } else if (kind === 'line') {
    dataset = {
      label: item.label,
      data: item.values,
      borderColor: '#2563eb',
      backgroundColor: 'rgba(37,99,235,0.12)',
      borderWidth: 2.5,
      tension: 0.35,
      fill: true,
      pointRadius: 5,
      pointHoverRadius: 7,
      pointBackgroundColor: '#2563eb',
      pointBorderColor: '#ffffff',
      pointBorderWidth: 2
    };
  } else {
    dataset = {
      label: item.label,
      data: item.values,
      backgroundColor: item.values.length > 1 ? chartColors.slice(0, item.values.length) : '#2563eb',
      borderRadius: 6,
      borderWidth: 0,
      maxBarThickness: 56
    };
  }

  const scales = kind === 'pie' ? {} : {
    x: {
      grid: { display: false },
      ticks: { color: subColor, font: { size: 11 } },
      title: { display: !!item.x_label, text: item.x_label, color: subColor, font: { size: 11, weight: '500' } }
    },
    y: {
      beginAtZero: true,
      grace: '15%',
      grid: { color: gridColor },
      ticks: {
        color: subColor,
        font: { size: 11 },
        callback: (v) => formatNumber(v)
      },
      title: { display: !!(item.unit || item.label), text: item.unit || item.label, color: subColor, font: { size: 11, weight: '500' } }
    }
  };

  const legend = kind === 'pie' ? {
    display: true,
    position: 'bottom',
    labels: {
      color: textColor,
      font: { size: 12 },
      padding: 14,
      generateLabels() {
        const total = item.values.reduce((sum, v) => sum + v, 0);
        return item.labels.map((lbl, i) => ({
          text: `${lbl}: ${formatNumber(item.values[i])} ${item.unit} (${total ? ((item.values[i]/total)*100).toFixed(1) : '0.0'}%)`,
          fillStyle: chartColors[i % chartColors.length],
          strokeStyle: isDark ? '#1e293b' : '#ffffff',
          lineWidth: 1,
          hidden: false,
          index: i
        }));
      }
    }
  } : {
    display: false
  };

  const chart = new Chart(canvas, {
    type: kind,
    data: { labels: item.labels, datasets: [dataset] },
    plugins: [valueLabelPlugin],
    options: {
      responsive: true,
      maintainAspectRatio: false,
      animation: false,
      layout: { padding: { top: 18, bottom: 4 } },
      plugins: {
        legend: legend,
        tooltip: {
          enabled: true,
          callbacks: {
            label: function(ctx) {
              const val = ctx.raw;
              const total = item.values.reduce((s, v) => s + v, 0);
              const pct = total ? ((val / total) * 100).toFixed(1) + '%' : '';
              return ` ${formatNumber(val)} ${item.unit}` + (pct ? ` (${pct})` : '');
            }
          }
        }
      },
      scales: scales
    }
  });

  activeCharts.set(index, chart);

  document.querySelectorAll('[data-chart-index="' + index + '"]').forEach(btn => {
    btn.setAttribute('aria-pressed', String(btn.dataset.chartKind === kind));
  });

  reportHeight();
}

function drawCharts() {
  applyTheme();
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
  const height = Math.ceil(Math.max(root.getBoundingClientRect().height, root.scrollHeight) + 24);
  parent.postMessage({type:'iframe:height', height: height}, '*');
}

reportHeight();
window.addEventListener('load', () => { drawCharts(); reportHeight(); setTimeout(reportHeight, 200); });
if (window.ResizeObserver) new ResizeObserver(reportHeight).observe(document.getElementById('erp-root') || document.body);
</script>""".replace("PAYLOAD", payload).replace("DOWNLOADS", download_payload)
    head = """<!doctype html><html lang="vi"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<style>
[hidden]{display:none!important}
html,body{overflow-y:hidden;background:transparent!important}
:root{
  --text-main:#0f172a;--text-sub:#64748b;--border:rgba(0,0,0,0.08);
  --th-bg:rgba(0,0,0,0.03);--tr-hover:rgba(0,0,0,0.02);
  --ctrl-bg:rgba(0,0,0,0.05);--ctrl-active:#ffffff;--ctrl-active-color:#2563eb;
  --ctrl-shadow:0 1px 3px rgba(0,0,0,0.12);
}
[data-theme="dark"]{
  --text-main:#f1f5f9;--text-sub:#94a3b8;--border:rgba(255,255,255,0.1);
  --th-bg:rgba(255,255,255,0.04);--tr-hover:rgba(255,255,255,0.025);
  --ctrl-bg:rgba(255,255,255,0.08);--ctrl-active:rgba(255,255,255,0.18);--ctrl-active-color:#60a5fa;
  --ctrl-shadow:0 1px 3px rgba(0,0,0,0.3);
}
body{font:13px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Inter,sans-serif;color:var(--text-main);margin:0;padding:4px 0}
#erp-root{background:transparent}
.intro{font-size:13px;font-weight:500;color:var(--text-sub);margin:0 0 10px}
.summary{font-weight:600;font-size:13px;color:#0284c7;margin:0 0 10px;padding:6px 10px;background:rgba(2,132,199,0.08);border-left:3px solid #0284c7;border-radius:0 6px 6px 0}
.warning{color:#d97706;font-size:12px;margin:0 0 10px;padding:6px 10px;background:rgba(217,119,6,0.08);border-left:3px solid #d97706;border-radius:0 6px 6px 0}
.download-controls{display:flex;flex-wrap:wrap;gap:8px;margin:6px 0 14px}
.btn-dl{display:inline-flex;align-items:center;gap:6px;padding:6px 13px;border-radius:7px;font-size:12px;font-weight:600;letter-spacing:0.02em;border:none;cursor:pointer;box-shadow:0 1px 2px rgba(0,0,0,0.1);transition:all 0.15s ease}
.btn-dl:hover{transform:translateY(-1px);box-shadow:0 3px 6px rgba(0,0,0,0.15)}
.btn-dl:active{transform:translateY(0)}
.btn-xlsx{background:#059669;color:#ffffff}
.btn-docx{background:#2563eb;color:#ffffff}
.btn-pdf{background:#e11d48;color:#ffffff}
.table-scroll{overflow-x:auto;max-width:100%;border:1px solid var(--border);border-radius:8px;background:transparent;margin-bottom:12px}
table{border-collapse:collapse;width:100%;table-layout:auto;box-sizing:border-box}
th,td{text-align:left;padding:9px 12px;border-bottom:1px solid var(--border);white-space:normal;word-break:break-word;vertical-align:middle}
th{background:var(--th-bg);font-size:11px;font-weight:700;text-transform:uppercase;letter-spacing:0.04em;color:var(--text-sub)}
tbody tr:last-child td{border-bottom:none}
tbody tr:hover{background:var(--tr-hover)}
td:nth-child(4),td:nth-child(5){text-align:right;font-variant-numeric:tabular-nums}
.chart{margin-top:14px;background:transparent;border:none;padding:0;box-shadow:none}
.chart h2{font-size:14px;font-weight:700;margin:0 0 2px;color:var(--text-main)}
.scope{font-size:11px;color:var(--text-sub);margin:0 0 10px}
.chart-controls{display:flex;gap:3px;margin:6px 0 14px;background:var(--ctrl-bg);padding:3px;border-radius:8px;width:fit-content}
.chart-controls button{border:none;border-radius:6px;background:transparent;color:var(--text-sub);padding:5px 14px;font-size:12px;font-weight:500;cursor:pointer;transition:all 0.15s ease}
.chart-controls button:hover:not(:disabled){color:var(--text-main)}
.chart-controls button[aria-pressed="true"]{background:var(--ctrl-active);color:var(--ctrl-active-color);font-weight:600;box-shadow:var(--ctrl-shadow)}
.chart-controls button:disabled{opacity:0.35;cursor:not-allowed}
.canvas-wrap{height:280px;max-width:760px;margin-bottom:8px}
.fallback{padding:0;list-style:none;max-width:760px;margin:8px 0 0}
.fallback li{display:grid;grid-template-columns:140px 1fr 100px;gap:10px;align-items:center;padding:6px 0;border-bottom:1px solid var(--border)}
.bar-track{height:12px;background:rgba(37,99,235,0.1);border-radius:6px;overflow:hidden}
.bar-fill{display:block;height:100%;background:linear-gradient(90deg,#3b82f6,#2563eb);border-radius:6px}
</style>
{chart_script}</head><body><div id="erp-root">""".replace("{chart_script}", CHART_JS_TAG if chart_data else '')
    return head + "".join(sections) + "</div>" + script + "</body></html>"
