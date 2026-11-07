#!/usr/bin/env python3
"""Build a review map from observed UI, catalog candidates and DB schema.

Name/caption matches are leads only: they do not prove runtime lineage or semantics.
The input schema snapshot must be collected separately using read-only SQL.
"""
import argparse
import collections
import csv
import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'docs/evidence/ERP-UI-20261106/continuation'


def folded(s):
    return re.sub(r'[^a-z0-9]+', '', ''.join(c for c in unicodedata.normalize('NFD', (s or '').lower().replace('đ','d')) if unicodedata.category(c) != 'Mn'))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--columns', required=True, help='Read-only DB schema JSON [table,column,type]')
    parser.add_argument('--output', required=True)
    args = parser.parse_args()
    cols = collections.defaultdict(set)
    for table, col, typ in json.loads(Path(args.columns).read_text()):
        cols[table.lower()].add(col.lower())
    ui = {r['state'].lower(): r for r in map(json.loads, (BASE / 'ui-observations.jsonl').read_text().splitlines())}
    functions = collections.defaultdict(list)
    for fn in json.loads((BASE / 'function-candidates.json').read_text())['functions']:
        functions[fn['name'].lower()].append(fn)
    grids = collections.defaultdict(list)
    for row in json.loads((BASE / 'grid-metadata.json').read_text())['rows']:
        grids[row['gridid']].append(row)
    screens = []
    with (ROOT / 'docs/evidence/ERP-UI-20261106/screen-inventory.csv').open(encoding='utf-8-sig', newline='') as f:
        for item in csv.DictReader(f):
            state = item['state']
            obs = ui.get(state.lower())
            # Grid variant suffix must be numeric; do not conflate e.g. Kho and KhoTem.
            selected = {gid:rows for gid,rows in grids.items() if re.fullmatch(re.escape(state) + r'\d*', gid, re.I)}
            headings = [h for h in (obs or {}).get('headings', []) if h and h not in ('×','#')]
            captions = {folded(h) for h in headings if folded(h)}
            fields = []
            for gid, rows in selected.items():
                for row in rows:
                    table = (row.get('tablename') or '').lower().strip()
                    root = (row.get('field_root') or '').lower().strip()
                    caption = row.get('fieldcaption') or ''
                    status = ('metadata_without_physical_source' if not table or not root else
                              'table_not_in_public_schema' if table not in cols else
                              'physical_column_exists_candidate' if root in cols[table] else 'physical_column_missing_or_derived')
                    fields.append({'grid':gid,'field':row.get('fieldname'),'caption':caption,
                                   'source_table_metadata':table,'source_field_metadata':root,
                                   'source_check':status,'caption_matches_observed_heading':bool(folded(caption) and folded(caption) in captions)})
            fns = functions.get(state.lower(), [])
            screens.append({'state':state,'label':item['label_ui'],'module':item['module_prior'],
                'screen_type':item['type_prior'],'ui_observed':bool(obs and obs.get('clicked')),
                'ui_observed_hash':(obs or {}).get('hash'), 'ui_headings':headings,
                'ui_filters_text':(obs or {}).get('filter_text',''),
                'grid_candidates':sorted(selected),'grid_fields':fields,
                'function_candidates':[{'name':x['name'],'sha256':x['source_sha256'],
                    'text_reference_candidates':x['text_reference_candidates'],'keyword_flags':x['keyword_flags']} for x in fns],
                'api_function_link':'unverified','business_formula':'unverified','user_permissions':'unverified',
                'business_approval':'unverified'})
    dest = Path(args.output);dest.mkdir(parents=True,exist_ok=True)
    (dest/'screen-map.json').write_text(json.dumps({'status':'candidate_only_unverified', 'screens':screens},ensure_ascii=False,indent=2))
    with (dest/'screen-summary.csv').open('w',encoding='utf-8-sig',newline='') as f:
        writer=csv.DictWriter(f,fieldnames=['state','label','module','type','ui_observed','ui_headings','grids','grid_fields','physical_column_candidates','missing_or_derived','same_name_functions','business_status']);writer.writeheader()
        for s in screens:
            count=collections.Counter(v['source_check'] for v in s['grid_fields'])
            writer.writerow({'state':s['state'],'label':s['label'],'module':s['module'],'type':s['screen_type'],
                'ui_observed':s['ui_observed'],'ui_headings':len(s['ui_headings']),'grids':'|'.join(s['grid_candidates']),
                'grid_fields':len(s['grid_fields']),'physical_column_candidates':count['physical_column_exists_candidate'],
                'missing_or_derived':count['physical_column_missing_or_derived'],
                'same_name_functions':len(s['function_candidates']),'business_status':'unverified'})
    print(json.dumps({'screens':len(screens),'ui_observed':sum(s['ui_observed'] for s in screens),
        'with_grid_candidates':sum(bool(s['grid_candidates']) for s in screens),
        'with_same_name_function_candidates':sum(bool(s['function_candidates']) for s in screens),
        'fields':sum(len(s['grid_fields']) for s in screens)},ensure_ascii=False))

if __name__ == '__main__': main()
