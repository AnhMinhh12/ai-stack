#!/usr/bin/env python3
import time, sys
print("STEP 1: Importing psycopg...", flush=True)
import psycopg
print("STEP 2: Connecting to 10.0.6.2:5410...", flush=True)
t0 = time.time()
try:
    conn = psycopg.connect(
        host='10.0.6.2',
        port=5410,
        dbname='3SERP_HTMP_DATA',
        user='read_htmp',
        password='P@ss@Htmp@W0rd!2025',
        connect_timeout=2
    )
    print(f"STEP 3: Connected in {time.time()-t0:.2f}s", flush=True)
    cur = conn.cursor()
    cur.execute("SET statement_timeout = '2s'")
    print("STEP 4: Querying pg_stat_activity...", flush=True)
    cur.execute("SELECT count(*) FROM pg_stat_activity")
    cnt = cur.fetchone()[0]
    print(f"STEP 5: Current active connections on DB: {cnt}", flush=True)
    conn.close()
    print("STEP 6: Closed.", flush=True)
except Exception as e:
    print(f"STEP ERROR in {time.time()-t0:.2f}s: {e}", flush=True)
