# scratch/summarize_db_metadata.py
import json

with open("scratch/db_metadata_audit.json", "r", encoding="utf-8") as f:
    data = json.load(f)

for k, v in data.items():
    print(f"=== {k.upper()} ===")
    print("  Reports:", len(v["reports"]), [(r.get("state"), r.get("rep_id"), r.get("gridid")) for r in v["reports"]])
    print("  Params:", len(v["params"]), [p.get("column_name") for p in v["params"][:6]])
    print("  Grids:", len(v["grids"]), "fields:", [g.get("fieldname") for g in v["grids"][:6]])
    print("  Routines:", len(v["routines"]), [rt.get("routine_name") for rt in v["routines"]])
