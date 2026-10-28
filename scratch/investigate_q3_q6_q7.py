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

def print_section(title):
    print(f"\n{'='*20} {title} {'='*20}")

def main():
    # ----------------------------------------------------
    # Q3: Lot gần nhất xuất giao tính đến 20/10/2026
    # ----------------------------------------------------
    print_section("CÂU 3: Lot gần nhất xuất giao tính đến 20/10/2026")
    q3 = query("""
        SELECT h.stt_rec, h.so_ct, h.ngay_ct, h.ma_kh, d.ma_vt, d.so_luong, d.ma_lo, d.so_po, d.gia2, d.tien2, d.gia_nt2, d.tien_nt2, h.ma_nt
        FROM ph81 h
        JOIN ct81 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct <= '2026-10-20'
        ORDER BY h.ngay_ct DESC, h.stt_rec DESC
        LIMIT 5
    """)
    for r in q3:
        print(f"Số CT: {r['so_ct']} | Ngày: {r['ngay_ct']} | KH: {r['ma_kh']} | SL: {r['so_luong']} | Lot: '{r['ma_lo']}' | PO: {r['so_po']} | Đơn giá: {r['gia_nt2']} {r['ma_nt']}")

    # ----------------------------------------------------
    # Q4: Doanh thu nguyên tệ vs tiền hạch toán (01/10/2026 - 20/10/2026)
    # ----------------------------------------------------
    print_section("CÂU 4: Tổng SL xuất bán & Doanh thu")
    q4_sum = query("""
        SELECT h.ma_nt, COUNT(DISTINCT h.so_ct) as so_phieu,
               SUM(d.so_luong) as tong_sl,
               SUM(d.tien2) as tong_tien_vnd,
               SUM(d.tien_nt2) as tong_tien_nt
        FROM ph81 h
        JOIN ct81 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
        GROUP BY h.ma_nt
    """)
    print("Q4 Tổng cộng:", json.dumps(q4_sum, ensure_ascii=False, indent=2, default=str))

    # ----------------------------------------------------
    # Q6: Nhập kho (01/10/2026 - 20/10/2026)
    # ----------------------------------------------------
    print_section("CÂU 6: Nhập kho QC7-5146-000")
    # Find user table
    user_tbl = query("SELECT table_name FROM information_schema.tables WHERE table_name LIKE '%user%'")
    print("User tables:", [u['table_name'] for u in user_tbl])
    
    q6 = query("""
        SELECT h.stt_rec, h.so_ct, h.ngay_ct, h.ma_ct, h.user_id0, h.user_id2,
               d.ma_vt, d.so_luong, d.ma_kho, k1.ten_kho as ten_kho_xuat,
               d.ma_khon, k2.ten_kho as ten_kho_nhap, d.ma_lo
        FROM ph74 h
        JOIN ct74 d USING(stt_rec)
        LEFT JOIN dmkho k1 ON d.ma_kho = k1.ma_kho
        LEFT JOIN dmkho k2 ON d.ma_khon = k2.ma_kho
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
        ORDER BY h.ngay_ct ASC, h.so_ct ASC
    """)
    print(f"Tổng số bản ghi nhập kho ph74/ct74: {len(q6)}")
    user_ids = set()
    for r in q6:
        user_ids.add(r['user_id0'])
        user_ids.add(r['user_id2'])
        print(f"Phiếu: {r['so_ct']} ({r['ma_ct']}) | Ngày: {r['ngay_ct']} | SL: {r['so_luong']} | Từ kho: {r['ma_kho']} ({r['ten_kho_xuat']}) -> Sang: {r['ma_khon']} ({r['ten_kho_nhap']}) | User0: {r['user_id0']} | User2: {r['user_id2']} | Lot: {r['ma_lo']}")
    
    print("Unique user IDs in q6:", user_ids)
    for utb in [u['table_name'] for u in user_tbl if 'user' in u['table_name']]:
        try:
            users = query(f"SELECT * FROM {utb} WHERE user_id IN ({','.join(str(x) for x in user_ids if x is not None)})")
            if users:
                print(f"Users in {utb}:", json.dumps(users, ensure_ascii=False, indent=2, default=str))
        except Exception:
            pass

    # Check other receipt tables like ph71/ct71
    q6_71 = query("""
        SELECT h.so_ct, h.ngay_ct, h.ma_ct, h.user_id0, d.ma_vt, d.so_luong, d.ma_kho, d.ma_lo
        FROM ph71 h JOIN ct71 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
    """)
    print("Trong ph71/ct71:", q6_71)

    # ----------------------------------------------------
    # Q7: So sánh DO và FCST hiện tại với bản trước
    # ----------------------------------------------------
    print_section("CÂU 7: DO và FCST của QC7-5146-000")
    # Check tables with do, fcst
    for pat in ['%fcst%', '%forecast%', '%ph96%', '%ct96%']:
        tbs = query(f"SELECT table_name FROM information_schema.tables WHERE table_schema='public' AND table_name LIKE '{pat}'")
        for tb in [t['table_name'] for t in tbs]:
            try:
                cnt = query(f"SELECT COUNT(*) as c FROM {tb} WHERE ma_vt = 'QC7-5146-000'")
                print(f"Table {tb}: {cnt[0]['c']} rows for QC7-5146-000")
                if cnt[0]['c'] > 0:
                    sample = query(f"SELECT * FROM {tb} WHERE ma_vt = 'QC7-5146-000' LIMIT 5")
                    print(f"  Sample {tb}:", json.dumps(sample, ensure_ascii=False, indent=2, default=str))
            except Exception as e:
                # check column names
                pass

if __name__ == '__main__':
    main()
