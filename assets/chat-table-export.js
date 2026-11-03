(() => {
  'use strict';

  const encoder = new TextEncoder();
  const xml = value => String(value ?? '').replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g, '')
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;').replace(/'/g, '&apos;');

  function parseTsv(source) {
    const rows = [];
    let row = [], cell = '', quoted = false;
    const input = String(source || '').replace(/^\uFEFF/, '').replace(/\r\n?/g, '\n');
    for (let i = 0; i < input.length; i += 1) {
      const char = input[i];
      if (char === '"') {
        if (quoted && input[i + 1] === '"') { cell += '"'; i += 1; }
        else if (!cell || quoted) quoted = !quoted;
        else cell += char;
      } else if (char === '\t' && !quoted) {
        row.push(cell); cell = '';
      } else if (char === '\n' && !quoted) {
        row.push(cell); rows.push(row); row = []; cell = '';
      } else {
        cell += char;
      }
    }
    if (row.length || cell) { row.push(cell); rows.push(row); }
    const width = Math.max(0, ...rows.map(item => item.length));
    return width >= 2 && rows.length >= 2 ? rows.map(item => [...item, ...Array(width - item.length).fill('')]) : [];
  }

  function crc32(bytes) {
    let crc = -1;
    for (const byte of bytes) {
      crc ^= byte;
      for (let bit = 0; bit < 8; bit += 1) crc = (crc >>> 1) ^ (crc & 1 ? 0xedb88320 : 0);
    }
    return (crc ^ -1) >>> 0;
  }

  function zip(files) {
    const local = [], central = [];
    let offset = 0;
    const u16 = (view, pos, value) => view.setUint16(pos, value, true);
    const u32 = (view, pos, value) => view.setUint32(pos, value >>> 0, true);
    for (const [name, value] of files) {
      const filename = encoder.encode(name), bytes = encoder.encode(value), crc = crc32(bytes);
      const entry = new Uint8Array(30 + filename.length + bytes.length), head = new DataView(entry.buffer);
      u32(head, 0, 0x04034b50); u16(head, 4, 20); u16(head, 6, 0x0800);
      u32(head, 14, crc); u32(head, 18, bytes.length); u32(head, 22, bytes.length);
      u16(head, 26, filename.length);
      entry.set(filename, 30); entry.set(bytes, 30 + filename.length);
      local.push(entry);

      const directory = new Uint8Array(46 + filename.length), dir = new DataView(directory.buffer);
      u32(dir, 0, 0x02014b50); u16(dir, 4, 20); u16(dir, 6, 20); u16(dir, 8, 0x0800);
      u32(dir, 16, crc); u32(dir, 20, bytes.length); u32(dir, 24, bytes.length);
      u16(dir, 28, filename.length); u32(dir, 42, offset);
      directory.set(filename, 46); central.push(directory);
      offset += entry.length;
    }
    const directorySize = central.reduce((total, entry) => total + entry.length, 0);
    const end = new Uint8Array(22), tail = new DataView(end.buffer);
    u32(tail, 0, 0x06054b50); u16(tail, 8, files.length); u16(tail, 10, files.length);
    u32(tail, 12, directorySize); u32(tail, 16, offset);
    const archive = new Uint8Array(offset + directorySize + end.length);
    let position = 0;
    for (const entry of [...local, ...central, end]) { archive.set(entry, position); position += entry.length; }
    return archive;
  }

  function column(index) {
    let name = '';
    for (let n = index + 1; n; n = Math.floor((n - 1) / 26)) name = String.fromCharCode(65 + (n - 1) % 26) + name;
    return name;
  }

  function xlsx(rows) {
    const body = rows.map((row, rowIndex) => `<row r="${rowIndex + 1}">${row.map((value, colIndex) =>
      `<c r="${column(colIndex)}${rowIndex + 1}" t="inlineStr"${rowIndex === 0 ? ' s="1"' : ''}><is><t xml:space="preserve">${xml(value)}</t></is></c>`
    ).join('')}</row>`).join('');
    const last = `${column(rows[0].length - 1)}${rows.length}`;
    const files = [
      ['[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/><Override PartName="/xl/worksheets/sheet1.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/><Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/></Types>'],
      ['_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>'],
      ['xl/workbook.xml', '<?xml version="1.0" encoding="UTF-8"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets><sheet name="Bảng dữ liệu" sheetId="1" r:id="rId1"/></sheets></workbook>'],
      ['xl/_rels/workbook.xml.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet1.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>'],
      ['xl/styles.xml', '<?xml version="1.0" encoding="UTF-8"?><styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><fonts count="2"><font/><font><b/></font></fonts><fills count="1"><fill><patternFill patternType="none"/></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/><xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0"/></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>'],
      ['xl/worksheets/sheet1.xml', `<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews><sheetData>${body}</sheetData><autoFilter ref="A1:${last}"/></worksheet>`],
    ];
    return zip(files);
  }

  function docx(rows) {
    const body = rows.map((row, rowIndex) => `<w:tr>${row.map(value =>
      `<w:tc><w:p><w:r>${rowIndex === 0 ? '<w:rPr><w:b/></w:rPr>' : ''}<w:t xml:space="preserve">${xml(value)}</w:t></w:r></w:p></w:tc>`
    ).join('')}</w:tr>`).join('');
    return zip([
      ['[Content_Types].xml', '<?xml version="1.0" encoding="UTF-8"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types"><Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/><Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/></Types>'],
      ['_rels/.rels', '<?xml version="1.0" encoding="UTF-8"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/></Relationships>'],
      ['word/document.xml', `<?xml version="1.0" encoding="UTF-8"?><w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:rPr><w:b/></w:rPr><w:t>Bảng dữ liệu</w:t></w:r></w:p><w:tbl><w:tblGrid>${rows[0].map(() => '<w:gridCol w:w="2400"/>').join('')}</w:tblGrid>${body}</w:tbl><w:sectPr/></w:body></w:document>`],
    ]);
  }

  function download(bytes, name, mime) {
    const url = URL.createObjectURL(new Blob([bytes], {type: mime}));
    const link = document.createElement('a');
    link.href = url; link.download = name; document.body.appendChild(link); link.click(); link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  }

  function printPdf(rows) {
    const page = window.open('', '_blank');
    if (!page) return;
    const doc = page.document;
    doc.title = 'Bảng dữ liệu';
    const style = doc.createElement('style');
    style.textContent = 'body{font:11px Arial,sans-serif;padding:16px}table{border-collapse:collapse;width:100%}td,th{border:1px solid #888;padding:5px;text-align:left}th{background:#eee}@page{size:landscape;margin:12mm}';
    doc.head.appendChild(style);
    const table = doc.createElement('table');
    rows.forEach((row, index) => {
      const tr = doc.createElement('tr');
      row.forEach(value => { const cell = doc.createElement(index ? 'td' : 'th'); cell.textContent = value; tr.appendChild(cell); });
      table.appendChild(tr);
    });
    doc.body.appendChild(table);
    page.focus(); page.print();
  }

  function readHtmlTable(table) {
    const rows = Array.from(table.querySelectorAll('tr'), tr =>
      Array.from(tr.children).filter(cell => cell.tagName === 'TH' || cell.tagName === 'TD')
        .map(cell => cell.textContent.trim()));
    const width = Math.max(0, ...rows.map(row => row.length));
    return width >= 2 && rows.length >= 2 ? rows.map(row => [...row, ...Array(width - row.length).fill('')]) : [];
  }

  function extractChartData(rows) {
    if (!rows || rows.length < 3) return null;
    const headers = rows[0];
    const dataRows = rows.slice(1).filter(r => {
      const first = (r[0] || '').toLowerCase();
      return !first.includes('tổng') && !first.includes('total') && !first.includes('ghi chú') && !first.includes('(*)') && r.some(c => c && c.trim());
    });
    if (dataRows.length < 2) return null;

    const colStats = headers.map((h, colIdx) => {
      const hLower = h.toLowerCase();
      const isCodeOrId = /stt|#|mã|so_|code|số\s*(ct|hóa|phiếu|đơn|lô|lo|thùng|seri|lot)/i.test(hLower);
      let numCount = 0;
      let validCount = 0;
      dataRows.forEach(r => {
        const raw = (r[colIdx] || '').trim();
        if (!raw) return;
        validCount++;
        const cleaned = raw.replace(/[,\s]/g, '').replace(/VND|PCS|KG|USD|Chiếc|Đồng|phút|min/gi, '');
        if (!isNaN(cleaned) && cleaned !== '') {
          numCount++;
        }
      });
      return { colIdx, header: h, isNumeric: !isCodeOrId && validCount > 0 && (numCount / validCount >= 0.7) };
    });

    const numCols = colStats.filter(c => c.isNumeric);
    if (!numCols.length) return null;

    let valCol = numCols.find(c => /số\s*lượng|tồn|doanh\s*thu|tiền|giá\s*trị|phút|chi\s*phí|shot/i.test(c.header)) || numCols[numCols.length - 1];

    const codeCol = headers.map((h, idx) => ({ h, idx })).find(c => c.idx !== valCol.colIdx && /mã|code/i.test(c.h));
    const nameCol = headers.map((h, idx) => ({ h, idx })).find(c => c.idx !== valCol.colIdx && !/mã|code/i.test(c.h) && /tên|khách|kho|nguyên\s*nhân|máy|lỗi|chi\s*tiết/i.test(c.h));

    const labels = [];
    const values = [];

    dataRows.forEach(r => {
      let label = '';
      if (codeCol && nameCol && codeCol.idx !== nameCol.idx) {
        const cVal = (r[codeCol.idx] || '').trim();
        const nVal = (r[nameCol.idx] || '').trim();
        label = cVal ? (nVal ? `${cVal} (${nVal.slice(0, 15)})` : cVal) : nVal;
      } else if (nameCol) {
        label = (r[nameCol.idx] || '').trim();
      } else if (codeCol) {
        label = (r[codeCol.idx] || '').trim();
      } else {
        const firstText = headers.findIndex((h, idx) => idx !== valCol.colIdx && !colStats[idx].isNumeric);
        label = firstText >= 0 ? (r[firstText] || '').trim() : `Dòng ${labels.length + 1}`;
      }
      if (label.length > 30) label = label.slice(0, 28) + '...';

      const rawVal = (r[valCol.colIdx] || '').trim().replace(/[,\s]/g, '').replace(/VND|PCS|KG|USD|Chiếc|Đồng|phút|min/gi, '');
      const num = parseFloat(rawVal) || 0;
      labels.push(label || `Dòng ${labels.length + 1}`);
      values.push(num);
    });

    return { title: valCol.header, labels, values };
  }

  const chartColors = [
    '#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6',
    '#ec4899', '#06b6d4', '#84cc16', '#f97316', '#6366f1'
  ];

  function ensureChartJs(callback) {
    if (window.Chart) {
      callback();
      return;
    }
    const existing = document.querySelector('script[src*="chart.umd"]');
    if (existing) {
      existing.addEventListener('load', callback);
      return;
    }
    const script = document.createElement('script');
    script.src = '/static/chart.umd.min.js';
    script.onload = callback;
    script.onerror = () => {
      const cdn = document.createElement('script');
      cdn.src = 'https://cdn.jsdelivr.net/npm/chart.js@4.5.1/dist/chart.umd.min.js';
      cdn.onload = callback;
      document.head.appendChild(cdn);
    };
    document.head.appendChild(script);
  }

  function renderChartInContainer(container, chartData, initialType) {
    let currentType = initialType || 'bar';
    let chartInstance = null;

    const isDark = () => document.documentElement.classList.contains('dark');
    const getTextColor = () => isDark() ? '#cbd5e1' : '#334155';
    const getGridColor = () => isDark() ? 'rgba(255, 255, 255, 0.08)' : 'rgba(0, 0, 0, 0.06)';

    container.innerHTML = `
      <div class="htmp-chart-box" style="margin: 10px 0 16px 0; padding: 14px; border-radius: 10px; border: 1px solid var(--chart-border, rgba(148, 163, 184, 0.2)); background: var(--chart-bg, rgba(255, 255, 255, 0.03)); backdrop-filter: blur(4px);">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; flex-wrap: wrap; gap: 8px;">
          <div style="font-weight: 600; font-size: 13px; color: var(--chart-text, inherit);">📊 Biểu đồ trực quan: ${xml(chartData.title)}</div>
          <div class="htmp-chart-tabs" style="display: flex; gap: 5px;">
            <button type="button" class="htmp-chart-tab" data-type="bar" style="border: 1px solid #64748b; border-radius: 6px; padding: 3px 9px; font-size: 12px; cursor: pointer; transition: all 0.15s;">📊 Cột</button>
            <button type="button" class="htmp-chart-tab" data-type="pie" style="border: 1px solid #64748b; border-radius: 6px; padding: 3px 9px; font-size: 12px; cursor: pointer; transition: all 0.15s;">🥧 Tròn</button>
            <button type="button" class="htmp-chart-tab" data-type="line" style="border: 1px solid #64748b; border-radius: 6px; padding: 3px 9px; font-size: 12px; cursor: pointer; transition: all 0.15s;">📈 Đường</button>
          </div>
        </div>
        <div style="position: relative; height: 320px; width: 100%;">
          <canvas></canvas>
        </div>
      </div>
    `;

    const canvas = container.querySelector('canvas');
    const buttons = container.querySelectorAll('.htmp-chart-tab');

    function updateActiveButton() {
      buttons.forEach(b => {
        const active = b.dataset.type === currentType;
        b.style.background = active ? '#2563eb' : (isDark() ? '#1e293b' : '#f8fafc');
        b.style.color = active ? '#ffffff' : (isDark() ? '#e2e8f0' : '#1e293b');
        b.style.borderColor = active ? '#2563eb' : (isDark() ? '#475569' : '#cbd5e1');
        b.style.fontWeight = active ? '600' : 'normal';
      });
    }

    function draw() {
      if (chartInstance) {
        chartInstance.destroy();
      }
      updateActiveButton();

      const textColor = getTextColor();
      const gridColor = getGridColor();
      const colors = chartData.labels.map((_, i) => chartColors[i % chartColors.length]);

      const config = {
        type: currentType,
        data: {
          labels: chartData.labels,
          datasets: [{
            label: chartData.title,
            data: chartData.values,
            backgroundColor: currentType === 'pie' ? colors : (currentType === 'line' ? 'rgba(59, 130, 246, 0.2)' : colors),
            borderColor: currentType === 'line' ? '#3b82f6' : (currentType === 'pie' ? (isDark() ? '#0f172a' : '#ffffff') : colors),
            borderWidth: currentType === 'pie' ? 2 : (currentType === 'line' ? 2 : 1),
            fill: currentType === 'line',
            tension: 0.25
          }]
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: {
              display: currentType === 'pie',
              position: 'right',
              labels: {
                color: textColor,
                boxWidth: 12,
                font: { size: 11 }
              }
            },
            tooltip: {
              callbacks: {
                label: function(context) {
                  const val = context.raw || 0;
                  const formatted = new Intl.NumberFormat('vi-VN').format(val);
                  if (currentType === 'pie') {
                    const total = chartData.values.reduce((a, b) => a + b, 0);
                    const pct = total > 0 ? ((val / total) * 100).toFixed(1) : 0;
                    return ` ${context.label}: ${formatted} (${pct}%)`;
                  }
                  return ` ${context.dataset.label || ''}: ${formatted}`;
                }
              }
            }
          },
          scales: currentType === 'pie' ? {} : {
            x: {
              ticks: {
                color: textColor,
                font: { size: 11 },
                maxRotation: 45,
                minRotation: 0
              },
              grid: { color: gridColor }
            },
            y: {
              ticks: {
                color: textColor,
                font: { size: 11 },
                callback: function(val) {
                  return new Intl.NumberFormat('vi-VN', { notation: 'compact' }).format(val);
                }
              },
              grid: { color: gridColor }
            }
          }
        }
      };

      chartInstance = new window.Chart(canvas, config);
    }

    buttons.forEach(b => {
      b.addEventListener('click', () => {
        currentType = b.dataset.type;
        draw();
      });
    });

    draw();

    return {
      destroy: () => chartInstance && chartInstance.destroy(),
      redraw: () => draw()
    };
  }

  function mountControls(target, readRows) {
    if (!target.parentElement || target.dataset.htmpExportReady || !readRows().length) return;
    target.dataset.htmpExportReady = '1';
    const rows = readRows();
    const chartData = extractChartData(rows);

    const controls = document.createElement('div');
    controls.className = 'htmp-table-export';

    for (const [label, format] of [['Tải Excel', 'xlsx'], ['Tải Word', 'docx'], ['In / PDF', 'pdf']]) {
      const button = document.createElement('button');
      button.type = 'button'; button.textContent = label;
      button.addEventListener('click', () => {
        const curRows = readRows();
        if (!curRows.length) return;
        if (format === 'pdf') printPdf(curRows);
        else download(format === 'xlsx' ? xlsx(curRows) : docx(curRows), `bang-du-lieu.${format}`,
          format === 'xlsx' ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document');
      });
      controls.appendChild(button);
    }

    let chartContainer = null;
    let chartRenderer = null;

    if (chartData) {
      const chartBtn = document.createElement('button');
      chartBtn.type = 'button';
      chartBtn.className = 'htmp-chart-toggle-btn';
      chartBtn.textContent = '📊 Biểu đồ';
      chartBtn.style.fontWeight = '500';

      chartContainer = document.createElement('div');
      chartContainer.className = 'htmp-chart-wrapper';
      chartContainer.style.display = 'none';
      chartContainer.style.width = '100%';

      chartBtn.addEventListener('click', () => {
        const isHidden = chartContainer.style.display === 'none';
        if (isHidden) {
          chartContainer.style.display = 'block';
          chartBtn.style.background = '#2563eb';
          chartBtn.style.color = '#ffffff';
          chartBtn.style.borderColor = '#2563eb';
          ensureChartJs(() => {
            if (!chartRenderer) {
              chartRenderer = renderChartInContainer(chartContainer, chartData, chartData.labels.length <= 6 ? 'pie' : 'bar');
            } else {
              chartRenderer.redraw();
            }
          });
        } else {
          chartContainer.style.display = 'none';
          chartBtn.style.background = '';
          chartBtn.style.color = '';
          chartBtn.style.borderColor = '';
        }
      });

      controls.appendChild(chartBtn);

      // Tự động mở biểu đồ cho các bảng báo cáo tổng hợp (dưới 15 dòng)
      if (chartData.labels.length >= 2 && chartData.labels.length <= 15) {
        setTimeout(() => {
          if (chartContainer && chartContainer.style.display === 'none') {
            chartBtn.click();
          }
        }, 150);
      }
    }

    target.parentElement.insertBefore(controls, target);
    if (chartContainer) {
      target.parentElement.insertBefore(chartContainer, target);
    }
  }

  function attach() {
    for (const code of document.querySelectorAll('pre code')) {
      const pre = code.closest('pre');
      if (pre) mountControls(pre, () => parseTsv(code.textContent));
    }
    for (const table of document.querySelectorAll('.markdown-prose table')) {
      mountControls(table, () => readHtmlTable(table));
    }
  }

  if (typeof module !== 'undefined' && module.exports) module.exports = {parseTsv, xlsx, docx, readHtmlTable};
  if (typeof document === 'undefined') return;
  const style = document.createElement('style');
  style.textContent = `
    .htmp-table-export { display: flex; gap: 6px; flex-wrap: wrap; margin: 8px 0; align-items: center; }
    .htmp-table-export button { border: 1px solid #cbd5e1; border-radius: 6px; padding: 5px 11px; background: #ffffff; color: #0f172a; cursor: pointer; font-size: 12px; font-weight: 500; transition: all 0.15s; }
    .htmp-table-export button:hover { background: #f1f5f9; }
    .dark .htmp-table-export button { border-color: #475569; background: #1e293b; color: #f1f5f9; }
    .dark .htmp-table-export button:hover { background: #334155; }
    .htmp-chart-toggle-btn { border-color: #3b82f6 !important; color: #2563eb !important; }
    .dark .htmp-chart-toggle-btn { color: #60a5fa !important; border-color: #3b82f6 !important; }
    .htmp-chart-box { box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -2px rgba(0, 0, 0, 0.1); }
  `;
  document.head.appendChild(style);
  let scheduled = false;
  const schedule = () => { if (scheduled) return; scheduled = true; requestAnimationFrame(() => { scheduled = false; attach(); }); };
  schedule();
  new MutationObserver(schedule).observe(document.documentElement, {childList: true, characterData: true, subtree: true});
})();
