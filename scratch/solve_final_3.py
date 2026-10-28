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
    print("=== Q15: Check intem_log columns ===")
    cols = query("SELECT column_name FROM information_schema.columns WHERE table_name = 'intem_log'")
    col_names = [c['column_name'] for c in cols]
    print("intem_log all cols:", col_names)
    
    # Find item code column
    item_col = [c for c in col_names if 'vt' in c or 'sp' in c or 'code' in c or 'item' in c or 'hang' in c]
    print("Item cols:", item_col)

    res_qc = query("""
        SELECT status_qc, COUNT(*) as c 
        FROM intem_log 
        WHERE data_tem::text LIKE '%%QC7-5146-000%%' OR data_tem2::text LIKE '%%QC7-5146-000%%'
        GROUP BY status_qc
    """)
    print("status_qc distribution:", res_qc)

    res_attn = query("""
        SELECT id_tem, status_qc, data_tem, date0, time0, ma_kho
        FROM intem_log 
        WHERE (data_tem::text LIKE '%%QC7-5146-000%%' OR data_tem2::text LIKE '%%QC7-5146-000%%')
          AND status_qc NOT IN ('OK', '1', '')
        ORDER BY date0 DESC LIMIT 10
    """)
    print("Lots needing attention:", json.dumps(res_attn, ensure_ascii=False, indent=2, default=str))

    print("\n=== Q16: Đơn hàng KH0015 từ 01/10/2026 đến hết 20/10/2026 chưa có giá chuẩn ===")
    # Find all items in SO1 of KH0015 in this period
    so_items = query("""
        SELECT DISTINCT d.ma_vt, v.ten_vt, d.gia2
        FROM ph64 h
        JOIN ct64 d USING(stt_rec)
        LEFT JOIN dmvt v ON d.ma_vt = v.ma_vt
        WHERE h.ma_kh = 'KH0015' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
    """)
    print(f"Tổng số mặt hàng unique trong SO1 của KH0015 kỳ này: {len(so_items)}")
    
    no_std_price = []
    for it in so_items:
        vt = it['ma_vt']
        bg = query("""
            SELECT ma_bang_gia, gia, ngay_bd, ngay_kt, status
            FROM dmbanggiact
            WHERE ma_vt = %s AND ma_kh = 'KH0015'
        """, [vt])
        if not bg or it['gia2'] == 0:
            no_std_price.append({
                "ma_vt": vt,
                "ten_vt": it['ten_vt'],
                "gia_so": it['gia2'],
                "co_trong_banggia": len(bg) > 0,
                "banggia_data": bg
            })
    print(f"Số mặt hàng KHÔNG có giá chuẩn hoặc giá SO = 0: {len(no_std_price)}")
    print(json.dumps(no_std_price, ensure_ascii=False, indent=2, default=str))

    print("\n=== Q18: Giao bù NG vs giao bù hàng thiếu (01/10 - 20/10/2026) ===")
    # Check ph82/ct82 (Hàng bán trả lại)
    tra_lai = query("""
        SELECT h.stt_rec, h.so_ct, h.ngay_ct, h.ma_kh, d.ma_vt, d.so_luong, d.dien_giai, h.dien_giai as h_dien_giai
        FROM ph82 h JOIN ct82 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
    """)
    print("Hàng bán trả lại (ph82/ct82):", tra_lai)

    # Check ph81 với các từ khóa bù, NG, thiếu
    bu_xuat = query("""
        SELECT h.stt_rec, h.so_ct, h.ngay_ct, h.ma_kh, h.ma_gd, d.ma_vt, d.so_luong, d.dien_giai, h.dien_giai as h_dien_giai
        FROM ph81 h JOIN ct81 d USING(stt_rec)
        WHERE d.ma_vt = 'QC7-5146-000' AND h.ngay_ct >= '2026-10-01' AND h.ngay_ct <= '2026-10-20'
          AND (h.dien_giai ILIKE '%%bù%%' OR d.dien_giai ILIKE '%%bù%%' 
               OR h.dien_giai ILIKE '%%ng%%' OR d.dien_giai ILIKE '%%ng%%'
               OR h.dien_giai ILIKE '%%thiếu%%' OR d.dien_giai ILIKE '%%thiếu%%'
               OR h.ma_gd != 1)
    """)
    print("Xuất giao bù trong ph81/ct81:", bu_xuat)

    # Check all transactions in ct70 with ma_ct related to returns or compensations
    ct70_ng = query("""
        SELECT so_ct, ngay_ct, ma_ct, sl_nhap, sl_xuat, ma_kho, dien_giai
        FROM ct70
        WHERE ma_vt = 'QC7-5146-000' AND ngay_ct >= '2026-10-01' AND ngay_ct <= '2026-10-20'
          AND (dien_giai ILIKE '%%bù%%' OR dien_giai ILIKE '%%ng%%' OR dien_giai ILIKE '%%thiếu%%' OR ma_kho = 'KHOQA')
    """)
    print("ct70 liên quan NG/Bù:", ct70_ng)

if __name__ == '__main__':
    main()
