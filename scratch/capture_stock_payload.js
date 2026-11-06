// scratch/capture_stock_payload.js
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
  let capturedResponse = null;

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

  // Navigate to InBCTonTheoKho
  await cmd('Runtime.evaluate', {
    expression: `(() => {
      const span = [...document.querySelectorAll('a span[translate]')].find(e => e.getAttribute('translate') === 'InBCTonTheoKho');
      if (span) span.closest('a').click();
      else location.hash = '#/IN/Report/InBCTonTheoKho';
    })()`
  });

  await new Promise(r => setTimeout(r, 2000));

  // Fill 75577-BZ010 and click button
  const fillRes = await cmd('Runtime.evaluate', {
    expression: `(async () => {
      // Find item input
      const inputs = [...document.querySelectorAll('input')];
      const vtInput = inputs.find(i => i.placeholder?.includes('vật tư') || i.name?.includes('vt') || i.getAttribute('ng-model')?.includes('cma_vt'));
      if (vtInput) {
        vtInput.value = '75577-BZ010';
        vtInput.dispatchEvent(new Event('input', { bubbles: true }));
        vtInput.dispatchEvent(new Event('change', { bubbles: true }));
      }
      return { filled: !!vtInput };
    })()`,
    returnByValue: true
  });
  console.log('Fill result:', fillRes.result?.result?.value);

  // Click 'Xem báo cáo' button
  await cmd('Runtime.evaluate', {
    expression: `(() => {
      const btn = [...document.querySelectorAll('button, input[type=button]')].find(b => b.innerText.includes('Xem báo cáo'));
      if (btn) btn.click();
    })()`
  });

  await new Promise(r => setTimeout(r, 4000));

  // Read the jqGrid rows from DOM
  const tableRes = await cmd('Runtime.evaluate', {
    expression: `(() => {
      const rows = [...document.querySelectorAll('.ui-jqgrid-bdiv tr.jqgrow')].map(tr => {
        return [...tr.querySelectorAll('td')].map(td => td.innerText.trim());
      });
      const headers = [...document.querySelectorAll('th, .ui-jqgrid-labels td, .ui-jqgrid-labels th')].filter(el => el.offsetParent !== null).map(el => el.innerText.trim()).filter(Boolean);
      return JSON.stringify({ headers, rows: rows.slice(0, 10) });
    })()`,
    returnByValue: true
  });

  console.log('Grid Table:', tableRes.result?.result?.value);
  ws.close();
}

run().catch(console.error);
