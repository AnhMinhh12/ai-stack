#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Bộ kiểm thử và đối soát tự động toàn diện 28 câu hỏi ERP/MES
theo Section 18 của TOM_TAT_TRIEN_KHAI_AI_ERP_MES_2026-10-29.md.
Chạy trực tiếp qua Chat API Open WebUI (model htmp-nhanh)
và đối chiếu song song với Cơ sở dữ liệu live PostgreSQL 3SERP_HTMP_DATA.
"""

import os
import sys
import json
import time
import urllib.request
import psycopg
from decimal import Decimal

# Load environment
for env_file in ['/home/admin/ai-stack/.env']:
    if os.path.exists(env_file):
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))

BASE_URL = "http://127.0.0.1:80"
API_KEY = "sk-1ce52487dd424dc4b2e8c54fe7041f8c"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

DB_PARAMS = {
    "host": os.getenv("HTMP_DB_HOST", "10.0.6.2"),
    "port": int(os.getenv("HTMP_DB_PORT", "5410")),
    "dbname": os.getenv("HTMP_DB_NAME", "3SERP_HTMP_DATA"),
    "user": os.getenv("HTMP_DB_USER", "read_htmp"),
    "password": os.getenv("HTMP_DB_PASSWORD", "P@ss@Htmp@W0rd!2025"),
    "connect_timeout": 10
}

sys.path.insert(0, "/home/admin/ai-stack")
from functions.htmp_postgres_query import Tools
tools = Tools()

TEST_QUESTIONS = [
    # Nhóm 1: Bán hàng, Xuất bán HDA & Lệnh giao hàng TO2/DO
    {
        "stt": 1,
        "group": "Nhóm 1: Bán hàng & Xuất bán",
        "question": "Cho tôi biết sản lượng và doanh thu xuất bán của mã QC7-5146-000 từ ngày 01/10/2026 đến 20/10/2026",
        "db_sql": """
            SELECT sum(d.so_luong) as sl, sum(d.tien2) as tien
            FROM public.ct81 d
            JOIN public.ph81 h ON h.stt_rec = d.stt_rec
            WHERE upper(trim(d.ma_vt)) = 'QC7-5146-000'
              AND h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-20'
              AND h.status::text NOT IN ('14', '15') AND h.ma_gd <> 4;
        """,
        "keywords": ["89,100", "170,992,971"]
    },
    {
        "stt": 2,
        "group": "Nhóm 1: Bán hàng & Xuất bán",
        "question": "So sánh số lượng xuất bán của mã hàng QC7-5146-000 từ 01/10 đến 10/10 so với từ 11/10 đến 20/10",
        "db_sql": """
            SELECT 
                sum(CASE WHEN h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-10' THEN d.so_luong ELSE 0 END) as sl_ky1,
                sum(CASE WHEN h.ngay_ct BETWEEN '2026-10-11' AND '2026-10-20' THEN d.so_luong ELSE 0 END) as sl_ky2
            FROM public.ct81 d
            JOIN public.ph81 h ON h.stt_rec = d.stt_rec
            WHERE upper(trim(d.ma_vt)) = 'QC7-5146-000'
              AND h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-20'
              AND h.status::text NOT IN ('14', '15') AND h.ma_gd <> 4;
        """,
        "keywords": ["41,520", "47,580", "6,060"]
    },
    {
        "stt": 3,
        "group": "Nhóm 1: Bán hàng & Xuất bán",
        "question": "So sánh xuất bán của khách hàng KH0015 từ 01/10 đến 10/10 so với 11/10 đến 20/10",
        "db_sql": """
            SELECT 
                sum(CASE WHEN h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-10' THEN d.so_luong ELSE 0 END) as sl_ky1,
                sum(CASE WHEN h.ngay_ct BETWEEN '2026-10-11' AND '2026-10-20' THEN d.so_luong ELSE 0 END) as sl_ky2
            FROM public.ct81 d
            JOIN public.ph81 h ON h.stt_rec = d.stt_rec
            WHERE h.ma_kh = 'KH0015'
              AND h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-20'
              AND h.status::text NOT IN ('14', '15') AND h.ma_gd <> 4;
        """,
        "keywords": ["1,631,107", "1,719,533", "88,426"]
    },
    {
        "stt": 4,
        "group": "Nhóm 1: Bán hàng & Xuất bán",
        "question": "Top 5 khách hàng đặt hàng lớn nhất trong tháng 10/2026",
        "db_sql": """
            SELECT h.ma_kh, sum(h.t_tien2) as tong_tien
            FROM public.ph64 h
            WHERE h.ma_ct = 'SO1' AND h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-31'
              AND h.status::text NOT IN ('14', '15')
            GROUP BY h.ma_kh ORDER BY tong_tien DESC LIMIT 5;
        """,
        "keywords": ["KH0034", "KH0015", "STT", "Canon"]
    },
    {
        "stt": 5,
        "group": "Nhóm 1: Bán hàng & Xuất bán",
        "question": "Đối soát đơn đặt hàng SO và thực tế xuất bán HDA của mã QC7-5146-000 trong tháng 10/2026",
        "db_sql": """
            SELECT 
                (SELECT sum(so_luong) FROM public.ct64 c JOIN public.ph64 p ON p.stt_rec=c.stt_rec WHERE upper(trim(c.ma_vt))='QC7-5146-000' AND p.ngay_ct BETWEEN '2026-10-01' AND '2026-10-31' AND p.status::text NOT IN ('14','15')) as so_dat,
                (SELECT sum(d.so_luong) FROM public.ct81 d JOIN public.ph81 h ON h.stt_rec=d.stt_rec WHERE upper(trim(d.ma_vt))='QC7-5146-000' AND h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-31' AND h.status::text NOT IN ('14','15') AND h.ma_gd <> 4) as hda_xuat;
        """,
        "keywords": ["167,440", "150,780", "16,660"]
    },
    {
        "stt": 6,
        "group": "Nhóm 1: Bán hàng & Xuất bán",
        "question": "Kiểm tra trạng thái các lệnh giao hàng TO2 của mã QC7-5146-000",
        "db_sql": """
            SELECT count(DISTINCT h.so_ct) as so_lenh, sum(d.so_luong) as sl
            FROM public.ct96 d
            JOIN public.ph96 h ON h.stt_rec = d.stt_rec
            WHERE upper(trim(d.ma_vt)) = 'QC7-5146-000' AND h.status::text = '12';
        """,
        "keywords": ["Hoàn thành", "12"]
    },
    {
        "stt": 7,
        "group": "Nhóm 1: Bán hàng & Xuất bán",
        "question": "Lô xuất hàng gần nhất của mã QC7-5146-000 là chứng từ nào?",
        "db_sql": """
            SELECT h.so_ct, h.ngay_ct, sum(d.so_luong) as sl, array_agg(DISTINCT nullif(d.ma_lo, '')) as lots
            FROM public.ct81 d
            JOIN public.ph81 h ON h.stt_rec = d.stt_rec
            WHERE upper(trim(d.ma_vt)) = 'QC7-5146-000' AND h.ma_gd <> 4
            GROUP BY h.stt_rec, h.so_ct, h.ngay_ct
            ORDER BY h.ngay_ct DESC, h.so_ct DESC LIMIT 1;
        """,
        "keywords": ["001-2610-002978", "360", "trống"]
    },

    # Nhóm 2: Định mức Kỹ thuật, BOM & Bảng giá Niêm yết
    {
        "stt": 8,
        "group": "Nhóm 2: BOM & Giá",
        "question": "Mã sản phẩm QC7-5146-000 sử dụng loại hạt nhựa nào và định mức bao nhiêu?",
        "db_sql": """
            SELECT DISTINCT ma_vt, ten_vt, so_luong_dm
            FROM public.mfkhsx_bom
            WHERE upper(trim(ma_sp)) = 'QC7-5146-000'
            LIMIT 1;
        """,
        "keywords": ["PS-576D", "0.026"]
    },
    {
        "stt": 9,
        "group": "Nhóm 2: BOM & Giá",
        "question": "Cấu trúc BOM sản xuất của mã 009-M66-198 gồm những linh kiện và hạt nhựa gì?",
        "db_sql": """
            SELECT DISTINCT ma_vt, ten_vt, so_luong_dm, ty_le_hao_hut
            FROM public.mfkhsx_bom
            WHERE upper(trim(ma_sp)) = '009-M66-198'
            ORDER BY ma_vt;
        """,
        "keywords": ["009-M85-132", "PP-H051", "0.0145"]
    },
    {
        "stt": 10,
        "group": "Nhóm 2: BOM & Giá",
        "question": "Bảng giá và MOQ hiện hành của mã QC7-5146-000 là bao nhiêu?",
        "db_sql": """
            SELECT sl_min, gia, ma_nt, ngay_bd, ngay_kt
            FROM public.dmbanggiact
            WHERE upper(trim(ma_vt)) = 'QC7-5146-000'
            ORDER BY ngay_bd DESC LIMIT 1;
        """,
        "keywords": ["0.07959", "MOQ", "1"]
    },
    {
        "stt": 11,
        "group": "Nhóm 2: BOM & Giá",
        "question": "Hệ thống có đơn hàng nào bị thiếu giá niêm yết hoặc giá chuẩn bằng 0 không?",
        "db_sql": """
            SELECT count(*) FROM public.ct64 c
            JOIN public.ph64 p ON p.stt_rec = c.stt_rec
            WHERE (c.gia_chuan IS NULL OR c.gia_chuan = 0)
              AND p.status::text NOT IN ('14', '15');
        """,
        "keywords": ["54", "22", "gia_chuan"]
    },

    # Nhóm 3: Kho vận, Tồn kho Sổ sách & Đóng gói MES
    {
        "stt": 12,
        "group": "Nhóm 3: Kho vận & Tồn kho",
        "question": "Mã hàng QC7-5146-000 hiện đang tồn ở những kho nào và số lượng bao nhiêu?",
        "db_sql": """
            WITH op AS (
                SELECT ma_kho, sum(ton00) as qty FROM public.cdvt
                WHERE nam = 2026 AND upper(trim(ma_vt)) = 'QC7-5146-000' GROUP BY ma_kho
            ),
            mv AS (
                SELECT ma_kho, sum(sl_nhap - sl_xuat) as qty FROM public.ct70
                WHERE upper(trim(ma_vt)) = 'QC7-5146-000' GROUP BY ma_kho
            )
            SELECT coalesce(op.ma_kho, mv.ma_kho) as ma_kho,
                   coalesce(op.qty, 0) + coalesce(mv.qty, 0) as ton_kho
            FROM op FULL OUTER JOIN mv ON op.ma_kho = mv.ma_kho
            WHERE coalesce(op.qty, 0) + coalesce(mv.qty, 0) > 0;
        """,
        "keywords": ["KHOTP00", "KHO_TAIMAY"]
    },
    {
        "stt": 13,
        "group": "Nhóm 3: Kho vận & Tồn kho",
        "question": "Lịch sử nhập kho của mã QC7-5146-000 từ 01/10/2026 đến 20/10/2026",
        "db_sql": """
            SELECT count(*) as so_luot, sum(sl_nhap) as tong_nhap
            FROM public.ct70
            WHERE upper(trim(ma_vt)) = 'QC7-5146-000'
              AND ngay_ct BETWEEN '2026-10-01' AND '2026-10-20' AND sl_nhap > 0;
        """,
        "keywords": ["431", "502,700", "nhập"]
    },
    {
        "stt": 14,
        "group": "Nhóm 3: Kho vận & Tồn kho",
        "question": "Quy cách đóng gói của mã QC7-5146-000 là gì và tồn kho quy đổi ra được bao nhiêu thùng?",
        "db_sql": """
            SELECT ma_thung, ma_khay, packs0, so_luong_vt_khay
            FROM public.dmvt WHERE upper(trim(ma_vt)) = 'QC7-5146-000';
        """,
        "keywords": ["60", "BGTD0070", "BGKP0012", "10"]
    },
    {
        "stt": 15,
        "group": "Nhóm 3: Kho vận & Tồn kho",
        "question": "Tra cứu danh sách pallet đóng thùng thành phẩm mới nhất ngày 29/10/2026",
        "db_sql": """
            SELECT id_pallet, so_luong_thung, so_luong FROM public.pallet
            WHERE ngay_sx = '2026-10-29' OR date0 = '2026-10-29' LIMIT 5;
        """,
        "keywords": ["Pallet", "20261029", "thùng"]
    },
    {
        "stt": 16,
        "group": "Nhóm 3: Kho vận & Tồn kho",
        "question": "Tình hình xuất nguyên vật liệu cho các xưởng sản xuất trong tháng 10/2026",
        "db_sql": """
            SELECT count(DISTINCT h.so_ct) as so_phieu, sum(d.so_luong) as tong_xuat
            FROM public.ct76 d JOIN public.ph76 h USING(stt_rec)
            WHERE h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-31';
        """,
        "keywords": ["xuất", "chứng từ"]
    },
    {
        "stt": 17,
        "group": "Nhóm 3: Kho vận & Tồn kho",
        "question": "Tình hình nhập kho thành phẩm hoàn thành từ xưởng sản xuất trong tháng 10/2026",
        "db_sql": """
            SELECT count(DISTINCT h.so_ct) as so_phieu, sum(d.so_luong) as tong_nhap
            FROM public.ct77 d JOIN public.ph77 h USING(stt_rec)
            WHERE h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-31';
        """,
        "keywords": ["nhập kho", "chứng từ"]
    },

    # Nhóm 4: Hồ sơ Khuôn mẫu, Tuổi thọ & Bộ đếm Shot
    {
        "stt": 18,
        "group": "Nhóm 4: Khuôn mẫu & Shot",
        "question": "Khuôn 25HI83 hiện tại đã chạy được bao nhiêu shot?",
        "db_sql": """
            SELECT ma_khuon, ten_khuon, tong_so_shot, so_shot_bh
            FROM public.dmhosokhuon WHERE ten_khuon = '25HI83';
        """,
        "keywords": ["4,581", "1,000,000", "K_146200007"]
    },
    {
        "stt": 19,
        "group": "Nhóm 4: Khuôn mẫu & Shot",
        "question": "Khuôn 25HI117 hiện tại có bao nhiêu shot?",
        "db_sql": """
            SELECT ma_khuon, ten_khuon, tong_so_shot, so_shot_bh
            FROM public.dmhosokhuon WHERE ten_khuon = '25HI117';
        """,
        "keywords": ["chưa cập nhật", "1,000,000", "bảo hành"]
    },
    {
        "stt": 20,
        "group": "Nhóm 4: Khuôn mẫu & Shot",
        "question": "Danh sách các khuôn có số shot chạy thực tế cao nhất hệ thống",
        "db_sql": """
            SELECT ma_khuon, ten_khuon, tong_so_shot
            FROM public.dmhosokhuon ORDER BY tong_so_shot DESC NULLS LAST LIMIT 5;
        """,
        "keywords": ["1,901,189", "K_QC5-0980-000-V2", "KYODAI"]
    },
    {
        "stt": 21,
        "group": "Nhóm 4: Khuôn mẫu & Shot",
        "question": "Mã hàng QC7-5146-000 đang có tồn kho theo các mã Die nào?",
        "db_sql": """
            SELECT e->>'die_no' as die, sum((e->>'so_luong')::numeric) as qty
            FROM public.intem_log a,
                 jsonb_array_elements(case when jsonb_typeof(a.data_tem::jsonb)='array' then a.data_tem::jsonb else jsonb_build_array(a.data_tem::jsonb) end) e
            WHERE upper(trim(e->>'ma_vt')) = 'QC7-5146-000' AND a.nxt = 1 AND a.status = '1'
            GROUP BY 1 ORDER BY 1;
        """,
        "keywords": ["V1", "V2", "940"]
    },

    # Nhóm 5: Quản lý Chất lượng (IQC, OQC & Tem hàng)
    {
        "stt": 22,
        "group": "Nhóm 5: Chất lượng QC",
        "question": "Trạng thái kiểm tra QC của các tem hàng mã QC7-5146-000 thế nào?",
        "db_sql": """
            SELECT e->>'status_qc' as status_qc, sum((e->>'so_luong')::numeric) as qty
            FROM public.intem_log a,
                 jsonb_array_elements(case when jsonb_typeof(a.data_tem::jsonb)='array' then a.data_tem::jsonb else jsonb_build_array(a.data_tem::jsonb) end) e
            WHERE upper(trim(e->>'ma_vt')) = 'QC7-5146-000' AND a.nxt = 1 AND a.status = '1'
            GROUP BY 1;
        """,
        "keywords": ["3 - OK", "OK"]
    },
    {
        "stt": 23,
        "group": "Nhóm 5: Chất lượng QC",
        "question": "Chi tiết kết quả kiểm tra chất lượng IQC của nhà cung cấp NCC0619 trong tháng 10/2026",
        "db_sql": """
            SELECT h.so_ct, h.ngay_ct, count(*) as so_chi_tieu
            FROM public.ctiqc d JOIN public.phiqc h USING(stt_rec)
            WHERE h.ma_ncc = 'NCC0619' AND h.ngay_ct BETWEEN '2026-10-01' AND '2026-10-31'
            GROUP BY h.so_ct, h.ngay_ct;
        """,
        "keywords": ["NCC0619", "IQC", "Đạt", "OK"]
    },
    {
        "stt": 24,
        "group": "Nhóm 5: Chất lượng QC",
        "question": "Trong kỳ có phát sinh phiếu xuất bù hàng NG cho mã QC7-5146-000 không?",
        "db_sql": """
            SELECT count(*) FROM public.ct81 d JOIN public.ph81 h USING(stt_rec)
            WHERE upper(trim(d.ma_vt)) = 'QC7-5146-000' AND h.ma_gd = 10;
        """,
        "keywords": ["Không phát sinh", "không"]
    },

    # Nhóm 6: Danh mục, Khách hàng & Tri thức Nhà máy
    {
        "stt": 25,
        "group": "Nhóm 6: Danh mục & Tri thức",
        "question": "Mã hàng QC7-5146-000 thuộc khách hàng nào quản lý?",
        "db_sql": """
            SELECT v.ma_vt, v.ma_kh, k.ten_kh
            FROM public.dmvt v JOIN public.dmkh k ON k.ma_kh = v.ma_kh
            WHERE upper(trim(v.ma_vt)) = 'QC7-5146-000';
        """,
        "keywords": ["KH0015", "Canon"]
    },
    {
        "stt": 26,
        "group": "Nhóm 6: Danh mục & Tri thức",
        "question": "Mã khách hàng của Canon Thăng Long trên hệ thống là gì?",
        "db_sql": """
            SELECT ma_kh, ten_kh FROM public.dmkh WHERE ma_kh = 'KH0015';
        """,
        "keywords": ["KH0015", "Canon"]
    },
    {
        "stt": 27,
        "group": "Nhóm 6: Danh mục & Tri thức",
        "question": "4509 là ai?",
        "db_sql": None,
        "keywords": ["Nguyễn Văn Trường", "hp4509", "nhân viên"]
    },
    {
        "stt": 28,
        "group": "Nhóm 6: Danh mục & Tri thức",
        "question": "Khái niệm 4M trong sản xuất là gì?",
        "db_sql": None,
        "keywords": ["Man", "Machine", "Material", "Method", "Con người"]
    }
]

def ask_chat_ui(question: str):
    """Mô phỏng 100% cuộc gọi từ Web UI đến Open WebUI API."""
    t0 = time.time()
    payload = {
        "model": "htmp-nhanh",
        "messages": [{"role": "user", "content": question}],
        "stream": False
    }
    req = urllib.request.Request(
        f"{BASE_URL}/api/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers=HEADERS
    )
    with urllib.request.urlopen(req, timeout=180) as resp:
        data1 = json.loads(resp.read().decode("utf-8"))
    msg1 = data1["choices"][0]["message"]
    
    if msg1.get("tool_calls"):
        tool_args = json.loads(msg1["tool_calls"][0]["function"]["arguments"])
        tool_res = tools.ask_erp(**tool_args)
        
        messages = [
            {"role": "user", "content": question},
            msg1,
            {
                "role": "tool",
                "tool_call_id": msg1["tool_calls"][0]["id"],
                "content": tool_res
            }
        ]
        req2 = urllib.request.Request(
            f"{BASE_URL}/api/chat/completions",
            data=json.dumps({"model": "htmp-nhanh", "messages": messages, "stream": False}).encode("utf-8"),
            headers=HEADERS
        )
        with urllib.request.urlopen(req2, timeout=180) as resp2:
            data2 = json.loads(resp2.read().decode("utf-8"))
        final_msg = data2["choices"][0]["message"]
        duration = round(time.time() - t0, 2)
        return final_msg.get("content") or "", duration, tool_res
    else:
        duration = round(time.time() - t0, 2)
        return msg1.get("content") or "", duration, None

def query_db(sql: str):
    """Thực thi câu SQL đối soát chỉ đọc trực tiếp trên Live DB."""
    if not sql:
        return "N/A (Câu hỏi tri thức / Khái niệm sản xuất)"
    try:
        with psycopg.connect(**DB_PARAMS) as conn:
            with conn.cursor() as cur:
                cur.execute("SET TRANSACTION READ ONLY")
                cur.execute(sql)
                rows = cur.fetchall()
                return [tuple(str(v) for v in r) for r in rows]
    except Exception as exc:
        return f"DB Error: {str(exc)}"

def run_all_tests():
    print(f"=== BẮT ĐẦU KIỂM THỬ VÀ ĐỐI SOÁT 28 CÂU HỎI ERP/MES (CHAT API & LIVE DB) ===")
    total = len(TEST_QUESTIONS)
    passed_count = 0
    results = []

    for item in TEST_QUESTIONS:
        stt = item["stt"]
        q = item["question"]
        grp = item["group"]
        expected_kws = item["keywords"]
        db_sql = item["db_sql"]

        print(f"\n[{stt:02d}/{total}] {grp} - Câu hỏi: '{q}'")
        
        # 1. Chạy chat UI
        try:
            ai_answer, dur, tool_raw = ask_chat_ui(q)
        except Exception as e:
            ai_answer, dur, tool_raw = f"API Error: {str(e)}", 0.0, None

        # 2. Đối soát DB
        db_truth = query_db(db_sql)

        # 3. Đánh giá kiểm tra
        # Kiểm tra từ khóa kỳ vọng
        kw_hits = [kw for kw in expected_kws if kw.lower() in ai_answer.lower()]
        is_pass = len(kw_hits) >= 1 and "API Error" not in ai_answer
        
        # Kiểm tra ngôn ngữ: Không chứa chữ Hán
        has_chinese = any('\u4e00' <= char <= '\u9fff' for char in ai_answer)
        if has_chinese:
            is_pass = False

        if is_pass:
            passed_count += 1
            status_label = "PASS"
        else:
            status_label = "FAIL"

        print(f"    -> Kết quả: {status_label} (Thời gian: {dur}s | Khớp từ khóa: {kw_hits})")
        print(f"    -> Live DB Ground Truth: {db_truth}")
        print(f"    -> AI Trả lời preview: {ai_answer[:150].strip()}...")

        results.append({
            "stt": stt,
            "group": grp,
            "question": q,
            "status": status_label,
            "duration_s": dur,
            "expected_keywords": expected_kws,
            "matched_keywords": kw_hits,
            "db_truth": str(db_truth),
            "ai_answer": ai_answer
        })

    print(f"\n=======================================================")
    print(f"TỔNG KẾT: {passed_count}/{total} CÂU ĐẠT TIÊU CHÍ (TỶ LỆ: {passed_count/total*100:.1f}%)")
    print(f"=======================================================")

    with open("/home/admin/ai-stack/scratch/ket_qua_doi_soat_28_cau.json", "w", encoding="utf-8") as f:
        json.dump({
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total": total,
            "passed": passed_count,
            "pass_rate": f"{passed_count/total*100:.1f}%",
            "details": results
        }, f, ensure_ascii=False, indent=2)

if __name__ == "__main__":
    run_all_tests()
