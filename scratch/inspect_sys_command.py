import psycopg
from erp_ai.native_tools import connection_settings

with psycopg.connect(**connection_settings()) as conn:
    with conn.cursor() as cur:
        cur.execute("""
            SELECT module, state, text, url 
            FROM sys_command 
            WHERE module IN ('GL', 'VS')
            ORDER BY module, state;
        """)
        rows = cur.fetchall()
        print(f"Total commands for GL and VS: {len(rows)}")
        for m, s, t, u in rows:
            print(f"[{m}] {s:25} | {t:40} | {u}")
