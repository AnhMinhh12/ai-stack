// scratch/inspect_top_screens.js
const fs = require('fs');

async function run() {
  const targets = await (await fetch('http://127.0.0.1:19223/json/list')).json();
  const t = targets.find(x => x.type === 'page' && x.url.includes('/Solution/ERP/'));
  if (!t) throw new Error('ERP page unavailable');

  const u = new URL(t.webSocketDebuggerUrl);
  u.hostname = '127.0.0.1';
  u.port = '19223';

  const ws = new WebSocket(u);
  await new Promise((resolve, reject) => {
    ws.onopen = resolve;
    ws.onerror = reject;
  });

  let id = 0;
  const pending = new Map();
  ws.onmessage = e => {
    const m = JSON.parse(e.data);
    if (m.id && pending.has(m.id)) {
      pending.get(m.id)(m);
      pending.delete(m.id);
    }
  };

  function cmd(method, params = {}) {
    let reqId = ++id;
    ws.send(JSON.stringify({ id: reqId, method, params }));
    return new Promise(resolve => pending.set(reqId, resolve));
  }

  const screens = [
    { name: 'Bảng kê đơn hàng bán', hash: '#/SO/Report/SOBKDonHang' },
    { name: 'Bảng kê đơn hàng mua', hash: '#/PO/Report/POBKDonHang' },
    { name: 'Báo cáo tình trạng đơn hàng mua', hash: '#/PO/Report/POStatus' },
    { name: 'Kế hoạch sản xuất', hash: '#/MF/Report/MfTKHSX' },
    { name: 'Báo cáo tồn theo kho', hash: '#/IN/Report/InBCTonTheoKho' }
  ];

  const results = [];

  for (const s of screens) {
    console.log('Navigating to', s.name, s.hash);
    await cmd('Runtime.evaluate', { expression: `location.hash = '${s.hash}'` });
    await new Promise(r => setTimeout(r, 2500));

    const evalRes = await cmd('Runtime.evaluate', {
      expression: `(() => {
        const title = document.title;
        const text = document.body.innerText.slice(0, 3000);
        const filterSection = (document.body.innerText.split('Điều kiện lọc')[1] || '').split('Xem báo cáo')[0].trim();
        const inputs = [...document.querySelectorAll('input, select')].map(inp => {
          const lbl = inp.closest('.form-group')?.querySelector('label')?.innerText.trim() ||
                      inp.closest('tr')?.querySelector('td:first-child')?.innerText.trim() || '';
          return {
            name: inp.name || inp.id || '',
            label: lbl,
            value: inp.value || '',
            placeholder: inp.placeholder || ''
          };
        }).filter(x => x.label || x.name || x.placeholder);

        const ths = [...document.querySelectorAll('th, .ui-jqgrid-labels td, .ui-jqgrid-labels th')].filter(e => e.offsetParent !== null).map(e => e.innerText.trim()).filter(Boolean);

        return JSON.stringify({
          title,
          filterSection: filterSection.slice(0, 1500),
          inputsCount: inputs.length,
          inputsSample: inputs.slice(0, 15),
          columns: [...new Set(ths)].slice(0, 30)
        });
      })()`,
      returnByValue: true
    });

    try {
      const data = JSON.parse(evalRes.result?.result?.value || '{}');
      results.push({ ...s, ...data });
    } catch(e) {
      results.push({ ...s, error: e.message });
    }
  }

  fs.writeFileSync('scratch/top_screens_live_survey.json', JSON.stringify(results, null, 2));
  console.log('Finished top screens live survey! Results saved to scratch/top_screens_live_survey.json');
  ws.close();
}

run().catch(console.error);
