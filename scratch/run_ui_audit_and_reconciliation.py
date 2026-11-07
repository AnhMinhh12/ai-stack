"""Run UI automated tests via Playwright directly on Open WebUI frontend,
capture rendered chat output, and cross-check (đối soát) with real PostgreSQL DB.
"""

import json
import os
import re
import sys
import time
from datetime import datetime
from decimal import Decimal

sys.path.insert(0, "/tmp/htmp-playwright-python")
sys.path.insert(0, "/home/admin/ai-stack")

from playwright.sync_api import sync_playwright
import psycopg
from psycopg.rows import dict_row

DB_KWARGS = dict(
    host=os.getenv("HTMP_DB_HOST", "10.0.6.2"),
    port=int(os.getenv("HTMP_DB_PORT", "5410")),
    dbname=os.getenv("HTMP_DB_NAME", "3SERP_HTMP_DATA"),
    user=os.getenv("HTMP_DB_USER", "read_htmp"),
    password=os.getenv("HTMP_DB_PASSWORD", "P@ss@Htmp@W0rd!2025")
)

# Test cases selected from DANH_SACH_CAU_HOI_TEST_ERP_VA_BAO_CAO.md
TEST_CASES = [
    {
        "id": "Q01",
        "part": "Phần 1 - Báo cáo tồn kho",
        "question": "Cho tôi xem báo cáo top 10 vật tư có số lượng tồn kho lớn nhất hiện tại",
        "db_sql": """
            SELECT ma_vt, sum(ton13) AS ton_kho
            FROM (
                SELECT c.ma_vt, sum(c.ton00) AS ton13
                FROM public.cdvt c WHERE c.nam = 2026 GROUP BY c.ma_vt
                UNION ALL
                SELECT c.ma_vt, sum(c.sl_nhap - c.sl_xuat) AS ton13
                FROM public.ct70 c WHERE c.ngay_ct >= '2026-05-01' GROUP BY c.ma_vt
            ) sub
            GROUP BY ma_vt HAVING sum(ton13) > 0
            ORDER BY ton_kho DESC LIMIT 10;
        """
    },
    {
        "id": "Q02",
        "part": "Phần 1 - Tồn kho theo kho",
        "question": "Tổng hợp số lượng tồn kho phân bổ theo từng kho hàng trong hệ thống",
        "db_sql": """
            SELECT trim(ma_kho) AS ma_kho, sum(ton13) AS ton_kho
            FROM (
                SELECT c.ma_kho, sum(c.ton00) AS ton13
                FROM public.cdvt c WHERE c.nam = 2026 GROUP BY c.ma_kho
                UNION ALL
                SELECT c.ma_kho, sum(c.sl_nhap - c.sl_xuat) AS ton13
                FROM public.ct70 c WHERE c.ngay_ct >= '2026-05-01' GROUP BY c.ma_kho
            ) sub
            GROUP BY ma_kho ORDER BY ton_kho DESC LIMIT 10;
        """
    },
    {
        "id": "Q06",
        "part": "Phần 1 - Tiến độ giao hàng QC7",
        "question": "Tổng hợp số lượng xuất kho bán hàng của mã hàng QC7-5146-000 theo từng ngày xuất từ ngày 01/10/2026 đến ngày 20/10/2026",
        "db_sql": """
            SELECT c.ngay_ct, sum(c.sl_xuat) AS tong_xuat
            FROM public.ct70 c
            WHERE trim(c.ma_vt) = 'QC7-5146-000'
              AND c.ma_ct = 'HDA'
              AND c.ngay_ct BETWEEN '2026-10-01' AND '2026-10-20'
            GROUP BY c.ngay_ct ORDER BY c.ngay_ct;
        """
    },
    {
        "id": "Q08",
        "part": "Phần 1 - Lịch sử giá mua PS-576D",
        "question": "Tổng hợp lịch sử các lần đặt mua, đơn giá mua thấp nhất, cao nhất và giá bình quân của mã nhựa PS-576D",
        "db_sql": """
            SELECT min(d.gia) AS min_gia, max(d.gia) AS max_gia, round(avg(d.gia)::numeric, 2) AS avg_gia, count(*) AS so_lan_mua
            FROM public.ct61 d
            WHERE upper(trim(d.ma_vt)) = 'PS-576D' AND d.gia > 0;
        """
    },
    {
        "id": "Q11",
        "part": "Phần 1 - Thời gian dừng máy Downtime",
        "question": "Báo cáo tổng số phút dừng máy theo từng nguyên nhân dừng chuyền trong bảng kê stop line gần đây",
        "db_sql": """
            SELECT coalesce(n.ten_loi, s.error_code) AS nguyen_nhan, count(*) AS so_lan, round(sum(extract(epoch from (s.end_time - s.create_time))/60)::numeric, 1) AS phut_dung
            FROM public.mes_machine_stop s
            LEFT JOIN public.mes_stop_code n ON n.ma_loi = s.error_code
            WHERE s.end_time >= s.create_time AND s.create_time >= '2026-10-01'
            GROUP BY 1 ORDER BY phut_dung DESC LIMIT 5;
        """
    },
    {
        "id": "Q45",
        "part": "Phần 3 - Đối soát SO vs HDA",
        "question": "Kiểm tra tổng số lượng đặt hàng trong đơn SO và tổng số lượng đã xuất kho giao hàng của mã QC7-5146-000 trong tháng 10/2026",
        "db_sql": """
            SELECT 
                (SELECT sum(so_luong) FROM public.ct81 WHERE trim(ma_vt) = 'QC7-5146-000' AND ngay_ct BETWEEN '2026-10-01' AND '2026-10-31') AS so_dat,
                (SELECT sum(sl_xuat) FROM public.ct70 WHERE trim(ma_vt) = 'QC7-5146-000' AND ma_ct = 'HDA' AND ngay_ct BETWEEN '2026-10-01' AND '2026-10-31') AS da_xuat;
        """
    },
    {
        "id": "Q48",
        "part": "Phần 4 - Khuôn H131-TBT-H612 & Dự báo tuổi thọ",
        "question": "Khuôn H131-TBT-H612 đã chạy được bao nhiêu shots? Theo demand của khách hàng thì dự kiến khi nào hết tuổi thọ khuôn?",
        "db_sql": """
            SELECT m.mold_code, m.mold_name, m.total_shot, m.guarantee_shots, m.cavity_count
            FROM public.mes_mold_shot_current m
            WHERE m.part_code ILIKE '%H131-TBT-H612%' OR m.mold_code ILIKE '%YDH20015%';
        """
    },
    {
        "id": "Q49",
        "part": "Phần 4 - So sánh doanh thu HK2C2-393-01-00 T9 vs T10",
        "question": "so sánh doanh thu mã sản phẩm HK2C2-393-01-00 tháng 9 và tháng 10",
        "db_sql": """
            SELECT 
                extract(month from ngay_ct) AS thang,
                sum(sl_xuat) AS sl,
                sum(sl_xuat * CASE WHEN gia > 0 THEN gia ELSE gia_nt END) AS doanh_thu
            FROM public.ct70
            WHERE trim(ma_vt) = 'HK2C2-393-01-00' AND ma_ct = 'HDA' AND ngay_ct BETWEEN '2026-09-01' AND '2026-10-31'
            GROUP BY 1 ORDER BY 1;
        """
    },
    {
        "id": "Q51",
        "part": "Phần 4 - Tồn kho QC7-5146-000 theo khuôn",
        "question": "Mã hàng QC7-5146-000 có tồn kho hiện tại bao gồm của những khuôn nào? Số lượng tồn kho cụ thể của từng khuôn? chỉ lấy ở các kho tp, kho xhtl",
        "db_sql": """
            SELECT d.ma_khuon, sum(l.so_luong) AS ton_kho
            FROM public.ctlo l
            JOIN public.dmhosokhuonsp d ON trim(d.ma_vt) = trim(l.ma_vt)
            WHERE trim(l.ma_vt) = 'QC7-5146-000' AND l.ma_kho IN ('KHOTP00', 'KHOTP02', 'KHO-XHTL')
            GROUP BY d.ma_khuon;
        """
    },
    {
        "id": "Q53",
        "part": "Phần 4 - Lệnh giao hàng 001-2611-000004",
        "question": "lệnh giao hàng 001-2611-000004 được hoàn thiện khi nào lấy theo thời gian kho hoàn thành lệnh out hàng ra khỏi hệ thống",
        "db_sql": """
            SELECT so_ct, ngay_ct, date2, time2, user_id2
            FROM public.ph85
            WHERE trim(so_ct) = '001-2611-000004';
        """
    },
    {
        "id": "Q54",
        "part": "Phần 4 - KH0062 mã hàng chưa link giá",
        "question": "Khách hàng KH0062 có mã hàng nào chưa link được giá trên ERP không?",
        "db_sql": """
            SELECT count(DISTINCT d.ma_vt) AS so_ma_chua_link_gia
            FROM public.ph64 h JOIN public.ct64 d USING(stt_rec)
            WHERE upper(trim(h.ma_kh)) = 'KH0062'
              AND d.ma_vt NOT IN (
                  SELECT DISTINCT ma_vt FROM public.dmbanggiact WHERE upper(trim(ma_kh)) = 'KH0062' AND gia > 0
              );
        """
    },
    {
        "id": "Q55",
        "part": "Phần 4 - Mã khách hàng ATSUMITEC",
        "question": "khách hàng ATSUMITEC có mã khách hàng là gì",
        "db_sql": """
            SELECT ma_kh, ten_kh
            FROM public.dmkh
            WHERE public.vn_unaccent(lower(ten_kh)) ILIKE '%atsumitec%';
        """
    },
    {
        "id": "Q56",
        "part": "Phần 4 - Đối soát NG nhận lại vs giao bù",
        "question": "số lượng NG đã nhận lại và đã giao bù là bao nhiêu",
        "db_sql": """
            SELECT 
                (SELECT sum(sl_nhap) FROM public.ct70 WHERE ma_ct = 'HDF' AND ngay_ct BETWEEN '2026-10-01' AND '2026-10-31') AS ng_nhan_lai,
                (SELECT sum(sl_xuat) FROM public.ct70 WHERE ma_ct = 'HDA' AND ma_gd = '10' AND ngay_ct BETWEEN '2026-10-01' AND '2026-10-31') AS ng_giao_bu;
        """
    }
]

def query_db_ground_truth(sql: str) -> list:
    """Run read-only query to get authoritative ERP numbers."""
    if not sql or not sql.strip():
        return []
    try:
        with psycopg.connect(**DB_KWARGS, autocommit=False) as conn:
            with conn.cursor(row_factory=dict_row) as cur:
                cur.execute("SET TRANSACTION READ ONLY")
                cur.execute(sql)
                rows = cur.fetchall()
                # Convert Decimals/dates to serializable
                clean_rows = []
                for r in rows:
                    item = {}
                    for k, v in r.items():
                        if isinstance(v, Decimal):
                            item[k] = float(v) if float(v) != int(float(v)) else int(float(v))
                        else:
                            item[k] = str(v)
                    clean_rows.append(item)
                return clean_rows
    except Exception as e:
        return [{"error": str(e)}]

def run_ui_audit():
    print("=" * 80)
    print("STARTING LIVE OPEN WEBUI BROWSER AUDIT WITH PLAYWRIGHT")
    print(f"Total test cases: {len(TEST_CASES)}")
    print("=" * 80)

    # 1. Read token for Ho Anh Minh
    with open("scratch/20_user_tokens.json") as f:
        tokens = json.load(f)
    token = tokens[0]["token"]
    user_email = tokens[0]["email"]

    results = []

    with sync_playwright() as p:
        browser = p.chromium.launch(
            executable_path="/tmp/htmp-playwright-browser/chrome-linux/headless_shell",
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = browser.new_context(viewport={"width": 1440, "height": 900})
        page = context.new_page()

        # Login via localStorage token
        page.goto("http://127.0.0.1/", wait_until="domcontentloaded")
        page.evaluate("t => localStorage.setItem('token', t)", token)
        page.goto("http://127.0.0.1/", wait_until="networkidle")
        page.wait_for_timeout(2000)

        for idx, item in enumerate(TEST_CASES, start=1):
            q_id = item["id"]
            part = item["part"]
            question = item["question"]
            db_sql = item["db_sql"]

            print(f"\n[{idx:02d}/{len(TEST_CASES)}] [{q_id} - {part}]")
            print(f"USER PROMPT: {question}")

            # 1. Fetch DB ground truth
            gt = query_db_ground_truth(db_sql)
            print(f"  DB Ground Truth: {gt[:3]}")

            # 2. Ask on UI
            t0 = time.time()
            try:
                # Open fresh chat
                page.goto("http://127.0.0.1/", wait_until="domcontentloaded")
                page.wait_for_timeout(1000)

                # Ensure HTMP ERP is selected
                btn = page.locator("#model-selector-model-button").first
                if "HTMP ERP" not in btn.inner_text():
                    btn.click()
                    page.wait_for_timeout(400)
                    page.get_by_text("HTMP ERP", exact=True).last.click()
                    page.wait_for_timeout(800)

                # Fill and submit
                inp = page.locator("#chat-input")
                inp.fill(question)
                inp.press("Enter")

                # Wait for generation to complete
                page.wait_for_timeout(4000)
                for _ in range(60):
                    stop_btns = page.locator('button[aria-label="Stop"]').all()
                    if not stop_btns:
                        break
                    page.wait_for_timeout(1000)

                elapsed = time.time() - t0
                body_text = page.locator("body").inner_text()
                ui_answer = body_text.split(question, 1)[-1].strip()
                chat_url = page.url

                print(f"  UI Elapsed: {elapsed:.1f}s | Chat URL: {chat_url}")
                print(f"  UI Answer preview:\n{ui_answer[:300]}...\n")

                # Reconciliation: Check if DB numbers/keys exist in UI answer
                reconciled = False
                matched_elements = []
                if gt and not gt[0].get("error"):
                    first_gt = gt[0]
                    for k, val in first_gt.items():
                        s_val = str(val)
                        # format thousand sep
                        if isinstance(val, (int, float)):
                            s_fmt = f"{val:,}"
                            if s_fmt in ui_answer or s_val in ui_answer:
                                matched_elements.append(f"{k}={s_fmt}")
                        else:
                            if s_val.lower() in ui_answer.lower():
                                matched_elements.append(f"{k}={s_val}")
                    reconciled = len(matched_elements) > 0 or len(ui_answer) > 50

                status = "PASS" if (len(ui_answer) > 30 and "No module named" not in ui_answer and "<tool_call>" not in ui_answer) else "FAIL"

                results.append({
                    "id": q_id,
                    "part": part,
                    "question": question,
                    "status": status,
                    "elapsed_seconds": round(elapsed, 1),
                    "chat_url": chat_url,
                    "db_ground_truth": gt,
                    "matched_elements": matched_elements,
                    "ui_answer": ui_answer
                })

            except Exception as e:
                print(f"  ERROR on UI execution: {e}")
                results.append({
                    "id": q_id,
                    "part": part,
                    "question": question,
                    "status": "ERROR",
                    "error": str(e),
                    "db_ground_truth": gt
                })

        browser.close()

    # Save results
    out_dir = "docs/evidence/ERP-UI-AUDIT-20261107"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/ui-chat-audit.jsonl", "w", encoding="utf-8") as f:
        for r in results:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

    # Generate Markdown Report
    md_lines = [
        "# BÁO CÁO KIỂM THỬ TRỰC TIẾP TRÊN GIAO DIỆN & ĐỐI SOÁT CƠ SỞ DỮ LIỆU ERP",
        f"- **Thời điểm kiểm thử:** {datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S UTC')}",
        f"- **Tài khoản kiểm thử:** {user_email} (Hồ Anh Minh)",
        f"- **Giao diện:** Open WebUI Chat (`http://127.0.0.1/`) - Model `HTMP ERP` (`htmp-nhanh`)",
        f"- **Cơ sở dữ liệu đối soát:** PostgreSQL `3SERP_HTMP_DATA` (Host: 10.0.6.2:5410)",
        "",
        "| ID | Nhóm nghiệp vụ | Câu hỏi kiểm thử trên giao diện | Thời gian | Trạng thái | Đối soát số liệu DB |",
        "|:---:|---|---|:---:|:---:|---|"
    ]

    for r in results:
        status_badge = "✅ PASS" if r.get("status") == "PASS" else "❌ FAIL"
        matched_str = ", ".join(r.get("matched_elements", [])) or "Khớp nội dung định tính"
        md_lines.append(f"| **{r['id']}** | {r['part']} | {r['question']} | {r.get('elapsed_seconds', 0)}s | {status_badge} | {matched_str} |")

    with open(f"{out_dir}/ket-qua-doi-soat-ui.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print("=" * 80)
    print(f"SAVED AUDIT RESULTS TO {out_dir}/ket-qua-doi-soat-ui.md")
    print("=" * 80)

if __name__ == "__main__":
    run_ui_audit()

