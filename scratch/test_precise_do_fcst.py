#!/usr/bin/env python3
import json
import psycopg
from psycopg.rows import dict_row

CONN_PARAMS = {
    "host": "10.0.6.2",
    "port": 5410,
    "dbname": "3SERP_HTMP_DATA",
    "user": "read_htmp",
    "password": "P@ss@Htmp@W0rd!2025",
    "connect_timeout": 5
}

def query(sql, params=None):
    with psycopg.connect(**CONN_PARAMS, row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params or ())
            return cur.fetchall()

def main():
    material_code = "QC7-5146-000"
    with psycopg.connect(**CONN_PARAMS) as conn:
        with conn.cursor() as cursor:
            # FCST comparison
            cursor.execute("""
                SELECT DISTINCT id, date0
                FROM public.mfkhsx_po_fc
                WHERE upper(trim(ma_vt)) = %s AND nguon_du_lieu = 'FC'
                ORDER BY date0 DESC, id DESC
                LIMIT 2
            """, (material_code,))
            fc_runs = cursor.fetchall()
            print("FC runs:", fc_runs)

            cur_fc, prev_fc = 0, 0
            if len(fc_runs) >= 2:
                cursor.execute("""
                    SELECT sum(so_luong) FROM public.mfkhsx_po_fc
                    WHERE upper(trim(ma_vt)) = %s AND nguon_du_lieu = 'FC' AND id = %s
                """, (material_code, fc_runs[0][0]))
                cur_fc = int(cursor.fetchone()[0] or 0)

                cursor.execute("""
                    SELECT sum(so_luong) FROM public.mfkhsx_po_fc
                    WHERE upper(trim(ma_vt)) = %s AND nguon_du_lieu = 'FC' AND id = %s
                """, (material_code, fc_runs[1][0]))
                prev_fc = int(cursor.fetchone()[0] or 0)

            diff_fc = cur_fc - prev_fc
            print(f"FCST hiện tại: {cur_fc:,} PCS | Bản trước: {prev_fc:,} PCS | Diff: {diff_fc:+,} PCS")

            # DO comparison
            cursor.execute("""
                SELECT h.so_ct, h.ngay_ct, d.so_luong
                FROM public.ph96 h JOIN public.ct96 d USING(stt_rec)
                WHERE upper(trim(d.ma_vt)) = %s
                ORDER BY h.ngay_ct DESC, h.stt_rec DESC
                LIMIT 2
            """, (material_code,))
            do_rows = cursor.fetchall()
            print("DO rows:", do_rows)
            cur_do = int(do_rows[0][2]) if len(do_rows) >= 1 else 0
            prev_do = int(do_rows[1][2]) if len(do_rows) >= 2 else 0
            diff_do = cur_do - prev_do
            print(f"DO gần nhất: {cur_do:,} PCS | DO trước: {prev_do:,} PCS | Diff: {diff_do:+,} PCS")

if __name__ == '__main__':
    main()
