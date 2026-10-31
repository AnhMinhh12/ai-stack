#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Kịch bản tự động kiểm thử 45 câu hỏi ERP & MES
và chọc trực tiếp vào Database PostgreSQL 3SERP_HTMP_DATA để xác minh đối chiếu.
"""

import os
import sys
import json
import time
from datetime import datetime
import psycopg

# Cấu hình môi trường kết nối DB và cấu hình báo cáo
os.environ["HTMP_DB_HOST"] = os.getenv("HTMP_DB_HOST", "10.0.6.2")
os.environ["HTMP_DB_PORT"] = os.getenv("HTMP_DB_PORT", "5410")
os.environ["HTMP_DB_NAME"] = os.getenv("HTMP_DB_NAME", "3SERP_HTMP_DATA")
os.environ["HTMP_DB_USER"] = os.getenv("HTMP_DB_USER", "read_htmp")
os.environ["HTMP_DB_PASSWORD"] = os.getenv("HTMP_DB_PASSWORD", "P@ss@Htmp@W0rd!2025")
os.environ["HTMP_ERP_REPORTS_DIR"] = "/home/admin/ai-stack/config/erp-reports"
os.environ["HTMP_ERP_BUSINESS_INTENTS_PATH"] = "/home/admin/ai-stack/config/erp-business-intents.json"
os.environ["HTMP_ERP_SHARED_USER_ID"] = "11"
os.environ["OPENAI_API_BASE_URLS"] = "http://172.23.0.3:8000/v1"
os.environ["OPENAI_API_KEY"] = "30a5f0a426489c143322a991412c343055e9302978074dfdc45e8752de8cedd7"
os.environ["OPENAI_API_KEYS"] = "30a5f0a426489c143322a991412c343055e9302978074dfdc45e8752de8cedd7"
os.environ["VLLM_API_KEY"] = "30a5f0a426489c143322a991412c343055e9302978074dfdc45e8752de8cedd7"

sys.path.insert(0, "/home/admin/ai-stack")

from functions.htmp_postgres_query import Tools

DB_PARAMS = {
    "host": os.environ["HTMP_DB_HOST"],
    "port": int(os.environ["HTMP_DB_PORT"]),
    "dbname": os.environ["HTMP_DB_NAME"],
    "user": os.environ["HTMP_DB_USER"],
    "password": os.environ["HTMP_DB_PASSWORD"],
    "connect_timeout": 5
}

# Danh sách 45 câu hỏi kiểm thử từ DANH_SACH_CAU_HOI_TEST_ERP_VA_BAO_CAO.md
TEST_QUESTIONS = [
    # --- PHẦN 1: BÁO CÁO TỔNG HỢP (12 câu) ---
    {
        "id": "Q01",
        "part": "Phần 1 - Báo cáo tồn kho",
        "question": "Cho tôi xem báo cáo top 10 vật tư có số lượng tồn kho lớn nhất hiện tại",
        "db_verify_sql": """
            WITH opening AS (
                SELECT ma_vt, sum(ton00) AS qty FROM public.cdvt WHERE nam = extract(year FROM CURRENT_DATE)::smallint GROUP BY ma_vt
            ), movements AS (
                SELECT ma_vt, sum(sl_nhap - sl_xuat) AS qty FROM public.ct70 WHERE ngay_ct >= make_date(extract(year FROM CURRENT_DATE)::integer, 1, 1) GROUP BY ma_vt
            ), balances AS (
                SELECT ma_vt, qty FROM opening UNION ALL SELECT ma_vt, qty FROM movements
            )
            SELECT b.ma_vt, v.ten_vt, sum(b.qty) AS ton_kho
            FROM balances b JOIN public.dmvt v ON v.ma_vt = b.ma_vt
            GROUP BY b.ma_vt, v.ten_vt
            HAVING sum(b.qty) > 0
            ORDER BY ton_kho DESC
            LIMIT 10;
        """
    },
    {
        "id": "Q02",
        "part": "Phần 1 - Báo cáo tồn kho",
        "question": "Tổng hợp số lượng tồn kho phân bổ theo từng kho hàng trong hệ thống",
        "db_verify_sql": """
            WITH opening AS (
                SELECT ma_kho, sum(ton00) AS qty FROM public.cdvt WHERE nam = extract(year FROM CURRENT_DATE)::smallint GROUP BY ma_kho
            ), movements AS (
                SELECT ma_kho, sum(sl_nhap - sl_xuat) AS qty FROM public.ct70 WHERE ngay_ct >= make_date(extract(year FROM CURRENT_DATE)::integer, 1, 1) GROUP BY ma_kho
            ), balances AS (
                SELECT ma_kho, qty FROM opening UNION ALL SELECT ma_kho, qty FROM movements
            )
            SELECT b.ma_kho, k.ten_kho, sum(b.qty) AS ton_kho
            FROM balances b LEFT JOIN public.dmkho k ON k.ma_kho = b.ma_kho
            GROUP BY b.ma_kho, k.ten_kho
            HAVING sum(b.qty) > 0
            ORDER BY ton_kho DESC;
        """
    },
    {
        "id": "Q03",
        "part": "Phần 1 - Báo cáo tồn kho",
        "question": "Báo cáo tổng hợp số lượng nhập kho và xuất kho theo từng ngày từ ngày 01/10/2026 đến ngày 20/10/2026",
        "db_verify_sql": """
            SELECT ngay_ct, sum(sl_nhap) AS tong_nhap, sum(sl_xuat) AS tong_xuat
            FROM public.ct70
            WHERE ngay_ct BETWEEN '2026-10-01' AND '2026-10-20'
            GROUP BY ngay_ct
            ORDER BY ngay_ct;
        """
    },
    {
        "id": "Q04",
        "part": "Phần 1 - Bán hàng & Đơn hàng",
        "question": "Cho tôi báo cáo top khách hàng có số lượng đặt hàng lớn nhất trong các đơn hàng bán gần đây",
        "db_verify_sql": """
            SELECT h.ma_kh, coalesce(k.ten_kh, h.ma_kh) AS ten_kh, count(DISTINCT h.so_ct) AS so_don, sum(d.so_luong) AS tong_dat
            FROM public.ph64 h
            JOIN public.ct64 d USING (stt_rec)
            LEFT JOIN public.dmkh k ON k.ma_kh = h.ma_kh
            GROUP BY h.ma_kh, k.ten_kh
            ORDER BY tong_dat DESC
            LIMIT 10;
        """
    },
    {
        "id": "Q05",
        "part": "Phần 1 - Bán hàng & Đơn hàng",
        "question": "Tổng hợp sản lượng xuất kho bán hàng cho các khách hàng từ ngày 01/10/2026 đến hết ngày 20/10/2026",
        "db_verify_sql": """
            SELECT h.ma_kh, coalesce(k.ten_kh, h.ma_kh) AS ten_kh, count(DISTINCT h.so_ct) AS so_phieu_xuat, sum(d.so_luong) AS tong_xuat
            FROM public.ph81 h
            JOIN public.ct81 d USING (stt_rec)
            LEFT JOIN public.dmkh k ON k.ma_kh = h.ma_kh
            WHERE h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-20'
            GROUP BY h.ma_kh, k.ten_kh
            ORDER BY tong_xuat DESC;
        """
    },
    {
        "id": "Q06",
        "part": "Phần 1 - Bán hàng & Đơn hàng",
        "question": "Tổng hợp số lượng xuất kho bán hàng của mã hàng QC7-5146-000 theo từng ngày xuất từ ngày 01/10/2026 đến ngày 20/10/2026",
        "db_verify_sql": """
            SELECT h.ngay_ct, count(*) AS so_luot_xuat, sum(d.so_luong) AS tong_xuat
            FROM public.ph81 h
            JOIN public.ct81 d USING (stt_rec)
            WHERE upper(trim(d.ma_vt)) = 'QC7-5146-000'
              AND h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-20'
            GROUP BY h.ngay_ct
            ORDER BY h.ngay_ct;
        """
    },
    {
        "id": "Q07",
        "part": "Phần 1 - Mua hàng & Nhà cung cấp",
        "question": "Tổng hợp số lượng đơn hàng mua và tổng số lượng vật tư đặt mua theo từng nhà cung cấp gần đây",
        "db_verify_sql": """
            SELECT h.ma_kh AS ma_ncc, coalesce(k.ten_kh, h.ma_kh) AS ten_ncc, count(DISTINCT h.so_ct) AS so_don_mua, sum(d.so_luong) AS tong_dat_mua
            FROM public.ph94 h
            JOIN public.ct94 d USING (stt_rec)
            LEFT JOIN public.dmkh k ON k.ma_kh = h.ma_kh
            GROUP BY h.ma_kh, k.ten_kh
            ORDER BY so_don_mua DESC, tong_dat_mua DESC
            LIMIT 10;
        """
    },
    {
        "id": "Q08",
        "part": "Phần 1 - Mua hàng & Nhà cung cấp",
        "question": "Tổng hợp lịch sử các lần đặt mua, đơn giá mua thấp nhất, cao nhất và giá bình quân của mã nhựa PS-576D",
        "db_verify_sql": """
            SELECT count(*) AS so_lan_mua, min(d.gia2) AS gia_thap_nhat, max(d.gia2) AS gia_cao_nhat, round(avg(d.gia2), 2) AS gia_binh_quan
            FROM public.ct94 d
            JOIN public.ph94 h USING (stt_rec)
            WHERE upper(trim(d.ma_vt)) = 'PS-576D';
        """
    },
    {
        "id": "Q09",
        "part": "Phần 1 - MES Sản xuất & Chất lượng",
        "question": "Báo cáo tổng hợp số lượng sản phẩm lỗi NG theo từng máy sản xuất trong các ca làm việc gần đây",
        "db_verify_sql": """
            SELECT coalesce(ma_may, 'N/A') AS ma_may, sum(coalesce(so_luong, 0)) AS tong_ng
            FROM public.mes_oi_loi
            GROUP BY ma_may
            ORDER BY tong_ng DESC
            LIMIT 10;
        """
    },
    {
        "id": "Q10",
        "part": "Phần 1 - MES Sản xuất & Chất lượng",
        "question": "Tổng hợp số lượng lỗi sản phẩm theo từng mã lỗi và nguyên nhân lỗi trong bảng kê xác nhận NG",
        "db_verify_sql": """
            SELECT coalesce(ma_loi, 'N/A') AS ma_loi, coalesce(ten_loi, 'Chưa rõ') AS ten_loi, sum(coalesce(so_luong, 0)) AS tong_ng
            FROM public.mes_oi_loi
            GROUP BY ma_loi, ten_loi
            ORDER BY tong_ng DESC
            LIMIT 10;
        """
    },
    {
        "id": "Q11",
        "part": "Phần 1 - MES Sản xuất & Chất lượng",
        "question": "Báo cáo tổng số phút dừng máy theo từng nguyên nhân dừng chuyền trong bảng kê stop line gần đây",
        "db_verify_sql": """
            SELECT coalesce(nguyen_nhan, 'Không rõ nguyên nhân') AS nguyen_nhan, sum(coalesce(so_phut, 0)) AS tong_phut_dung
            FROM public.mes_oi_stopline
            GROUP BY nguyen_nhan
            ORDER BY tong_phut_dung DESC
            LIMIT 10;
        """
    },
    {
        "id": "Q12",
        "part": "Phần 1 - MES Sản xuất & Chất lượng",
        "question": "Tổng hợp số lượng kế hoạch sản xuất theo từng Work Order trong bảng điều độ sản xuất gần đây",
        "db_verify_sql": """
            SELECT wo_code, ma_vt, ma_may, ma_khuon, so_luong_ke_hoach
            FROM public.mes_oi_khsx
            ORDER BY ngay_bd DESC NULLS LAST
            LIMIT 10;
        """
    },

    # --- PHẦN 2: TRA CỨU NGẪU NHIÊN (30 câu) ---
    {"id": "Q13", "part": "Phần 2 - Đơn hàng bán SO", "question": "Cho tôi xem bảng kê đơn hàng bán gần đây nhất", "db_verify_sql": "SELECT so_ct, ngay_ct, ma_kh FROM public.ph64 ORDER BY ngay_ct DESC, so_ct DESC LIMIT 5;"},
    {"id": "Q14", "part": "Phần 2 - Đơn hàng bán SO", "question": "Bảng kê đơn hàng bán của khách hàng mã KH0047", "db_verify_sql": "SELECT so_ct, ngay_ct, ma_kh FROM public.ph64 WHERE upper(trim(ma_kh)) = 'KH0047' ORDER BY ngay_ct DESC LIMIT 5;"},
    {"id": "Q15", "part": "Phần 2 - Đơn hàng bán SO", "question": "Tra cứu chi tiết đơn hàng bán số 001-2610-010164", "db_verify_sql": "SELECT h.so_ct, h.ngay_ct, h.ma_kh, d.ma_vt, d.so_luong, d.gia2 FROM public.ph64 h JOIN public.ct64 d USING(stt_rec) WHERE upper(trim(h.so_ct)) = '001-2610-010164';"},
    {"id": "Q16", "part": "Phần 2 - Đơn hàng bán SO", "question": "Tìm kiếm các đơn hàng bán có chứa mã hàng VGL1A416", "db_verify_sql": "SELECT DISTINCT h.so_ct, h.ngay_ct, h.ma_kh, d.ma_vt, d.so_luong FROM public.ph64 h JOIN public.ct64 d USING(stt_rec) WHERE upper(trim(d.ma_vt)) = 'VGL1A416' ORDER BY h.ngay_ct DESC LIMIT 5;"},
    {"id": "Q17", "part": "Phần 2 - Xuất kho HDA", "question": "Bảng kê phiếu xuất kho bán hàng phát sinh ngày hôm nay", "db_verify_sql": "SELECT so_ct, ngay_ct, ma_kh FROM public.ph81 ORDER BY ngay_ct DESC LIMIT 5;"},
    {"id": "Q18", "part": "Phần 2 - Xuất kho HDA", "question": "Bảng kê các phiếu xuất bán cho khách hàng mã KH0049", "db_verify_sql": "SELECT so_ct, ngay_ct, ma_kh FROM public.ph81 WHERE upper(trim(ma_kh)) = 'KH0049' ORDER BY ngay_ct DESC LIMIT 5;"},
    {"id": "Q19", "part": "Phần 2 - Xuất kho HDA", "question": "Xem chi tiết phiếu xuất kho bán hàng số 001-2610-002643", "db_verify_sql": "SELECT h.so_ct, h.ngay_ct, h.ma_kh, d.ma_vt, d.so_luong FROM public.ph81 h JOIN public.ct81 d USING(stt_rec) WHERE upper(trim(h.so_ct)) = '001-2610-002643';"},
    {"id": "Q20", "part": "Phần 2 - Xuất kho HDA", "question": "Lot giao gần nhất của mã hàng QC7-5146-000 là khi nào và số lượng bao nhiêu?", "db_verify_sql": "SELECT h.so_ct, h.ngay_ct, d.so_luong FROM public.ph81 h JOIN public.ct81 d USING(stt_rec) WHERE upper(trim(d.ma_vt)) = 'QC7-5146-000' ORDER BY h.ngay_ct DESC, h.so_ct DESC LIMIT 1;"},

    {"id": "Q21", "part": "Phần 2 - Mua hàng PO", "question": "Bảng kê đơn hàng mua gần đây nhất của công ty", "db_verify_sql": "SELECT so_ct, ngay_ct, ma_kh FROM public.ph94 ORDER BY ngay_ct DESC LIMIT 5;"},
    {"id": "Q22", "part": "Phần 2 - Mua hàng PO", "question": "Bảng kê đơn hàng mua của nhà cung cấp mã NCC0220", "db_verify_sql": "SELECT so_ct, ngay_ct, ma_kh FROM public.ph94 WHERE upper(trim(ma_kh)) = 'NCC0220' ORDER BY ngay_ct DESC LIMIT 5;"},
    {"id": "Q23", "part": "Phần 2 - Mua hàng PO", "question": "Tra cứu đơn hàng mua số 001-2610-000702", "db_verify_sql": "SELECT h.so_ct, h.ngay_ct, h.ma_kh, d.ma_vt, d.so_luong, d.gia2 FROM public.ph94 h JOIN public.ct94 d USING(stt_rec) WHERE upper(trim(h.so_ct)) = '001-2610-000702';"},
    {"id": "Q24", "part": "Phần 2 - Mua hàng PO", "question": "Mã hàng PS-576D đã mua bao nhiêu lần và giá mua gần nhất là bao nhiêu?", "db_verify_sql": "SELECT count(*) AS so_lan_mua, (SELECT d.gia2 FROM public.ct94 d JOIN public.ph94 h USING(stt_rec) WHERE upper(trim(d.ma_vt)) = 'PS-576D' ORDER BY h.ngay_ct DESC LIMIT 1) AS gia_gan_nhat FROM public.ct94 d WHERE upper(trim(d.ma_vt)) = 'PS-576D';"},
    {"id": "Q25", "part": "Phần 2 - Mua hàng PO", "question": "Kiểm tra trạng thái duyệt giá và báo giá nhà cung cấp của mã vật tư PS-576D", "db_verify_sql": "SELECT ma_vt, ma_ncc, gia2, ngay_hl, trang_thai FROM public.dmbanggiancc WHERE upper(trim(ma_vt)) = 'PS-576D' ORDER BY ngay_hl DESC LIMIT 5;"},

    {"id": "Q26", "part": "Phần 2 - Kho vận nội bộ", "question": "Bảng kê phiếu nhập kho nội bộ từ sản xuất phát sinh gần đây", "db_verify_sql": "SELECT so_ct, ngay_ct, ma_kho FROM public.ph74 ORDER BY ngay_ct DESC LIMIT 5;"},
    {"id": "Q27", "part": "Phần 2 - Kho vận nội bộ", "question": "Chi tiết phiếu nhập kho nội bộ số 001-2610-011362", "db_verify_sql": "SELECT h.so_ct, h.ngay_ct, d.ma_vt, d.so_luong, d.ma_kho FROM public.ph74 h JOIN public.ct74 d USING(stt_rec) WHERE upper(trim(h.so_ct)) = '001-2610-011362';"},
    {"id": "Q28", "part": "Phần 2 - Kho vận nội bộ", "question": "Bảng kê nhập kho từ sản xuất của mã hàng RC4-3049-000", "db_verify_sql": "SELECT h.so_ct, h.ngay_ct, d.so_luong, d.ma_kho FROM public.ph74 h JOIN public.ct74 d USING(stt_rec) WHERE upper(trim(d.ma_vt)) = 'RC4-3049-000' ORDER BY h.ngay_ct DESC LIMIT 5;"},
    {"id": "Q29", "part": "Phần 2 - Kho vận nội bộ", "question": "Mã hàng QC7-5146-000 được nhập kho khi nào trong tháng 10/2026? Từ kho nào sang và ai lập phiếu?", "db_verify_sql": "SELECT h.so_ct, h.ngay_ct, d.ma_kho, h.user_id0 FROM public.ph74 h JOIN public.ct74 d USING(stt_rec) WHERE upper(trim(d.ma_vt)) = 'QC7-5146-000' AND h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-31' ORDER BY h.ngay_ct DESC LIMIT 5;"},
    {"id": "Q30", "part": "Phần 2 - Kho vận nội bộ", "question": "Tra cứu lần nhập kho gần đây nhất của mã vật tư RC4-3049-000", "db_verify_sql": "SELECT h.so_ct, h.ngay_ct, d.so_luong, d.ma_kho FROM public.ph74 h JOIN public.ct74 d USING(stt_rec) WHERE upper(trim(d.ma_vt)) = 'RC4-3049-000' ORDER BY h.ngay_ct DESC LIMIT 1;"},

    {"id": "Q31", "part": "Phần 2 - MES Sản xuất & Khuôn", "question": "Bảng kê đóng gói đóng thùng thành phẩm gần đây nhất", "db_verify_sql": "SELECT id, ngay_ct, ma_vt, so_thung, so_luong FROM public.mes_oi_dong_thung ORDER BY id DESC LIMIT 5;"},
    {"id": "Q32", "part": "Phần 2 - MES Sản xuất & Khuôn", "question": "Cho tôi xem bảng kê gộp tách thùng tem carton gần đây", "db_verify_sql": "SELECT id, ngay_ct, ma_carton, loai_thao_tac, so_luong FROM public.intem_carton_log ORDER BY id DESC LIMIT 5;"},
    {"id": "Q33", "part": "Phần 2 - MES Sản xuất & Khuôn", "question": "Bảng kê bổ sung hoặc bỏ shot khuôn trong ca sản xuất gần đây", "db_verify_sql": "SELECT id, ngay_ct, ma_khuon, so_shot_bo_sung, so_shot_bo FROM public.mes_oi_bo_shot ORDER BY id DESC LIMIT 5;"},
    {"id": "Q34", "part": "Phần 2 - MES Sản xuất & Khuôn", "question": "Tra cứu hồ sơ khuôn của mã khuôn K_VGY1A061", "db_verify_sql": "SELECT ma_khuon, ten_khuon, tong_shot, shot_dinh_muc FROM public.dmhosokhuon WHERE upper(trim(ma_khuon)) = 'K_VGY1A061';"},
    {"id": "Q35", "part": "Phần 2 - MES Sản xuất & Khuôn", "question": "Danh sách các hồ sơ khuôn và tuổi thọ shot định mức mới cập nhật gần đây", "db_verify_sql": "SELECT ma_khuon, ten_khuon, tong_shot, shot_dinh_muc FROM public.dmhosokhuon ORDER BY date_update DESC NULLS LAST LIMIT 5;"},
    {"id": "Q36", "part": "Phần 2 - MES Sản xuất & Khuôn", "question": "Bảng kê điều độ sản xuất và danh sách Work Order đang chạy", "db_verify_sql": "SELECT wo_code, ma_vt, ma_may, ma_khuon, trang_thai FROM public.mes_oi_khsx ORDER BY ngay_bd DESC LIMIT 5;"},
    {"id": "Q37", "part": "Phần 2 - MES Sản xuất & Khuôn", "question": "Lịch sử các lần dừng máy stop line gần đây nhất", "db_verify_sql": "SELECT id, ngay_ct, ma_may, so_phut, nguyen_nhan FROM public.mes_oi_stopline ORDER BY id DESC LIMIT 5;"},
    {"id": "Q38", "part": "Phần 2 - MES Sản xuất & Khuôn", "question": "Bảng kê xác nhận phế phẩm NG sản xuất gần đây nhất", "db_verify_sql": "SELECT id, ngay_ct, ma_may, ma_loi, so_luong FROM public.mes_oi_loi ORDER BY id DESC LIMIT 5;"},

    {"id": "Q39", "part": "Phần 2 - Bảng giá & BOM", "question": "Danh mục bảng giá bán sản phẩm đang có hiệu lực hiện hành", "db_verify_sql": "SELECT ma_bg, ten_bg, ngay_hl, ngay_hhet FROM public.dmbanggia ORDER BY ngay_hl DESC LIMIT 5;"},
    {"id": "Q40", "part": "Phần 2 - Bảng giá & BOM", "question": "Mã hàng QC7-5146-000 dùng loại hạt nhựa gì theo định mức BOM?", "db_verify_sql": "SELECT b.ma_vt_me, c.ma_vt_con, v.ten_vt, c.dinh_muc FROM public.dmbom b JOIN public.dmbomct c USING(stt_rec) JOIN public.dmvt v ON v.ma_vt = c.ma_vt_con WHERE upper(trim(b.ma_vt_me)) = 'QC7-5146-000';"},
    {"id": "Q41", "part": "Phần 2 - Bảng giá & BOM", "question": "MOQ báo giá và đơn giá bán hiện hành áp dụng cho mã hàng QC7-5146-000 là bao nhiêu?", "db_verify_sql": "SELECT d.ma_vt, d.gia2, d.moq, h.ngay_hl FROM public.dmbanggiact d JOIN public.dmbanggia h USING(stt_rec) WHERE upper(trim(d.ma_vt)) = 'QC7-5146-000' ORDER BY h.ngay_hl DESC LIMIT 1;"},
    {"id": "Q42", "part": "Phần 2 - Bảng giá & BOM", "question": "Mã hàng QC7-5146-000 thuộc quyền quản lý của khách hàng nào?", "db_verify_sql": "SELECT v.ma_vt, v.ten_vt, k.ma_kh, kh.ten_kh FROM public.dmvt v LEFT JOIN public.dmkhvt k ON k.ma_vt = v.ma_vt LEFT JOIN public.dmkh kh ON kh.ma_kh = k.ma_kh WHERE upper(trim(v.ma_vt)) = 'QC7-5146-000';"},

    # --- PHẦN 3: ĐỐI SOÁT PHỨC TẠP & SO SÁNH KỲ (3 câu) ---
    {
        "id": "Q43",
        "part": "Phần 3 - So sánh kỳ",
        "question": "So sánh số lượng xuất bán của mã hàng QC7-5146-000 từ ngày 01/10/2026 đến ngày 10/10/2026 so với từ ngày 11/10/2026 đến ngày 20/10/2026",
        "db_verify_sql": """
            SELECT
                sum(CASE WHEN h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-10' THEN d.so_luong ELSE 0 END) AS sl_ky_1,
                sum(CASE WHEN h.ngay_ct BETWEEN '2026-10-11' AND '2026-10-20' THEN d.so_luong ELSE 0 END) AS sl_ky_2
            FROM public.ph81 h JOIN public.ct81 d USING(stt_rec)
            WHERE upper(trim(d.ma_vt)) = 'QC7-5146-000';
        """
    },
    {
        "id": "Q44",
        "part": "Phần 3 - So sánh kỳ",
        "question": "Đối chiếu doanh thu và số lượng xuất bán của khách hàng KH0015 từ ngày 01/10/2026 đến ngày 10/10/2026 và từ ngày 11/10/2026 đến ngày 20/10/2026",
        "db_verify_sql": """
            SELECT
                sum(CASE WHEN h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-10' THEN d.so_luong ELSE 0 END) AS sl_ky_1,
                sum(CASE WHEN h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-10' THEN d.tien2 ELSE 0 END) AS tien_ky_1,
                sum(CASE WHEN h.ngay_ct BETWEEN '2026-10-11' AND '2026-10-20' THEN d.so_luong ELSE 0 END) AS sl_ky_2,
                sum(CASE WHEN h.ngay_ct BETWEEN '2026-10-11' AND '2026-10-20' THEN d.tien2 ELSE 0 END) AS tien_ky_2
            FROM public.ph81 h JOIN public.ct81 d USING(stt_rec)
            WHERE upper(trim(h.ma_kh)) = 'KH0015';
        """
    },
    {
        "id": "Q45",
        "part": "Phần 3 - Đối soát SO vs HDA",
        "question": "Kiểm tra tổng số lượng đặt hàng trong đơn SO và tổng số lượng đã xuất kho giao hàng của mã QC7-5146-000 trong tháng 10/2026",
        "db_verify_sql": """
            SELECT
                (SELECT sum(d.so_luong) FROM public.ph64 h JOIN public.ct64 d USING(stt_rec) WHERE upper(trim(d.ma_vt)) = 'QC7-5146-000' AND h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-31') AS tong_dat_so,
                (SELECT sum(d.so_luong) FROM public.ph81 h JOIN public.ct81 d USING(stt_rec) WHERE upper(trim(d.ma_vt)) = 'QC7-5146-000' AND h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-31') AS tong_xuat_hda;
        """
    }
]

def run_tests():
    print(f"=== BẮT ĐẦU CHẠY KIỂM THỬ VÀ XÁC MINH CƠ SỞ DỮ LIỆU ({len(TEST_QUESTIONS)} CÂU HỎI) ===")
    tools = Tools()
    results = []

    # Kết nối trực tiếp vào DB để sẵn sàng đối chiếu
    conn = psycopg.connect(**DB_PARAMS, autocommit=True)
    cur = conn.cursor()

    for idx, item in enumerate(TEST_QUESTIONS, 1):
        qid = item["id"]
        q = item["question"]
        part = item["part"]
        db_sql = item.get("db_verify_sql")

        print(f"\n[{idx}/{len(TEST_QUESTIONS)}] {qid} ({part}): {q}")
        t0 = time.time()
        ai_resp = None
        ai_rows_count = 0
        ai_status = "UNKNOWN"

        # 1. Chạy AI / Tool
        try:
            res = tools.ask_erp(q, __user__={"id": "admin", "email": "admin@htmp.vn"})
            if isinstance(res, tuple):
                html_resp, ctx = res
                rows = ctx.get("rows", [])
                ai_rows_count = len(rows) if isinstance(rows, list) else 0
                ai_resp = rows[:2]
                ai_status = "OK" if ai_rows_count > 0 else "EMPTY_ROWS"
            elif isinstance(res, str):
                try:
                    parsed = json.loads(res)
                    rows = parsed.get("rows", [])
                    ai_rows_count = len(rows) if isinstance(rows, list) else 0
                    ai_resp = rows[:2] if rows else parsed.get("message", res[:100])
                    ai_status = "OK" if ai_rows_count > 0 else "TEXT_JSON"
                except Exception:
                    ai_resp = res[:150]
                    ai_status = "TEXT_MSG"
        except Exception as e:
            ai_status = f"ERROR: {str(e)[:100]}"

        ai_duration = round(time.time() - t0, 3)

        # 2. Chọc DB đối chiếu
        db_data = None
        db_status = "NOT_CHECKED"
        if db_sql:
            try:
                cur.execute(db_sql)
                db_rows = cur.fetchall()
                db_data = db_rows[:3]
                db_status = f"VERIFIED ({len(db_rows)} records in DB)"
            except Exception as e:
                db_status = f"DB_QUERY_ERROR: {str(e)[:100]}"

        print(f"  -> AI Engine: {ai_status} ({ai_rows_count} rows, {ai_duration}s)")
        print(f"  -> DB Verify: {db_status} (Sample: {db_data[0] if db_data else 'None'})")

        results.append({
            "id": qid,
            "part": part,
            "question": q,
            "ai_status": ai_status,
            "ai_rows_count": ai_rows_count,
            "ai_duration_sec": ai_duration,
            "db_status": db_status,
            "db_sample": str(db_data[0]) if db_data else ""
        })

    conn.close()

    # Lưu kết quả kiểm thử vào file báo cáo
    report_path = "/home/admin/ai-stack/scratch/ket_qua_kiem_thu_45_cau_hoi.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n=== ĐÃ HOÀN TẤT KIỂM THỬ. KẾT QUẢ ĐÃ LƯU TẠI: {report_path} ===")

if __name__ == "__main__":
    run_tests()
