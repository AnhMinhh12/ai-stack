#!/usr/bin/env python3
"""Print a self-contained synthetic evaluation bundle for `docker exec ... python -`."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
paths = [p.relative_to(ROOT).as_posix() for p in (ROOT/'erp_ai').glob('*.py')]
paths += ['config/erp-agent.json','docs/knowledge/erp-sales-agent.md',
          'sql/erp-reports/agent-sales-lines.sql','scripts/evaluate_erp_agent.py']
assets = {p: (ROOT/p).read_text() for p in paths}
print('import json,tempfile,pathlib,runpy,sys')
print('assets=json.loads('+repr(json.dumps(assets))+')')
print('''with tempfile.TemporaryDirectory(prefix="erp-agent-eval-") as tmp:
 root=pathlib.Path(tmp)
 for name,content in assets.items():
  p=root/name; p.parent.mkdir(parents=True,exist_ok=True); p.write_text(content)
 sys.path.insert(0,str(root))
 runpy.run_path(str(root/"scripts/evaluate_erp_agent.py"),run_name="__main__")''')
