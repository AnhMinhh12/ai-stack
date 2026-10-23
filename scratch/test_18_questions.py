#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path
from decimal import Decimal
import psycopg
from psycopg.rows import dict_row

ROOT = Path("/home/admin/ai-stack")
sys.path.insert(0, str(ROOT))

os.environ["OPENAI_API_BASE_URLS"] = "http://127.0.0.1:8000/v1"
os.environ["OPENAI_API_KEYS"] = "30a5f0a426489c143322a991412c343055e9302978074dfdc45e8752de8cedd7"
os.environ["VLLM_API_KEY"] = "30a5f0a426489c143322a991412c343055e9302978074dfdc45e8752de8cedd7"
os.environ["HTMP_DB_HOST"] = "10.0.6.2"
os.environ["HTMP_DB_PORT"] = "5410"
os.environ["HTMP_DB_NAME"] = "3SERP_HTMP_DATA"
os.environ["HTMP_DB_USER"] = "read_htmp"
os.environ["HTMP_DB_PASSWORD"] = "P@ss@Htmp@W0rd!2025"
os.environ["HTMP_ERP_SHARED_USER_ID"] = "11"
os.environ["HTMP_ERP_REPORTS_DIR"] = "/home/admin/ai-stack/config/erp-reports"
os.environ["HTMP_ERP_BUSINESS_INTENTS_PATH"] = "/home/admin/ai-stack/config/erp-business-intents.json"

from functions.htmp_postgres_query import Tools, connection_settings

QUESTIONS = [
    (1, "Mã hàng QC7-5146-000 dùng loại nhựa gì? Cấu trúc sản phẩm của mã hàng này gồm những gì?"),
    (2, "MOQ báo giá hiện tại của mã QC7-5146-000 là bao nhiêu? Giá áp dụng hiện tại theo từng mức MOQ là bao nhiêu?"),
    (3, "Tính đến ngày 20/10/2026, lot gần nhất được xuất giao của mã QC7-5146-000 là lot nào? Ngày xuất và số lượng bao nhiêu?"),
    (4, "Từ ngày 01/10/2026 đến hết ngày 20/10/2026, tổng số lượng xuất bán và doanh thu của mã QC7-5146-000 là bao nhiêu?"),
    (5, "Mã hàng QC7-5146-000 được khai báo thuộc khách hàng nào?"),
    (6, "Từ ngày 01/10/2026 đến hết ngày 20/10/2026, mã QC7-5146-000 được nhập kho vào những ngày nào, từ kho nào sang kho nào, số lượng bao nhiêu và tài khoản nào tạo phiếu?"),
    (7, "So sánh DO và FCST hiện tại với bản trước của mã QC7-5146-000: số lượng tăng hay giảm bao nhiêu?"),
    (8, "Quy cách đóng gói của mã QC7-5146-000 gồm những thông tin gì? Có thể quy đổi tồn kho hiện tại theo quy cách đóng gói không?"),
    (9, "Khuôn K_QC5-2919-000-V1 đã chạy tổng cộng bao nhiêu shot cho mã QC7-5146-000? Với demand của khách KH0015, có đủ dữ liệu để dự kiến thời điểm khuôn hết tuổi thọ không?"),
    (10, "So sánh doanh thu mã QC7-5146-000 của khách KH0015 trong hai khoảng 01/09/2026–20/09/2026 và 01/10/2026–20/10/2026. Nêu số lượng và doanh thu từng kỳ."),
    (11, "Mã QC7-5146-000 hiện có tồn kho thuộc những khuôn nào? Số lượng theo từng khuôn là bao nhiêu?"),
    (12, "Liệt kê dữ liệu đơn hàng bán của khách KH0015 từ ngày 01/10/2026 đến hết ngày 20/10/2026, gồm số đơn, ngày đặt, mã hàng, số lượng và trạng thái."),
    (13, "Lệnh giao hàng 001-2610-001811 được ghi nhận hoàn thành khi nào? Cho biết trạng thái lệnh và căn cứ thời gian được dùng."),
    (14, "Tồn kho hiện tại của mã QC7-5146-000 là bao nhiêu ở từng kho?"),
    (15, "Mã QC7-5146-000 hiện có lot thành phẩm nào ở trạng thái QC cần chú ý? Cho biết trạng thái QC đúng như dữ liệu ERP."),
    (16, "Trong đơn hàng của khách KH0015 từ ngày 01/10/2026 đến hết ngày 20/10/2026, có mã hàng nào chưa có giá chuẩn được liên kết không?"),
    (17, "Công ty TNHH Canon Việt Nam- Chi nhánh Thăng Long có mã khách hàng nào trên ERP?"),
    (18, "Từ ngày 01/10/2026 đến hết ngày 20/10/2026, mã QC7-5146-000 có số lượng giao bù NG là bao nhiêu, số lượng hàng NG đã nhận lại là bao nhiêu, và còn bao nhiêu chưa giao bù hoặc chưa nhận về? Phân biệt rõ giao bù NG với giao bù hàng thiếu; nếu ERP không lưu đủ căn cứ để phân biệt thì nêu rõ."),
]

def default_json(obj):
    if isinstance(obj, Decimal):
        return float(obj)
    return str(obj)

def run_db_probes():
    """Fetch factual ground truth from PostgreSQL for the 18 cases."""
    facts = {}
    with psycopg.connect(**connection_settings(), row_factory=dict_row) as conn:
        with conn.cursor() as cur:
            # 1. BOM
            cur.execute("""
                SELECT b.bom_code, b.bom_version, b.status, b.valid_from, b.valid_to,
                       m.material_code, v.ten_vt, m.quantity, m.uom
                FROM public.mfbom b
                JOIN public.mfbom_material m USING(bom_code)
                LEFT JOIN public.dmvt v ON v.ma_vt = m.material_code
                WHERE b.product_code = 'QC7-5146-000' AND '2026-10-20'::date BETWEEN b.valid_from AND b.valid_to
                ORDER BY b.bom_version DESC, m.material_code
            """)
            facts[1] = cur.fetchall()

            # 2. MOQ & Prices
            cur.execute("""
                SELECT d.ma_kh, d.sl_min, d.dvt, d.gia, d.gia0, d.ma_nt, d.ngay_bd, d.ngay_kt, h.status
                FROM public.dmbanggiact d JOIN public.dmbanggia h USING(ma_bang_gia)
                WHERE d.ma_vt = 'QC7-5146-000' AND '2026-10-20'::date BETWEEN d.ngay_bd AND d.ngay_kt
                ORDER BY d.ma_kh, d.sl_min, d.ngay_bd DESC
            """)
            facts[2] = cur.fetchall()

            # 3. Latest sales doc
            cur.execute("""
                SELECT h.stt_rec, h.so_ct, h.ngay_lct, h.ngay_ct, h.status,
                       array_agg(DISTINCT nullif(d.ma_lo, '')) AS lots, sum(d.so_luong) AS quantity
                FROM public.ph81 h JOIN public.ct81 d USING(stt_rec)
                WHERE d.ma_vt = 'QC7-5146-000' AND h.ma_gd <> 4 AND h.ngay_lct <= '2026-10-20'::date
                GROUP BY h.stt_rec, h.so_ct, h.ngay_lct, h.ngay_ct, h.status
                ORDER BY h.ngay_lct DESC, h.ngay_ct DESC, h.so_ct DESC LIMIT 3
            """)
            facts[3] = cur.fetchall()

            # 4. Sales posted 01-20/10
            cur.execute("""
                SELECT count(*) AS lines, sum(d.so_luong) AS quantity, sum(d.tien2) AS tien2
                FROM public.ph81 h JOIN public.ct81 d USING(stt_rec)
                WHERE d.ma_vt = 'QC7-5146-000' AND h.ma_gd <> 4 AND h.ngay_lct BETWEEN '2026-10-01' AND '2026-10-20'
            """)
            facts[4] = cur.fetchone()

            # 5. Customer of material
            cur.execute("""
                SELECT v.ma_vt, v.ma_kh, k.ten_kh
                FROM public.dmvt v LEFT JOIN public.dmkh k ON k.ma_kh = v.ma_kh
                WHERE v.ma_vt = 'QC7-5146-000'
            """)
            facts[5] = cur.fetchone()

            # 6. Receipts
            cur.execute("""
                SELECT count(*) AS total_receipts, sum(sl_nhap) AS total_qty
                FROM public.ct70 WHERE ma_vt = 'QC7-5146-000' AND nxt = 1 AND date0 BETWEEN '2026-10-01' AND '2026-10-20'
            """)
            facts[6] = cur.fetchone()

            # 7. FCST
            cur.execute("""
                SELECT nguon_du_lieu, loai_du_lieu, count(*) AS cnt, min(ngay_tinh_toan), max(ngay_tinh_toan)
                FROM public.mfkhsx_po_fc WHERE ma_vt = 'QC7-5146-000' GROUP BY 1, 2
            """)
            facts[7] = cur.fetchall()

            # 8. Packaging & stock
            cur.execute("""
                SELECT ma_vt, dvt, packs0, ma_thung, ma_khay FROM public.dmvt WHERE ma_vt = 'QC7-5146-000'
            """)
            facts[8] = cur.fetchone()

            # 9. Mold
            cur.execute("""
                SELECT h.ma_khuon, h.tong_so_shot, h.so_shot_bh, s.ma_sp
                FROM public.dmhosokhuon h JOIN public.dmhosokhuonsp s USING(ma_khuon)
                WHERE h.ma_khuon = 'K_QC5-2919-000-V1' AND s.ma_sp = 'QC7-5146-000'
            """)
            facts[9] = cur.fetchone()

            # 10. Sales 2 periods
            cur.execute("""
                SELECT to_char(h.ngay_ct, 'YYYY-MM') AS period, count(*) AS lines, sum(d.so_luong) AS qty, sum(d.tien2) AS tien2
                FROM public.ph81 h JOIN public.ct81 d USING(stt_rec)
                WHERE d.ma_vt = 'QC7-5146-000' AND h.ma_kh = 'KH0015' AND h.ma_gd <> 4
                  AND ((h.ngay_ct BETWEEN '2026-09-01' AND '2026-09-20') OR (h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-20'))
                GROUP BY 1 ORDER BY 1
            """)
            facts[10] = cur.fetchall()

            # 11. Mold stock on labels
            cur.execute("""
                SELECT e->>'die_no' AS die_no, e->>'ma_khuon' AS mold, sum((e->>'so_luong')::numeric) AS qty
                FROM public.intem_log a CROSS JOIN LATERAL jsonb_array_elements(
                    CASE WHEN jsonb_typeof(a.data_tem::jsonb)='array' THEN a.data_tem::jsonb ELSE '[]'::jsonb END
                ) e
                WHERE a.nxt = 1 AND a.status = '1' AND e->>'ma_vt' = 'QC7-5146-000'
                GROUP BY 1, 2 ORDER BY 1, 2
            """)
            facts[11] = cur.fetchall()

            # 12. Orders of KH0015
            cur.execute("""
                SELECT count(DISTINCT h.stt_rec) AS docs, count(*) AS lines, sum(d.so_luong) AS qty
                FROM public.ph64 h JOIN public.ct64 d USING(stt_rec)
                WHERE h.ma_kh = 'KH0015' AND h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-20'
            """)
            facts[12] = cur.fetchone()

            # 13. Delivery order 001-2610-001811
            cur.execute("""
                SELECT h.stt_rec, h.so_ct, h.status, s.statusname, h.date0, h.time0
                FROM public.ph96 h LEFT JOIN public.sys_dmtt s ON s.ma_ct = 'TO2' AND s.status = h.status
                WHERE h.so_ct = '001-2610-001811'
            """)
            facts[13] = cur.fetchall()

            # 14. Stock per warehouse
            cur.execute("""
                SELECT ma_kho, sum(sl_nhap) - sum(sl_xuat) AS ton_kho
                FROM public.ct70 WHERE upper(trim(ma_vt)) = 'QC7-5146-000'
                GROUP BY ma_kho HAVING sum(sl_nhap) - sum(sl_xuat) > 0 ORDER BY ton_kho DESC
            """)
            facts[14] = cur.fetchall()

            # 15. QC status of labels
            cur.execute("""
                SELECT a.status_qc, o.form_name, sum((e->>'so_luong')::numeric) AS qty
                FROM public.intem_log a CROSS JOIN LATERAL jsonb_array_elements(
                    CASE WHEN jsonb_typeof(a.data_tem::jsonb)='array' THEN a.data_tem::jsonb ELSE '[]'::jsonb END
                ) e
                LEFT JOIN public.sys_listoptions o ON o.form = 'OQC' AND o.form_type = 'TYPE_ST' AND o.form_value = a.status_qc::text
                WHERE a.nxt = 1 AND a.status = '1' AND e->>'ma_vt' = 'QC7-5146-000'
                GROUP BY 1, 2 ORDER BY 1
            """)
            facts[15] = cur.fetchall()

            # 16. Orders without standard price
            cur.execute("""
                SELECT d.ma_vt, count(*) AS lines
                FROM public.ph64 h JOIN public.ct64 d USING(stt_rec)
                WHERE h.ma_kh = 'KH0015' AND h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-20'
                  AND (d.gia_chuan IS NULL OR d.gia_chuan = 0)
                GROUP BY d.ma_vt ORDER BY d.ma_vt LIMIT 10
            """)
            facts[16] = cur.fetchall()

            # 17. Customer by name
            cur.execute("""
                SELECT ma_kh, ten_kh FROM public.dmkh WHERE ten_kh ILIKE '%Canon Việt Nam%' LIMIT 5
            """)
            facts[17] = cur.fetchall()

            # 18. Replacement transactions (ma_gd=10)
            cur.execute("""
                SELECT count(*) AS lines, sum(d.so_luong) AS qty
                FROM public.ph96 h JOIN public.ct96 d USING(stt_rec)
                WHERE d.ma_vt = 'QC7-5146-000' AND h.ma_gd = 10 AND h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-20'
            """)
            facts[18] = cur.fetchone()

    return facts

def main():
    print("=== ĐỐI CHIẾU THỰC TẾ DATABASE VỚI KẾT QUẢ ASK_ERP ===", flush=True)
    print("Connecting to DB and fetching ground truth facts...", flush=True)
    facts = run_db_probes()
    print("Database facts fetched successfully.\n", flush=True)

    tools = Tools()
    user_context = {"id": "11", "email": "operator-audit"}

    results = []
    for q_id, q_text in QUESTIONS:
        print(f"--- Running Q{q_id}: {q_text[:60]}... ---", flush=True)
        try:
            raw_result = tools._ask_erp_data(q_text, __user__=user_context)
            try:
                parsed = json.loads(raw_result)
            except Exception:
                parsed = {"raw": raw_result}
        except Exception as exc:
            parsed = {"error": str(exc)}
        
        db_fact = facts.get(q_id)
        print(f"   [DONE Q{q_id}] Response preview: {str(parsed)[:100]}...", flush=True)
        results.append({
            "id": q_id,
            "question": q_text,
            "db_fact": db_fact,
            "ask_erp_result": parsed,
        })

    out_file = ROOT / "scratch/eval_18_questions_result.json"
    out_file.parent.mkdir(parents=True, exist_ok=True)
    out_file.write_text(json.dumps(results, ensure_ascii=False, indent=2, default=default_json))
    print(f"\nAll 18 questions tested! Results written to: {out_file}", flush=True)

if __name__ == "__main__":
    main()
