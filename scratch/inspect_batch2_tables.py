#!/usr/bin/env python3
import psycopg
from psycopg.rows import dict_row

conn = psycopg.connect(
    host='10.0.6.2',
    port=5410,
    dbname='3SERP_HTMP_DATA',
    user='read_htmp',
    password='P@ss@Htmp@W0rd!2025',
    connect_timeout=5
)

with conn.cursor(row_factory=dict_row) as cur:
    cur.execute("SET statement_timeout = 8000")
    
    candidate_tables = ['mes_scheduling', 'mfwo', 'mes_oi_downtime', 'mes_oi_ng', 'mes_oi_ng_linh_kien']
    for tbl in candidate_tables:
        print(f"\n==================== TABLE: {tbl} ====================")
        # Check existence and row count
        try:
            cur.execute(f"SELECT count(*) FROM public.{tbl}")
            cnt = cur.fetchone()['count']
            print(f"Row count: {cnt:,}")
        except Exception as e:
            conn.rollback()
            print(f"Table {tbl} error/not found: {e}")
            continue

        # Columns
        cur.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = '{tbl}'
            ORDER BY ordinal_position
        """)
        cols = cur.fetchall()
        print("Columns (total:", len(cols), "):")
        col_names = [c['column_name'] for c in cols]
        print(", ".join(col_names[:25]))
        if len(col_names) > 25:
            print("...", ", ".join(col_names[25:50]))

        # Indexes
        cur.execute(f"""
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE schemaname = 'public' AND tablename = '{tbl}'
        """)
        indexes = cur.fetchall()
        print("Indexes:")
        for idx in indexes:
            print(" ", idx['indexname'], ":", idx['indexdef'])

        # Sample recent row
        try:
            cur.execute(f"SELECT * FROM public.{tbl} LIMIT 1")
            sample = cur.fetchone()
            print("Sample 1 row keys & values:")
            for k, v in list(sample.items())[:12]:
                print(f"   {k}: {v}")
        except Exception as e:
            conn.rollback()
            print(f"Error fetching sample: {e}")
