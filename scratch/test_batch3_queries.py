#!/usr/bin/env python3
import psycopg
from psycopg.rows import dict_row
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

def test_queries():
    conn = get_connection()
    cur = conn.cursor(row_factory=dict_row)
    cur.execute("SET statement_timeout = '3s'")
    
    print("=" * 80, flush=True)
    print("TESTING BATCH 3 OPTIMIZED SEMANTIC QUERIES", flush=True)
    print("=" * 80, flush=True)

    # 1. SALES ORDER (SO1: ph64 + ct64 + dmvt + sys_dmtt)
    print("\n--- 1. SALES ORDER REGISTER (SO1) ---", flush=True)
    t0 = time.time()
    cur.execute("""
        WITH header AS (
            SELECT stt_rec, so_ct, ngay_ct, ma_kh, ten_kh, so_po, ma_nt, status
            FROM public.ph64
            WHERE ma_ct = 'SO1'
            ORDER BY ngay_ct DESC, stt_rec DESC
            LIMIT 10
        )
        SELECT 
            h.so_ct,
            to_char(h.ngay_ct, 'YYYY-MM-DD') AS ngay_ct,
            h.ma_kh,
            coalesce(k.ten_kh, h.ten_kh) AS ten_kh,
            h.so_po,
            d.ma_vt,
            coalesce(v.ten_vt, d.ma_vt) AS ten_vt,
            d.dvt,
            d.so_luong,
            d.gia2 AS don_gia,
            d.tien2 AS thanh_tien,
            h.ma_nt,
            coalesce(s.statusname, h.status) AS trang_thai
        FROM header h
        JOIN public.ct64 d USING(stt_rec)
        LEFT JOIN public.dmkh k ON k.ma_kh = h.ma_kh
        LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
        LEFT JOIN public.sys_dmtt s ON s.ma_ct = 'SO1' AND s.status = h.status
        ORDER BY h.ngay_ct DESC, h.stt_rec DESC, d.ln;
    """)
    rows1 = cur.fetchall()
    print(f"Query 1 finished in {time.time()-t0:.3f}s, {len(rows1)} rows", flush=True)
    for r in rows1[:3]:
        print(f"  SO: {r['so_ct']} | Ngày: {r['ngay_ct']} | KH: {r['ma_kh']} | VT: {r['ma_vt']} | SL: {r['so_luong']:,.0f} | TT: {r['trang_thai']}", flush=True)

    # 2. SALES SHIPMENT REGISTER (HDA: ph81 + ct81 + dmvt + sys_dmtt)
    print("\n--- 2. SALES SHIPMENT REGISTER (HDA) ---", flush=True)
    t0 = time.time()
    cur.execute("""
        WITH header AS (
            SELECT stt_rec, so_ct, ngay_ct, ma_kh, ten_kh, so_ct_so1, status
            FROM public.ph81
            WHERE ma_ct = 'HDA'
            ORDER BY ngay_ct DESC, stt_rec DESC
            LIMIT 10
        )
        SELECT 
            h.so_ct,
            to_char(h.ngay_ct, 'YYYY-MM-DD') AS ngay_ct,
            h.ma_kh,
            coalesce(k.ten_kh, h.ten_kh) AS ten_kh,
            h.so_ct_so1 AS so_so,
            d.so_po,
            d.ma_vt,
            coalesce(v.ten_vt, d.ma_vt) AS ten_vt,
            d.dvt,
            d.so_luong,
            d.ma_kho,
            coalesce(s.statusname, h.status) AS trang_thai
        FROM header h
        JOIN public.ct81 d USING(stt_rec)
        LEFT JOIN public.dmkh k ON k.ma_kh = h.ma_kh
        LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
        LEFT JOIN public.sys_dmtt s ON s.ma_ct = 'HDA' AND s.status = h.status
        ORDER BY h.ngay_ct DESC, h.stt_rec DESC, d.ln;
    """)
    rows2 = cur.fetchall()
    print(f"Query 2 finished in {time.time()-t0:.3f}s, {len(rows2)} rows", flush=True)
    for r in rows2[:3]:
        print(f"  PXK: {r['so_ct']} | Ngày: {r['ngay_ct']} | KH: {r['ma_kh']} | VT: {r['ma_vt']} | SL: {r['so_luong']:,.0f} | Kho: {r['ma_kho']} | TT: {r['trang_thai']}", flush=True)

    # 3. PURCHASE ORDER REGISTER (PO1: ph94 + ct94 + dmvt + sys_dmtt)
    print("\n--- 3. PURCHASE ORDER REGISTER (PO1) ---", flush=True)
    t0 = time.time()
    cur.execute("""
        WITH header AS (
            SELECT stt_rec, so_ct, ngay_ct, ma_kh, ten_kh, ma_nt, status
            FROM public.ph94
            WHERE ma_ct = 'PO1'
            ORDER BY ngay_ct DESC, stt_rec DESC
            LIMIT 10
        )
        SELECT 
            h.so_ct AS so_po,
            to_char(h.ngay_ct, 'YYYY-MM-DD') AS ngay_po,
            h.ma_kh AS ma_ncc,
            coalesce(k.ten_kh, h.ten_kh) AS ten_ncc,
            d.ma_vt,
            coalesce(v.ten_vt, d.ma_vt) AS ten_vt,
            d.dvt,
            d.so_luong,
            d.gia AS don_gia,
            d.tien AS thanh_tien,
            h.ma_nt,
            coalesce(s.statusname, h.status) AS trang_thai
        FROM header h
        JOIN public.ct94 d USING(stt_rec)
        LEFT JOIN public.dmkh k ON k.ma_kh = h.ma_kh
        LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
        LEFT JOIN public.sys_dmtt s ON s.ma_ct = 'PO1' AND s.status = h.status
        ORDER BY h.ngay_ct DESC, h.stt_rec DESC, d.ln;
    """)
    rows3 = cur.fetchall()
    print(f"Query 3 finished in {time.time()-t0:.3f}s, {len(rows3)} rows", flush=True)
    for r in rows3[:3]:
        print(f"  PO: {r['so_po']} | Ngày: {r['ngay_po']} | NCC: {r['ma_ncc']} | VT: {r['ma_vt']} | SL: {r['so_luong']:,.0f} | Tiền: {r['thanh_tien']:,.0f} | TT: {r['trang_thai']}", flush=True)

    # 4. INTERNAL WAREHOUSE TRANSFERS (ph74 + ct74 + dmvt + dmkho)
    print("\n--- 4. INTERNAL WAREHOUSE TRANSFERS (PND/PXA) ---", flush=True)
    t0 = time.time()
    cur.execute("""
        WITH header AS (
            SELECT stt_rec, so_ct, ngay_ct, ma_ct, dien_giai, status
            FROM public.ph74
            ORDER BY ngay_ct DESC, stt_rec DESC
            LIMIT 10
        )
        SELECT 
            h.so_ct,
            to_char(h.ngay_ct, 'YYYY-MM-DD') AS ngay_ct,
            h.ma_ct AS loai_phieu,
            d.ma_vt,
            coalesce(v.ten_vt, d.ma_vt) AS ten_vt,
            d.dvt,
            d.ma_kho,
            coalesce(w.ten_kho, d.ma_kho) AS ten_kho,
            d.so_luong,
            h.dien_giai,
            coalesce(s.statusname, h.status) AS trang_thai
        FROM header h
        JOIN public.ct74 d USING(stt_rec)
        LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
        LEFT JOIN public.dmkho w ON w.ma_kho = d.ma_kho
        LEFT JOIN public.sys_dmtt s ON s.ma_ct = h.ma_ct AND s.status = h.status
        ORDER BY h.ngay_ct DESC, h.stt_rec DESC, d.ln;
    """)
    rows4 = cur.fetchall()
    print(f"Query 4 finished in {time.time()-t0:.3f}s, {len(rows4)} rows", flush=True)
    for r in rows4[:3]:
        print(f"  Phiếu: {r['so_ct']} ({r['loai_phieu']}) | Ngày: {r['ngay_ct']} | Kho: {r['ma_kho']} | VT: {r['ma_vt']} | SL: {r['so_luong']:,.0f} | Diễn giải: {r['dien_giai']}", flush=True)

    # 5. MOLD PROFILE (dmhosokhuon)
    print("\n--- 5. MOLD PROFILE REGISTER (dmhosokhuon) ---", flush=True)
    t0 = time.time()
    cur.execute("""
        SELECT 
            m.ma_khuon,
            m.ten_khuon,
            to_char(m.ngay, 'YYYY-MM-DD') AS ngay_su_dung,
            to_char(m.ngay_bh, 'YYYY-MM-DD') AS ngay_bao_hiem,
            m.so_cavity,
            m.so_shot_bh AS tuoi_tho_shot_dinh_muc,
            m.loai_gate,
            m.so_cong_hot,
            m.so_cong_van_dau
        FROM public.dmhosokhuon m
        ORDER BY m.ngay DESC NULLS LAST, m.ma_khuon
        LIMIT 5;
    """)
    rows5 = cur.fetchall()
    print(f"Query 5 finished in {time.time()-t0:.3f}s, {len(rows5)} rows", flush=True)
    for r in rows5[:3]:
        print(f"  Khuôn: {r['ma_khuon']} | Tên: {r['ten_khuon']} | Cavity: {r['so_cavity']} | Tuổi thọ shot: {r['tuoi_tho_shot_dinh_muc']:,.0f} | Ngày BH: {r['ngay_bao_hiem']}", flush=True)

    # 6. SALES PRICE LIST (dmbanggia + dmbanggiact + dmvt)
    print("\n--- 6. SALES PRICE LIST REGISTER (dmbanggia + dmbanggiact) ---", flush=True)
    t0 = time.time()
    cur.execute("""
        SELECT 
            b.ma_bang_gia,
            b.ten_bang_gia,
            c.ma_vt,
            coalesce(v.ten_vt, c.ma_vt) AS ten_vt,
            c.dvt,
            c.ma_kh,
            coalesce(k.ten_kh, c.ma_kh) AS ten_kh,
            c.gia AS don_gia_ban,
            c.ma_nt,
            c.sl_min,
            to_char(c.ngay_bd, 'YYYY-MM-DD') AS ngay_bd,
            to_char(c.ngay_kt, 'YYYY-MM-DD') AS ngay_kt
        FROM public.dmbanggiact c
        JOIN public.dmbanggia b ON b.ma_bang_gia = c.ma_bang_gia
        LEFT JOIN public.dmvt v ON v.ma_vt = c.ma_vt
        LEFT JOIN public.dmkh k ON k.ma_kh = c.ma_kh
        WHERE c.gia > 0
        ORDER BY c.ma_bang_gia, c.ma_vt
        LIMIT 5;
    """)
    rows6 = cur.fetchall()
    print(f"Query 6 finished in {time.time()-t0:.3f}s, {len(rows6)} rows", flush=True)
    for r in rows6[:3]:
        print(f"  Bảng giá: {r['ma_bang_gia']} ({r['ten_bang_gia']}) | VT: {r['ma_vt']} | KH: {r['ma_kh']} | Giá: {r['don_gia_ban']:,.2f} {r['ma_nt']}", flush=True)

    conn.close()
    print("\nALL 6 BATCH 3 QUERIES EXECUTED SUCCESSFULLY!", flush=True)

if __name__ == '__main__':
    test_queries()
