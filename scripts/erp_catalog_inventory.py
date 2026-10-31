#!/usr/bin/env python3
"""Build a reviewable, non-executable inventory of ERP report metadata."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def build_catalog(root):
    root = Path(root)
    reports = []
    errors = []
    for path in sorted((root / 'config/erp-reports').glob('*.json')):
        try:
            raw = path.read_bytes()
            item = json.loads(raw)
            if not isinstance(item, dict) or not isinstance(item.get('id'), str):
                raise ValueError('missing report id')
            validation = item.get('validation', {})
            reports.append({
                'id': item['id'], 'title': item.get('title', ''),
                'phrases': item.get('match_phrases', []),
                'sources': item.get('sources', []),
                'columns': item.get('columns', []),
                'inputs': item.get('inputs', {}),
                'output': item.get('output', {}),
                'execution_context': item.get('execution_context', {}),
                'validation': validation,
                'query_file': item.get('query_file'),
                'provenance': {'path': str(path.relative_to(root)),
                               'sha256': hashlib.sha256(raw).hexdigest()},
            })
        except (OSError, ValueError, TypeError) as exc:
            errors.append({'path': str(path.relative_to(root)), 'error': str(exc)})
    ids = [r['id'] for r in reports]
    duplicates = sorted({i for i in ids if ids.count(i) > 1})
    return {'version': 1, 'purpose': 'inventory_only_not_authorization_or_execution',
            'reports': reports, 'errors': errors, 'duplicate_ids': duplicates}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, help='Output JSON path')
    args = parser.parse_args()
    catalog = build_catalog(ROOT)
    Path(args.output).write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(f"reports={len(catalog['reports'])} errors={len(catalog['errors'])} duplicate_ids={len(catalog['duplicate_ids'])}")
    return bool(catalog['errors'] or catalog['duplicate_ids'])


if __name__ == '__main__':
    raise SystemExit(main())
