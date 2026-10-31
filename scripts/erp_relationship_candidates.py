#!/usr/bin/env python3
"""Extract non-executable relationship candidates from report SQL for review."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# Conservative only: explicit public.table aliases and direct column equality.
TABLE = re.compile(r'\b(?:FROM|JOIN)\s+public\.([a-z_][a-z_0-9]*)\s+(?:AS\s+)?([a-z_][a-z_0-9]*)\b', re.I)
EQUALITY = re.compile(r'\b([a-z_][a-z_0-9]*)\.([a-z_][a-z_0-9]*)\s*=\s*([a-z_][a-z_0-9]*)\.([a-z_][a-z_0-9]*)\b', re.I)


def extract(root, schema):
    columns = {(x['table_name'], x['column_name']) for x in schema['columns'] if x['table_schema'] == 'public'}
    candidates = []
    for manifest_path in sorted((root / 'config/erp-reports').glob('*.json')):
        manifest = json.loads(manifest_path.read_text(encoding='utf-8'))
        filename = manifest.get('query_file')
        if not isinstance(filename, str) or Path(filename).name != filename:
            continue
        path = root / 'sql/erp-reports' / filename
        if not path.is_file():
            continue
        raw = path.read_bytes()
        sql = raw.decode('utf-8')
        aliases = {}
        for table, alias in TABLE.findall(sql):
            aliases.setdefault(alias.lower(), set()).add(table.lower())
        seen = set()
        for a, ac, b, bc in EQUALITY.findall(sql):
            left, right = aliases.get(a.lower(), set()), aliases.get(b.lower(), set())
            if len(left) != 1 or len(right) != 1:
                continue
            x, y = (next(iter(left)), ac.lower()), (next(iter(right)), bc.lower())
            if x == y or x not in columns or y not in columns:
                continue
            key = tuple(sorted((x, y)))
            if key in seen:
                continue
            seen.add(key)
            candidates.append({'left': {'table': key[0][0], 'column': key[0][1]},
                               'right': {'table': key[1][0], 'column': key[1][1]},
                               'report_id': manifest['id'], 'report_validation': manifest.get('validation', {}),
                               'sql_path': str(path.relative_to(root)),
                               'sql_sha256': hashlib.sha256(raw).hexdigest(),
                               'status': 'candidate_requires_review'})
    return {'version': 1, 'warning': 'Heuristic equality candidates only; scope, predicates, cardinality, authorization and business semantics are not verified. Never execute from these candidates.', 'candidates': candidates}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--schema', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    result = extract(ROOT, json.loads(Path(args.schema).read_text(encoding='utf-8')))
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print('candidates=' + str(len(result['candidates'])))


if __name__ == '__main__':
    main()
