import re
import json
import psycopg
from decimal import Decimal

DB_KWARGS = dict(host='10.0.6.2', port=5410, dbname='3SERP_HTMP_DATA', user='read_htmp', password='P@ss@Htmp@W0rd!2025')

def test_q10_customer_code(question: str):
    print("=== TEST Q10: CUSTOMER CODE ===")
    normalized = question.lower()
    search_term = ""
    if "atsumitec" in normalized:
        search_term = "atsumitec"
    elif "canon" in normalized:
        if "que vo" in normalized:
            search_term = "que vo"
        elif "tien son" in normalized:
            search_term = "tien son"
        elif "thang long" in normalized:
            search_term = "thang long"
        else:
            search_term = "canon"
    elif "tenma" in normalized:
        search_term = "tenma"
    elif "luxshare" in normalized:
        search_term = "luxshare"
    elif "funing" in normalized:
        search_term = "funing"
    else:
        m = re.search(r"(?:khách hàng|khach hang|khách|khach)\s+([A-Za-z0-9_\-\.\s]+?)(?:\s+(?:có|co|là|la|mã|ma|\?|$))", question, re.I)
        if m:
            search_term = m.group(1).strip()
    
    with psycopg.connect(**DB_KWARGS) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT ma_kh, ten_kh, coalesce(ten_kh2, '') 
                FROM public.dmkh
                WHERE lower(ten_kh) ILIKE %s OR lower(coalesce(ten_kh2, '')) ILIKE %s OR lower(ma_kh) = %s
                ORDER BY ma_kh LIMIT 5
            """, (f"%{search_term}%", f"%{search_term}%", search_term.lower()))
            rows = cur.fetchall()
            print(f"Query '{search_term}': {rows}")

def test_q9_unlinked_prices(question: str):
    print("\n=== TEST Q9: UNLINKED PRICES ===")
    cust_match = re.search(r"\b(KH\d+|NCC\d+)\b", question, re.I)
    customer_code = cust_match.group(1).upper() if cust_match else "KH0062"
    with psycopg.connect(**DB_KWARGS) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT DISTINCT d.ma_vt, coalesce(v.ten_vt, d.ma_vt) AS ten_vt, count(*) as so_dong
                FROM public.ph64 h JOIN public.ct64 d USING(stt_rec)
                LEFT JOIN public.dmvt v ON d.ma_vt = v.ma_vt
                WHERE upper(trim(h.ma_kh)) = %s
                  AND d.ma_vt NOT IN (
                      SELECT DISTINCT ma_vt FROM public.dmbanggiact WHERE upper(trim(ma_kh)) = %s AND gia > 0
                  )
                GROUP BY d.ma_vt, coalesce(v.ten_vt, d.ma_vt)
                ORDER BY d.ma_vt
            """, (customer_code, customer_code))
            rows = cur.fetchall()
            print(f"Customer {customer_code} unlinked count: {len(rows)}")
            for r in rows[:3]:
                print("  Sample:", r)

def test_q3_mold_shots(question: str):
    print("\n=== TEST Q3: MOLD SHOTS & LIFE EXPECTANCY ===")
    material_code = "H131-TBT-H612"
    with psycopg.connect(**DB_KWARGS) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT h.ma_khuon, h.ten_khuon, h.tong_so_shot, h.so_shot_bh, coalesce(h.so_cavity, 1), coalesce(s.ma_sp, '')
                FROM public.dmhosokhuon h
                JOIN public.dmhosokhuonsp s USING(ma_khuon)
                WHERE upper(trim(s.ma_sp)) = %s
                ORDER BY h.tong_so_shot DESC
            """, (material_code,))
            molds = cur.fetchall()
            print(f"Molds for {material_code}: {molds}")
            cur.execute("""
                SELECT nguon_du_lieu, sum(so_luong)
                FROM public.mfkhsx_po_fc
                WHERE ma_vt = %s AND id = '20261102001'
                GROUP BY nguon_du_lieu
            """, (material_code,))
            demands = cur.fetchall()
            print(f"Demands for {material_code}: {demands}")

def test_q8_voucher_completion(question: str):
    print("\n=== TEST Q8: VOUCHER COMPLETION ===")
    so_ct = "001-2611-000004"
    with psycopg.connect(**DB_KWARGS) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT h.so_ct, h.ngay_ct, h.date2, h.time2, u.user_name, u.ten, u.phong_ban,
                       h.ma_kh, k.ten_kh, count(d.stt_rec), sum(d.so_luong), sum(d.tien2)
                FROM public.ph81 h
                JOIN public.ct81 d USING(stt_rec)
                LEFT JOIN public.userinfo u ON h.user_id0 = u.user_id
                LEFT JOIN public.dmkh k ON h.ma_kh = k.ma_kh
                WHERE h.so_ct = %s
                GROUP BY h.so_ct, h.ngay_ct, h.date2, h.time2, u.user_name, u.ten, u.phong_ban, h.ma_kh, k.ten_kh
            """, (so_ct,))
            row = cur.fetchone()
            print(f"Voucher {so_ct} completed: {row}")

def test_q11_ng_reconciliation():
    print("\n=== TEST Q11: NG RECONCILIATION ===")
    with psycopg.connect(**DB_KWARGS) as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT count(DISTINCT h.stt_rec), count(d.stt_rec), coalesce(sum(d.so_luong), 0)
                FROM public.ph76 h JOIN public.ct76 d USING(stt_rec)
                WHERE h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-31'
            """)
            r_hdf = cur.fetchone()
            cur.execute("""
                SELECT count(DISTINCT h.stt_rec), count(d.stt_rec), coalesce(sum(d.so_luong), 0), coalesce(sum(d.tien2), 0)
                FROM public.ph81 h JOIN public.ct81 d USING(stt_rec)
                JOIN public.ph64 s ON d.stt_rec_so1 = s.stt_rec
                WHERE s.ma_gd = '10' AND h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-31'
            """)
            r_hda = cur.fetchone()
            print(f"NG Received (HDF): {r_hdf}")
            print(f"NG Compensated (HDA ma_gd=10): {r_hda}")

test_q10_customer_code("khách hàng ATSUMITEC có mã khách hàng là gì")
test_q9_unlinked_prices("Khách hàng KH0062 có mã hàng nào chưa link được giá trên ERP không?")
test_q3_mold_shots("Khuôn H131-TBT-H612 đã chạy được bao nhiêu shots? Theo demand của khách hàng thì dự kiến khi nào hết tuổi thọ khuôn?")
test_q8_voucher_completion("lệnh giao hàng 001-2611-000004 được hoàn thiện khi nào lấy theo thời gian kho hoàn thành lệnh out hàng ra khỏi hệ thống")
test_q11_ng_reconciliation()
