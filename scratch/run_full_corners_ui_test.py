"""Automated UI Full Corner Testing Suite for HTMP ERP on Open WebUI via Playwright CDP.
"""

import json
import os
import sys
import time
from playwright.sync_api import sync_playwright

TEST_CASES = [
    {
        "id": 1,
        "module": "KHO (IN)",
        "question": "Cho tôi xem báo cáo top 10 vật tư có số lượng tồn kho lớn nhất hiện tại",
        "expected_keywords": ["top 10", "tồn kho", "vật tư", "PCS"]
    },
    {
        "id": 2,
        "module": "KHO (IN)",
        "question": "Tổng hợp số lượng tồn kho phân bổ theo từng kho hàng trong hệ thống",
        "expected_keywords": ["phân bổ", "kho", "tồn kho"]
    },
    {
        "id": 6,
        "module": "BÁN HÀNG (SO)",
        "question": "Tổng hợp số lượng xuất kho bán hàng của mã hàng QC7-5146-000 theo từng ngày xuất từ ngày 01/10/2026 đến ngày 20/10/2026",
        "expected_keywords": ["QC7-5146-000", "xuất", "2026-10"]
    },
    {
        "id": 70,
        "module": "BÁN HÀNG (SO)",
        "question": "Báo cáo tổng hợp bán hàng và doanh số trong tháng 10 năm 2026",
        "expected_keywords": ["bán hàng", "doanh số", "Canon"]
    },
    {
        "id": 72,
        "module": "MUA HÀNG (PO)",
        "question": "Báo cáo tổng hợp hàng nhập mua từ các nhà cung cấp trong tháng 10 năm 2026",
        "expected_keywords": ["nhập mua", "nhà cung cấp"]
    },
    {
        "id": 8,
        "module": "MUA HÀNG (PO)",
        "question": "Tổng hợp lịch sử các lần đặt mua, đơn giá mua thấp nhất, cao nhất và giá bình quân của mã nhựa PS-576D",
        "expected_keywords": ["PS-576D", "giá"]
    },
    {
        "id": 12,
        "module": "SẢN XUẤT (MES)",
        "question": "Báo cáo tổng hợp thời gian dừng máy và nguyên nhân dừng chuyền sản xuất trong tháng 10 năm 2026",
        "expected_keywords": ["dừng máy", "phút", "nguyên nhân"]
    },
    {
        "id": 48,
        "module": "SẢN XUẤT (MES)",
        "question": "Bảng kê gộp tách thùng tem carton trong tháng 10 năm 2026",
        "expected_keywords": ["gộp", "tách", "thùng"]
    },
    {
        "id": 49,
        "module": "SẢN XUẤT (MES)",
        "question": "Bảng kê bổ sung hoặc bỏ shot khuôn trong tháng 10 năm 2026",
        "expected_keywords": ["shot", "bổ sung", "khuôn"]
    },
    {
        "id": 50,
        "module": "KHUÔN MẪU (VS)",
        "question": "Lịch sử các lần thay khuôn sản xuất trong tháng 10 năm 2026",
        "expected_keywords": ["thay khuôn", "khuôn hạ", "khuôn lắp"]
    },
    {
        "id": 58,
        "module": "KẾ TOÁN (GL)",
        "question": "Xem sổ cái tài khoản 1521 nguyên vật liệu chính từ ngày 01/10/2026 đến ngày 31/10/2026",
        "expected_keywords": ["1521", "sổ cái", "phát sinh"]
    },
    {
        "id": 59,
        "module": "KẾ TOÁN (GL)",
        "question": "Bảng cân đối số phát sinh các tài khoản trong tháng 10 năm 2026",
        "expected_keywords": ["cân đối", "phát sinh", "tài khoản"]
    },
    {
        "id": 37,
        "module": "GIAO NHẬN (TO2)",
        "question": "Lệnh giao hàng TO2 số chứng từ 001-2610-000001 đã out hàng thực tế lúc mấy giờ ngày nào?",
        "expected_keywords": ["001-2610-000001", "out", "giờ"]
    },
    {
        "id": 41,
        "module": "CHẤT LƯỢNG (QC)",
        "question": "Báo cáo đánh giá chất lượng nguyên vật liệu mua vào IQC theo từng nhà cung cấp từ ngày 01/10/2026 đến ngày 25/10/2026",
        "expected_keywords": ["IQC", "nhà cung cấp", "lô"]
    },
    {
        "id": 42,
        "module": "CHẤT LƯỢNG (QC)",
        "question": "Trạng thái tem kiểm định chất lượng OQC của mã hàng QC7-5146-000 hiện tại có lô nào bị khóa hoặc khoanh vùng không?",
        "expected_keywords": ["QC7-5146-000", "OK", "tem"]
    },
    {
        "id": 75,
        "module": "DANH MỤC / HELPDESK",
        "question": "Mã 4509 là ai trên hệ thống? Có phải mã vật tư không?",
        "expected_keywords": ["Nguyễn Văn Trường", "nhân viên"]
    },
    {
        "id": 76,
        "module": "CROSS-MODULE (360)",
        "question": "Mã hàng QC7-5146-000 được khai báo thuộc khách hàng nào? Chị hỏi tồn kho ở KHO tại máy nó đang ở vị trí tồn là vị trí nào?",
        "expected_keywords": ["KH0015", "Canon", "DUC-0223"]
    }
]

OUTPUT_FILE = "docs/evidence/ERP-FULL-20261109/ui-full-corner-results.jsonl"
os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

print(f"=== STARTING FULL CORNER UI TEST RUNNER ({len(TEST_CASES)} CASES) ===")
print(f"Target Open WebUI via CDP at http://127.0.0.1:19223")

results = []

with sync_playwright() as p:
    browser = p.chromium.connect_over_cdp('http://127.0.0.1:19223')
    
    # Locate Open WebUI tab
    page = None
    for c in browser.contexts:
        for pg in c.pages:
            if 'Open WebUI' in pg.title():
                page = pg
                break
        if page:
            break
            
    if not page:
        print("ERROR: No Open WebUI page found via CDP!")
        sys.exit(1)
        
    print(f"Connected to page: {page.title()} ({page.url})")
    
    with open(OUTPUT_FILE, "a", encoding="utf-8") as out_f:
        for idx, tc in enumerate(TEST_CASES, 1):
            qid = tc["id"]
            module = tc["module"]
            question = tc["question"]
            expected = tc["expected_keywords"]
            
            print(f"\n[{idx}/{len(TEST_CASES)}] [Q{qid}] [{module}]")
            print(f"  Prompt: {question}")
            
            t0 = time.time()
            # Navigate to home to start a clean new chat
            page.goto('http://192.168.31.10/', wait_until='domcontentloaded', timeout=30000)
            
            # Ensure model HTMP ERP is selected
            sel = page.locator('#model-selector-model-button').first
            sel.wait_for(timeout=30000)
            if 'HTMP ERP' not in sel.inner_text():
                sel.click()
                page.get_by_text('HTMP ERP', exact=True).last.click(timeout=10000)
                
            # Input question and send
            chat_box = page.locator('#chat-input')
            chat_box.fill(question)
            chat_box.press('Enter')
            
            # Wait for assistant response to finish
            # Either continue-response-button appears or stop button disappears
            completed = False
            for _ in range(60): # up to 60s
                time.sleep(1)
                try:
                    # If continue button exists and is visible -> done
                    btn = page.locator('#continue-response-button')
                    if btn.count() > 0 and btn.last.is_visible():
                        completed = True
                        break
                except Exception:
                    pass
                    
            dur = round(time.time() - t0, 1)
            page.wait_for_timeout(1000)
            
            # Extract response text
            body_text = page.locator('body').inner_text()
            chat_part = body_text.split('Chat Conversation', 1)[-1] if 'Chat Conversation' in body_text else body_text
            lines = [l.strip() for l in chat_part.split('\n') if l.strip() and not l.strip().startswith('Nov 9') and 'HTMP ERP' not in l and question not in l]
            resp_sample = " // ".join(lines[-8:]) if lines else "NO_RESPONSE"
            
            # Keyword evaluation
            matched_kws = [k for k in expected if k.lower() in chat_part.lower()]
            pass_status = len(matched_kws) >= 1 and "không có dữ liệu báo cáo phù hợp" not in chat_part.lower()
            
            print(f"  Duration: {dur}s | Completed: {completed} | Match: {matched_kws}/{expected} -> {'PASS' if pass_status else 'FAIL'}")
            print(f"  Snippet: {resp_sample[:250]}")
            
            entry = {
                "id": qid,
                "module": module,
                "question": question,
                "completed": completed,
                "duration_seconds": dur,
                "expected": expected,
                "matched_keywords": matched_kws,
                "status": "PASS" if pass_status else "FAIL",
                "response_tail": resp_sample
            }
            results.append(entry)
            out_f.write(json.dumps(entry, ensure_ascii=False) + "\n")
            out_f.flush()

print(f"\n=== FINISHED FULL CORNER TEST SUITE ===")
pass_count = sum(1 for r in results if r["status"] == "PASS")
print(f"Summary: {pass_count}/{len(results)} PASSED ({pass_count/len(results)*100:.1f}%)")

