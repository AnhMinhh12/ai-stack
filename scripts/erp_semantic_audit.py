#!/usr/bin/env python3
"""Cross-check report manifest references against a read-only schema inventory.

This is an audit, not a SQL generator or approval of business definitions.
"""
import argparse
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCE = re.compile(r'(?<![\w.])([A-Za-z_][\w]*)\.([A-Za-z_][\w]*)(?![\w.])')


def build_audit(root, schema):
    tables = {item['table_name'] for item in schema['tables'] if item['table_schema'] == 'public'}
    columns = {(item['table_name'], item['column_name']) for item in schema['columns'] if item['table_schema'] == 'public'}
    reports = []
    for path in sorted((root / 'config/erp-reports').glob('*.json')):
        manifest = json.loads(path.read_text(encoding='utf-8'))
        sources = manifest.get('sources', [])
        if not isinstance(sources, list):
            raise ValueError('invalid report sources')
        source_names = [s.removeprefix('public.') for s in sources if isinstance(s, str)]
        mappings = manifest.get('ui_column_mapping', {})
        if not isinstance(mappings, dict):
            mappings = {}
        checked = []
        for field, expression in mappings.items():
            if not isinstance(expression, str):
                continue
            # Only direct names matching declared source tables can be checked;
            # SQL aliases, formulas and joins are deliberately not inferred.
            refs = sorted(set(REFERENCE.findall(expression)))
            direct = [(table, column) for table, column in refs if table in source_names]
            if direct:
                checked.append({'field': field, 'expression': expression,
                                'references': [{'table': t, 'column': c, 'exists': (t, c) in columns}
                                               for t, c in direct]})
        reports.append({'id': manifest['id'], 'title': manifest.get('title', ''),
                        'manifest': str(path.relative_to(root)),
                        'validation': manifest.get('validation', {}),
                        'sources': [{'name': name, 'visible': name in tables} for name in source_names],
                        'checked_mappings': checked})
    return {'version': 1, 'schema_captured_at_utc': schema.get('captured_at_utc'),
            'warning': 'Structural checks only; neither authorization nor business validation.',
            'reports': reports}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--schema', required=True)
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    schema = json.loads(Path(args.schema).read_text(encoding='utf-8'))
    audit = build_audit(ROOT, schema)
    Path(args.output).write_text(json.dumps(audit, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    refs = [ref for report in audit['reports'] for mapping in report['checked_mappings'] for ref in mapping['references']]
    print(f"reports={len(audit['reports'])} direct_references={len(refs)} missing_columns={sum(not ref['exists'] for ref in refs)}")


if __name__ == '__main__':
    main()
