#!/usr/bin/env python3
import time, sys
print("Starting check_conn...", flush=True)
import psycopg
print("Psycopg imported...", flush=True)
t0 = time.time()
try:
    conn = psycopg.connect(
        host='10.0.6.2',
        port=5410,
        dbname='3SERP_HTMP_DATA',
        user='read_htmp',
        password='P@ss@Htmp@W0rd!2025',
        connect_timeout=3
    )
    print(f"Connected in {time.time()-t0:.2f}s", flush=True)
    conn.close()
except Exception as e:
    print(f"Connection failed in {time.time()-t0:.2f}s: {e}", flush=True)
