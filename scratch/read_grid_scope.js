// scratch/read_grid_scope.js
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

  // Read AngularJS grid data and columns
  const evalRes = await cmd('Runtime.evaluate', {
    expression: `(() => {
      // Find jqGrid data
      const grid = $('#gview_grid, .ui-jqgrid-bdiv table, table[id^=grid]').first();
      let gridData = [];
      try {
        const id = grid.attr('id') || 'grid';
        gridData = $('#' + id).jqGrid('getGridParam', 'data') || [];
      } catch(e) {}

      // Also get table rows directly from DOM
      const rows = [...document.querySelectorAll('.ui-jqgrid-bdiv tr.jqgrow, table.table tbody tr')].map(tr => {
        return [...tr.querySelectorAll('td')].map(td => td.innerText.trim());
      });

      // Get colModel
      let colModel = [];
      try {
        colModel = $('#grid').jqGrid('getGridParam', 'colModel') || [];
      } catch(e) {}

      // Get filter form scope values
      let filterScope = {};
      try {
        const el = document.querySelector('form, [ng-controller]');
        if (window.angular && el) {
          const sc = angular.element(el).scope();
          filterScope = sc.searchDynamic || sc.formData || sc.model || {};
        }
      } catch(e) {}

      return JSON.stringify({
        url: location.href,
        title: document.title,
        rowCount: rows.length,
        rows: rows.slice(0, 5),
        gridDataSample: gridData.slice(0, 3),
        colModelNames: colModel.map(c => ({ name: c.name, label: c.label, hidden: c.hidden })),
        filterScope
      });
    })()`,
    returnByValue: true
  });

  console.log(evalRes.result?.result?.value);
  ws.close();
}

run().catch(console.error);
