"""Inspect ground truth for Q3, Q4, Q6, Q7, Q9, Q10, Q12, Q13, Q15, Q16, Q18."""

import sys
sys.path.insert(0, ".")
import psycopg
from psycopg.rows import dict_row
from functions.htmp_postgres_query import Tools
from erp_ai.native_tools import connection_settings

tools = Tools()

def inspect_remaining():
    with psycopg.connect(**connection_settings(), autocommit=False) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            # Q3: Tính đến 20/10/2026, lot gần nhất được xuất giao của QC7-5146-000
            print("=== Q3: Lot xuất giao gần nhất tính đến 20/10/2026 ===")
            cur.execute("""
                SELECT c.so_ct, c.ngay_ct, b.ma_lo, b.so_luong, b.ma_kho
                FROM public.ct70 c
                JOIN public.ct70bsp b ON b.stt_rec = c.stt_rec
                WHERE trim(c.ma_vt) = 'QC7-5146-000'
                  AND c.ma_ct = 'HDA'
                  AND c.ngay_ct <= '2026-10-20'
                ORDER BY c.ngay_ct DESC, c.so_ct DESC
                LIMIT 5;
            """)
            rows3 = cur.fetchall()
            print("HDA lots <= 2026-10-20:", rows3)

            # Q4: Từ 01/10/2026 đến 20/10/2026, tổng số lượng xuất bán và doanh thu của QC7-5146-000
            print("\n=== Q4: Xuất bán & doanh thu 01/10/2026 - 20/10/2026 ===")
            cur.execute("""
                SELECT sum(c.sl_xuat) AS tong_sl_xuat,
                       sum(c.sl_xuat * CASE WHEN c.gia > 0 THEN c.gia ELSE c.gia_nt END) AS tong_doanh_thu,
                       c.ma_nt
                FROM public.ct70 c
                WHERE trim(c.ma_vt) = 'QC7-5146-000'
                  AND c.ma_ct = 'HDA'
                  AND c.ngay_ct BETWEEN '2026-10-01' AND '2026-10-20'
                GROUP BY c.ma_nt;
            """)
            print("HDA 01-20/10/2026:", cur.fetchall())

            # Q6: Nhập kho 01/10/2026 - 20/10/2026 của QC7-5146-000
            print("\n=== Q6: Nhập kho 01/10/2026 - 20/10/2026 ===")
            cur.execute("""
                SELECT c.so_ct, c.ngay_ct, c.ma_ct, c.ma_kho, c.sl_nhap, c.dien_giai,
                       u.user_name AS nguoi_tao
                FROM public.ct70 c
                LEFT JOIN public.sys_user u ON u.user_id = c.user_id0
                WHERE trim(c.ma_vt) = 'QC7-5146-000'
                  AND c.sl_nhap > 0
                  AND c.ngay_ct BETWEEN '2026-10-01' AND '2026-10-20'
                ORDER BY c.ngay_ct;
            """)
            print("Receipts 01-20/10/2026:", cur.fetchall())

            # Q7: So sánh DO và FCST
            print("\n=== Q7: DO & FCST QC7-5146-000 ===")
            # Check ask_erp handler for DO/FCST
            ans7 = tools.ask_erp("So sánh DO và FCST hiện tại với bản trước của mã QC7-5146-000")
            print("ask_erp Q7 preview:", ans7[:300])

            # Q9: Khuôn K_QC5-2919-000-V1 chạy bao nhiêu shot cho QC7-5146-000 & dự kiến tuổi thọ
            print("\n=== Q9: Khuôn K_QC5-2919-000-V1 & Tuổi thọ ===")
            ans9 = tools.ask_erp("Khuôn K_QC5-2919-000-V1 đã chạy tổng cộng bao nhiêu shot cho mã QC7-5146-000? Với demand của khách KH0015, có đủ dữ liệu để dự kiến thời điểm khuôn hết tuổi thọ không?")
            print("ask_erp Q9 preview:", ans9[:300])

            # Q10: So sánh doanh thu 01/09-20/09 và 01/10-20/10
            print("\n=== Q10: So sánh doanh thu kỳ 1 (01/09-20/09) và kỳ 2 (01/10-20/10) ===")
            ans10 = tools.ask_erp("So sánh doanh thu mã QC7-5146-000 của khách KH0015 trong hai khoảng 01/09/2026–20/09/2026 và 01/10/2026–20/10/2026")
            print("ask_erp Q10 preview:", ans10[:400])

            # Q12: Đơn hàng bán KH0015 từ 01/10/2026 đến 20/10/2026
            print("\n=== Q12: Đơn hàng bán KH0015 từ 01/10 đến 20/10/2026 ===")
            cur.execute("""
                SELECT c.so_ct, c.ngay_ct, c.ma_vt, c.so_luong, c.status
                FROM public.ct81 c
                WHERE trim(c.ma_kh) = 'KH0015'
                  AND c.ngay_ct BETWEEN '2026-10-01' AND '2026-10-20'
                ORDER BY c.ngay_ct, c.so_ct
                LIMIT 10;
            """)
            print("Orders sample:", cur.fetchall())

            # Q13: Lệnh giao hàng 001-2610-001811
            print("\n=== Q13: Lệnh giao hàng 001-2610-001811 ===")
            cur.execute("""
                SELECT so_ct, ngay_ct, status, date2, time2
                FROM public.ph85
                WHERE trim(so_ct) = '001-2610-001811';
            """)
            print("ph85:", cur.fetchall())

            # Q15: QC status của lot thành phẩm QC7-5146-000
            print("\n=== Q15: Lot thành phẩm QC status ===")
            ans15 = tools.ask_erp("Mã QC7-5146-000 hiện có lot thành phẩm nào ở trạng thái QC cần chú ý?")
            print("ask_erp Q15 preview:", ans15[:300])

            # Q16: Đơn hàng KH0015 thiếu giá chuẩn
            print("\n=== Q16: Đơn hàng KH0015 thiếu giá chuẩn ===")
            ans16 = tools.ask_erp("Trong đơn hàng của khách KH0015 từ ngày 01/10/2026 đến hết ngày 20/10/2026, có mã hàng nào chưa có giá chuẩn được liên kết không?")
            print("ask_erp Q16 preview:", ans16[:300])

            # Q18: Giao bù NG vs giao bù hàng thiếu
            print("\n=== Q18: Giao bù NG vs giao bù hàng thiếu ===")
            ans18 = tools.ask_erp("Từ ngày 01/10/2026 đến hết ngày 20/10/2026, mã QC7-5146-000 có số lượng giao bù NG là bao nhiêu, số lượng hàng NG đã nhận lại là bao nhiêu, và còn bao nhiêu chưa giao bù hoặc chưa nhận về? Phân biệt rõ giao bù NG với giao bù hàng thiếu; nếu ERP không lưu đủ căn cứ để phân biệt thì nêu rõ.")
            print("ask_erp Q18 preview:", ans18[:400])

if __name__ == "__main__":
    inspect_remaining()

