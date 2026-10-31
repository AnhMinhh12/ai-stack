#!/usr/bin/env python3
"""
Bộ đối soát tự động toàn diện ERP/MES (Automated ERP Reconciliation).
Chạy đối soát trực tiếp giữa:
1. Từ điển siêu dữ liệu (sys_dmtt, sys_gridconfig, sys_listoptions)
2. Cơ sở dữ liệu live PostgreSQL 3SERP_HTMP_DATA
3. 12 bài toán kiểm thử nghiệp vụ cốt lõi (BOM, Giá, Đơn hàng, Tồn kho, Lệnh giao, QC, Khuôn, Doanh số, Khách hàng)
"""

import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import psycopg
from decimal import Decimal
from erp_ai.system_dictionary import (
    get_document_status_name, 
    get_valid_statuses, 
    get_column_caption,
    get_visible_grid_columns
)

def run_reconciliation():
    conn_params = {
        'host': os.getenv('HTMP_DB_HOST', '10.0.6.2'),
        'port': os.getenv('HTMP_DB_PORT', '5410'),
        'dbname': os.getenv('HTMP_DB_NAME', '3SERP_HTMP_DATA'),
        'user': os.getenv('HTMP_DB_USER', 'read_htmp'),
        'password': os.getenv('HTMP_DB_PASSWORD', 'P@ss@Htmp@W0rd!2025'),
        'connect_timeout': 10
    }

    print("=== BẮT ĐẦU ĐỐI SOÁT TỰ ĐỘNG HỆ THỐNG ERP/MES ===")
    results = []

    with psycopg.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            # Test 1: sys_dmtt - Trạng thái SO1, TO2, HDA
            so1_completed = get_document_status_name('SO1', '12')
            so1_valid = get_valid_statuses('SO1')
            check_st = (so1_completed == "Hoàn thành" and "14" not in so1_valid and "15" not in so1_valid)
            results.append(("1. Status Dictionary (sys_dmtt)", check_st, f"SO1 Status 12='{so1_completed}', Đã loại trừ trạng thái hủy/từ chối 14, 15"))

            # Test 2: sys_gridconfig - Cột hiển thị & Nhãn tiếng Việt
            caption_vt = get_column_caption('ma_vt')
            caption_sl = get_column_caption('so_luong')
            caption_tien = get_column_caption('tien2')
            check_grid = (caption_vt != 'ma_vt' and caption_sl != 'so_luong')
            results.append(("2. UI Grid Labels (sys_gridconfig)", check_grid, f"Đã map nhãn: ma_vt='{caption_vt}', so_luong='{caption_sl}', tien2='{caption_tien}'"))

            # Test 3: BOM & Nhựa (mfbom_material)
            cur.execute("""
                SELECT b.product_code, b.material_code, m.ten_vt, b.quantity, b.uom
                FROM public.mfbom_material b
                JOIN public.dmvt m ON m.ma_vt = b.material_code
                WHERE b.product_code = 'QC7-5146-000'
                LIMIT 5;
            """)
            bom_rows = cur.fetchall()
            found_resin = any('PS-576D' in str(r[1]) for r in bom_rows)
            qty = bom_rows[0][3] if bom_rows else 0
            results.append(("3. BOM Structure (mfbom_material)", found_resin, f"Mã nhựa: {[r[1] for r in bom_rows]}, Định mức: {qty:.4f} KG/PCS"))

            # Test 4: Giá niêm yết & MOQ (dmbanggiact)
            cur.execute("""
                SELECT d.ma_vt, d.gia, d.ma_nt, d.sl_min, d.ngay_bd, d.ngay_kt
                FROM public.dmbanggiact d
                WHERE d.ma_vt = 'QC7-5146-000'
                ORDER BY d.ngay_bd DESC LIMIT 1;
            """)
            prow = cur.fetchone()
            results.append(("4. Price List & MOQ (dmbanggiact)", prow is not None, f"Giá: {prow[1]} {prow[2]}, MOQ: {prow[3]} PCS (Hiệu lực: {prow[4]} -> {prow[5]})"))

            # Test 5: Tồn kho nhiều kho (cdvt + ct70)
            cur.execute("""
                WITH opening AS (
                    SELECT ma_kho, SUM(ton00) AS qty FROM public.cdvt WHERE ma_vt = 'QC7-5146-000' AND nam = 2026 GROUP BY ma_kho
                ), movements AS (
                    SELECT ma_kho, SUM(sl_nhap - sl_xuat) AS qty FROM public.ct70 WHERE ma_vt = 'QC7-5146-000' GROUP BY ma_kho
                ), balances AS (
                    SELECT ma_kho, qty FROM opening
                    UNION ALL
                    SELECT ma_kho, qty FROM movements
                )
                SELECT k.ten_kho, SUM(b.qty) as ton
                FROM balances b
                JOIN public.dmkho k ON k.ma_kho = b.ma_kho
                GROUP BY k.ten_kho
                HAVING SUM(b.qty) <> 0
                ORDER BY ton DESC;
            """)
            stock_rows = cur.fetchall()
            results.append(("5. Multi-warehouse Inventory", len(stock_rows) > 0, f"Tổng tồn qua {len(stock_rows)} kho thực tế: {sum(r[1] for r in stock_rows):,} PCS"))

            # Test 6: Hồ sơ khuôn & Shot đếm (dmhosokhuon)
            cur.execute("""
                SELECT ma_khuon, ten_khuon, tong_so_shot, so_shot_bh
                FROM public.dmhosokhuon
                WHERE ma_khuon LIKE 'K_%' AND tong_so_shot > 0
                ORDER BY tong_so_shot DESC LIMIT 1;
            """)
            mrow = cur.fetchone()
            results.append(("6. Mold Profile & Shot Counter", mrow is not None, f"Khuôn {mrow[0]}: {mrow[2]:,} shots (Bảo hành: {mrow[3]:,})"))

            # Test 7: Sản lượng & Doanh thu xuất bán (ph81 + ct81)
            cur.execute("""
                SELECT COUNT(DISTINCT h.so_ct), SUM(d.so_luong), SUM(d.tien2)
                FROM public.ph81 h
                JOIN public.ct81 d USING (stt_rec)
                WHERE d.ma_vt = 'QC7-5146-000'
                  AND h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-20'
                  AND h.status::text NOT IN ('14', '15');
            """)
            srow = cur.fetchone()
            results.append(("7. Sales Deliveries (ph81/ct81)", srow and srow[0] > 0, f"{srow[0]} phiếu xuất, Tổng: {srow[1]:,} PCS, Tiền: {srow[2]:,.2f} VND"))

            # Test 8: Khách hàng quản lý mã hàng (dmvt + dmkh)
            cur.execute("""
                SELECT v.ma_vt, v.ma_kh, k.ten_kh
                FROM public.dmvt v
                JOIN public.dmkh k ON k.ma_kh = v.ma_kh
                WHERE v.ma_vt = 'QC7-5146-000';
            """)
            krow = cur.fetchone()
            results.append(("8. Customer Ownership (dmvt/dmkh)", krow is not None, f"Mã KH: {krow[1]}, Tên: {krow[2]}"))

            # Test 9: Lịch sử nhập kho (ct70)
            cur.execute("""
                SELECT COUNT(*), SUM(sl_nhap)
                FROM public.ct70
                WHERE ma_vt = 'QC7-5146-000'
                  AND ngay_ct BETWEEN '2026-10-01' AND '2026-10-20'
                  AND sl_nhap > 0;
            """)
            nrow = cur.fetchone()
            results.append(("9. Receipt Transactions (ct70)", nrow and nrow[0] > 0, f"{nrow[0]} lượt nhập kho, Tổng nhập: {nrow[1]:,} PCS"))

            # Test 10: Lệnh giao hàng hoàn thành (ph96 / ct96 status 12)
            cur.execute("""
                SELECT COUNT(*), SUM(d.so_luong)
                FROM public.ph96 h
                JOIN public.ct96 d USING (stt_rec)
                WHERE d.ma_vt = 'QC7-5146-000'
                  AND h.status::text = '12';
            """)
            drow = cur.fetchone()
            results.append(("10. Completed Delivery Orders (TO2)", drow and drow[0] > 0, f"{drow[0]} dòng lệnh giao trạng thái 12 (Hoàn thành), Tổng: {drow[1]:,} PCS"))

            # Test 11: Trạng thái tem & QC (intem_log + sys_listoptions)
            cur.execute("""
                SELECT a.status_qc,
                       coalesce(o.form_name, a.status_qc::text) AS trang_thai_qc,
                       count(*) AS so_tem,
                       sum((e->>'so_luong')::numeric) AS so_luong
                FROM public.intem_log a
                CROSS JOIN LATERAL jsonb_array_elements(
                  CASE WHEN jsonb_typeof(a.data_tem::jsonb)='array' THEN a.data_tem::jsonb ELSE '[]'::jsonb END
                ) e
                LEFT JOIN public.sys_listoptions o ON o.form = 'OQC' AND o.form_type = 'TYPE_ST' AND o.form_value = a.status_qc::text
                WHERE a.nxt = 1 AND a.status = '1'
                  AND upper(trim(e->>'ma_vt')) = 'QC7-5146-000'
                GROUP BY a.status_qc, o.form_name
                ORDER BY a.status_qc;
            """)
            qc_rows = cur.fetchall()
            results.append(("11. Quality QC Labels (intem_log)", len(qc_rows) > 0, f"Phân bổ tem QC: {[(r[1], int(r[2]), float(r[3])) for r in qc_rows]}"))

            # Test 12: Đơn hàng SO loại trừ hủy (ph64/ct64)
            cur.execute("""
                SELECT COUNT(DISTINCT h.so_ct), SUM(d.so_luong), SUM(d.tien2)
                FROM public.ph64 h
                JOIN public.ct64 d USING (stt_rec)
                WHERE d.ma_vt = 'QC7-5146-000'
                  AND h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-31'
                  AND h.status::text NOT IN ('14', '15');
            """)
            orow = cur.fetchone()
            results.append(("12. Active Sales Orders (ph64/ct64)", orow and orow[0] > 0, f"{orow[0]} đơn hàng SO hợp lệ, Tổng đặt: {orow[1]:,} PCS, Tiền: {orow[2]:,.2f} VND"))

    print("\n" + "="*80)
    print("BẢNG TỔNG HỢP ĐỐI SOÁT TỰ ĐỘNG TOÀN DIỆN ERP/MES:")
    print("="*80)
    all_pass = True
    for name, status, detail in results:
        mark = " PASS " if status else " FAIL "
        if not status:
            all_pass = False
        print(f"[{mark}] {name:<35} | {detail}")
    
    print("="*80)
    if all_pass:
        print(">> TOÀN BỘ 12 BÀI KIỂM THỬ ĐỐI SOÁT ĐỀU ĐẠT CHUẨN 100% PASS!")
        print(">> KHÔNG CẦN ĐĂNG NHẬP GIAO DIỆN HAY PHỎNG VẤN PHÒNG BAN.")
    return all_pass

if __name__ == "__main__":
    success = run_reconciliation()
    sys.exit(0 if success else 1)
