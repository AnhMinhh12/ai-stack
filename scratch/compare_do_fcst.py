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
    print("=== FCST version comparison for QC7-5146-000 ===")
    fcst_vers = query("""
        SELECT id, date0, nguon_du_lieu, COUNT(*) as so_dong, SUM(so_luong) as tong_sl
        FROM mfkhsx_po_fc
        WHERE ma_vt = 'QC7-5146-000'
        GROUP BY id, date0, nguon_du_lieu
        ORDER BY date0 DESC, id DESC
        LIMIT 10
    """)
    print("FCST versions:", json.dumps(fcst_vers, ensure_ascii=False, indent=2, default=str))

    # Compare the two latest FC versions
    fc_runs = query("""
        SELECT DISTINCT id, date0
        FROM mfkhsx_po_fc
        WHERE ma_vt = 'QC7-5146-000' AND nguon_du_lieu = 'FC'
        ORDER BY date0 DESC
        LIMIT 2
    """)
    if len(fc_runs) >= 2:
        v_current, v_prev = fc_runs[0]['id'], fc_runs[1]['id']
        cur_fc = query("SELECT SUM(so_luong) as sl FROM mfkhsx_po_fc WHERE ma_vt = 'QC7-5146-000' AND nguon_du_lieu = 'FC' AND id = %s", [v_current])[0]['sl']
        prev_fc = query("SELECT SUM(so_luong) as sl FROM mfkhsx_po_fc WHERE ma_vt = 'QC7-5146-000' AND nguon_du_lieu = 'FC' AND id = %s", [v_prev])[0]['sl']
        diff = cur_fc - prev_fc
        print(f"FCST hiện tại ({v_current} ngày {fc_runs[0]['date0']}): {cur_fc:,.0f} PCS")
        print(f"FCST bản trước ({v_prev} ngày {fc_runs[1]['date0']}): {prev_fc:,.0f} PCS")
        print(f"Chênh lệch FCST: {diff:+,.0f} PCS ({'Tăng' if diff > 0 else 'Giảm' if diff < 0 else 'Không đổi'})")

    print("\n=== DO (ph96/ct96) comparison for QC7-5146-000 ===")
    do_runs = query("""
        SELECT h.stt_rec, h.so_ct, h.ngay_ct, h.ngay_gh, d.so_luong
        FROM ph96 h JOIN ct96 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000'
        ORDER BY h.ngay_ct DESC, h.stt_rec DESC
        LIMIT 5
    """)
    for d in do_runs:
        print(f"Lệnh DO: {d['so_ct']} | Ngày CT: {d['ngay_ct']} | Ngày GH: {d['ngay_gh']} | SL: {d['so_luong']}")

if __name__ == '__main__':
    main()
