# scratch/stats_mapping.py
import csv
from collections import Counter

with open('docs/evidence/ERP-UI-20261106/continuation/mapping-progress.csv', encoding='utf-8') as f:
    rows = list(csv.DictReader(f))

print(f"Total rows in mapping-progress: {len(rows)}")

types = Counter(r['type_prior'] for r in rows)
print(f"By type_prior: {types}")

has_reports = sum(bool(r['metadata_report_ids']) for r in rows)
has_params = sum(r['metadata_parameters_present'] == 'True' for r in rows)
has_funcs = sum(int(r['same_name_function_definitions'] or 0) > 0 for r in rows)
has_ui_cols = sum(int(r['ui_fields_or_columns_count'] or 0) > 0 for r in rows)

print(f"Has metadata_report_ids: {has_reports} / {len(rows)}")
print(f"Has metadata_parameters_present: {has_params} / {len(rows)}")
print(f"Has same_name_function_definitions: {has_funcs} / {len(rows)}")
print(f"Has observed UI fields/columns: {has_ui_cols} / {len(rows)}")

# Check how many are marked VERIFIED vs UNVERIFIED
api_actual = Counter(r['api_actual'] for r in rows)
db_join = Counter(r['db_join_formula'] for r in rows)
print(f"api_actual: {api_actual}")
print(f"db_join_formula: {db_join}")
