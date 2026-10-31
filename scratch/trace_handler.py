import sys, sqlite3

sys.path.insert(0, '/app/backend')
con = sqlite3.connect('/app/backend/data/webui.db')
content = con.cursor().execute("SELECT content FROM tool WHERE id = 'htmp_postgres_query'").fetchone()[0]
scope = {}
exec(content, scope)
t = scope['Tools']()

q = "khuôn 4509 có bao nhiêu cavity"

# Check handlers individually:
print("mold_shot_and_demand:", t._mold_shot_and_demand(q))
print("mold_profile_register:", t._mold_profile_register(q))
