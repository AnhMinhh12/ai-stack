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

  function mountControls(target, readRows) {
    if (!target.parentElement || target.dataset.htmpExportReady || !readRows().length) return;
    target.dataset.htmpExportReady = '1';
    const controls = document.createElement('div');
    controls.className = 'htmp-table-export';
    for (const [label, format] of [['Tải Excel', 'xlsx'], ['Tải Word', 'docx'], ['In / PDF', 'pdf']]) {
      const button = document.createElement('button');
      button.type = 'button'; button.textContent = label;
      button.addEventListener('click', () => {
        const rows = readRows();
        if (!rows.length) return;
        if (format === 'pdf') printPdf(rows);
        else download(format === 'xlsx' ? xlsx(rows) : docx(rows), `bang-du-lieu.${format}`,
          format === 'xlsx' ? 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet' : 'application/vnd.openxmlformats-officedocument.wordprocessingml.document');
      });
      controls.appendChild(button);
    }
    target.parentElement.insertBefore(controls, target);
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
  style.textContent = '.htmp-table-export{display:flex;gap:6px;flex-wrap:wrap;margin:8px 0}.htmp-table-export button{border:1px solid #64748b;border-radius:6px;padding:5px 10px;background:#fff;color:#0f172a;cursor:pointer;font:inherit}.htmp-table-export button:hover{background:#f1f5f9}';
  document.head.appendChild(style);
  let scheduled = false;
  const schedule = () => { if (scheduled) return; scheduled = true; requestAnimationFrame(() => { scheduled = false; attach(); }); };
  schedule();
  new MutationObserver(schedule).observe(document.documentElement, {childList: true, characterData: true, subtree: true});
})();
