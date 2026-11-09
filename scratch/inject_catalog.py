import pprint
import re

# Read current procedure_catalog.py
with open("erp_ai/procedure_catalog.py", "r", encoding="utf-8") as f:
    content = f.read()

# Load the NEW_REPORTS dict from scratch/update_procedure_catalog.py
with open("scratch/update_procedure_catalog.py", "r", encoding="utf-8") as f:
    scratch_code = f.read()

# Execute scratch_code to get NEW_REPORTS
local_vars = {}
exec(scratch_code, {}, local_vars)
new_reports = local_vars["NEW_REPORTS"]

# Format new reports as Python code
formatted_entries = []
for report_id, meta in new_reports.items():
    formatted_entries.append(f'    "{report_id}": ' + pprint.pformat(meta, indent=8, width=120) + ",")

new_code_block = "\n\n" + "\n\n".join(formatted_entries) + "\n"

# Locate the closing brace of REPORT_CATALOG (right before `def normalize_vietnamese`)
split_marker = "\n}\n\n\ndef normalize_vietnamese"
if split_marker not in content:
    # Try alternate spacing
    split_marker = "\n}\n\ndef normalize_vietnamese"

parts = content.split(split_marker)
if len(parts) != 2:
    raise ValueError(f"Could not find exact split marker in procedure_catalog.py (found {len(parts)} parts)")

new_content = parts[0] + ",\n" + new_code_block + "\n}\n\n\ndef normalize_vietnamese" + parts[1]

with open("erp_ai/procedure_catalog.py", "w", encoding="utf-8") as f:
    f.write(new_content)

print("Successfully injected Stage 3 reports into erp_ai/procedure_catalog.py!")

