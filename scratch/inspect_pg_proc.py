import psycopg
from erp_ai.native_tools import connection_settings

with psycopg.connect(**connection_settings()) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT proname, proargnames 
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE n.nspname = 'public' 
              AND (proname ILIKE 'gl%' OR proname ILIKE 'mf%' OR proname ILIKE 'qc%' OR proname ILIKE 'po%' OR proname ILIKE 'so%' OR proname ILIKE 'in%' OR proname ILIKE 'mes%')
            ORDER BY proname;
        """)
        rows = cur.fetchall()
        print(f"Total procedures in public schema: {len(rows)}")
        by_prefix = {}
        for name, args in rows:
            prefix = name[:2].lower()
            if name.startswith('mes'): prefix = 'mes'
            by_prefix.setdefault(prefix, []).append((name, len(args) if args else 0))
        for p, items in sorted(by_prefix.items()):
            print(f"Prefix {p} ({len(items)}): {[x[0] for x in items[:8]]}")

