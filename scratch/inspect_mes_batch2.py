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
    
    tables = [
        'mes_scheduling_output',
        'phlsx', 'ctlsx',
        'mes_oi_stop_line', 'mes_oi_allocation_stop_line',
        'cttksxloi', 'mes_oi_ng_confirm', 'dmloi', 'dmnndungmay'
    ]
    
    for tbl in tables:
        print(f"\n==================== TABLE: {tbl} ====================")
        try:
            cur.execute(f"SELECT count(*) FROM public.{tbl}")
            cnt = cur.fetchone()['count']
            print(f"Row count: {cnt:,}")
        except Exception as e:
            conn.rollback()
            print(f"Error count: {e}")
            continue

        cur.execute(f"""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_schema = 'public' AND table_name = '{tbl}'
            ORDER BY ordinal_position
        """)
        cols = cur.fetchall()
        print("Cols (", len(cols), "):", ", ".join([c['column_name'] for c in cols[:20]]))
        if len(cols) > 20:
            print(" ...", ", ".join([c['column_name'] for c in cols[20:40]]))
            
        try:
            cur.execute(f"SELECT * FROM public.{tbl} ORDER BY 1 DESC LIMIT 1")
            sample = cur.fetchone()
            print("Sample 1:")
            for k, v in list(sample.items())[:10]:
                print(f"   {k}: {v}")
        except Exception as e:
            conn.rollback()
            print(f"Error sample: {e}")
