#!/usr/bin/env python3
import psycopg
import time
import json

def get_connection():
    return psycopg.connect(
        host='10.0.6.2',
        port=5410,
        dbname='3SERP_HTMP_DATA',
        user='read_htmp',
        password='P@ss@Htmp@W0rd!2025',
        connect_timeout=3
    )

CANDIDATES = [
    # Bán hàng
    'ph81', 'ct81', 'ph64', 'ct64', 'phso1', 'ctso1', 'ctkhgh',
    'ph96', 'ct96', 'phgh', 'ctgh',
    # Mua hàng
    'php01', 'ctp01', 'ph31', 'ct31', 'phpo', 'ctpo', 'ph41', 'ct41',
    'ph71', 'ct71', 'phnk', 'ctnk', 'phnh', 'ctnh',
    # Kho vận
    'ct70', 'cdvt', 'ph74', 'ct74', 'dmkho', 'cdvtlo', 'ct70lo',
    # Bảng giá & Khuôn
    'dmbanggia', 'dmbanggiact', 'dmbg', 'ctbg',
    'dmhosokhuon', 'dmkhuon', 'tbkhuon',
    # Danh mục dùng chung
    'dmkh', 'sys_dmtt', 'sys_listoptions'
]

def main():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SET statement_timeout = '3s'")
    cur.execute("SET lock_timeout = '1s'")
    
    results = {}
    for tbl in CANDIDATES:
        cur.execute("""
            SELECT c.relname, c.reltuples::bigint
            FROM pg_class c
            JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE n.nspname = 'public' AND c.relname = %s;
        """, (tbl,))
        res = cur.fetchone()
        if res:
            name, approx = res
            results[name] = {"exists": True, "approx_rows": max(0, approx)}
        else:
            results[tbl] = {"exists": False, "approx_rows": 0}

    # For existing tables, get column count & first 10 columns
    for name, info in results.items():
        if info["exists"]:
            cur.execute("""
                SELECT a.attname, format_type(a.atttypid, a.atttypmod)
                FROM pg_attribute a
                JOIN pg_class c ON c.oid = a.attrelid
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relname = %s AND a.attnum > 0 AND NOT a.attisdropped
                ORDER BY a.attnum;
            """, (name,))
            cols = cur.fetchall()
            info["column_count"] = len(cols)
            info["columns"] = [c[0] for c in cols]

    conn.close()

    with open("/home/admin/ai-stack/scratch/batch3_survey_result.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("SAVED_SURVEY_OK")

if __name__ == '__main__':
    main()
