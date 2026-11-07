"""Run full test on the 18 user questions through Open WebUI htmp-nhanh API."""

import json
import os
import sys
import time
import urllib.request

BASE_URL = "http://127.0.0.1:80"
API_KEY = "sk-1ce52487dd424dc4b2e8c54fe7041f8c"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

QUESTIONS = [
    {
        "id": 1,
        "question": "Mã hàng QC7-5146-000 dùng loại nhựa gì? Cấu trúc sản phẩm của mã hàng này gồm những gì?",
        "topic": "BOM & Loại nhựa",
        "expected": ["PS-576D", "0.026"]
    },
    {
        "id": 2,
        "question": "MOQ báo giá hiện tại của mã QC7-5146-000 là bao nhiêu? Giá áp dụng hiện tại theo từng mức MOQ là bao nhiêu?",
        "topic": "Bảng giá & MOQ",
        "expected": ["0.07959", "1", "USD"]
    },
    {
        "id": 3,
        "question": "Tính đến ngày 20/10/2026, lot gần nhất được xuất giao của mã QC7-5146-000 là lot nào? Ngày xuất và số lượng bao nhiêu?",
        "topic": "Lot xuất gần nhất",
        "expected": ["20/10/2026", "QC7-5146-000"]
    },
    {
        "id": 4,
        "question": "Từ ngày 01/10/2026 đến hết ngày 20/10/2026, tổng số lượng xuất bán và doanh thu của mã QC7-5146-000 là bao nhiêu?",
        "topic": "Xuất bán & Doanh thu",
        "expected": ["QC7-5146-000"]
    },
    {
        "id": 5,
        "question": "Mã hàng QC7-5146-000 được khai báo thuộc khách hàng nào?",
        "topic": "Khách hàng của sản phẩm",
        "expected": ["KH0015", "Canon"]
    },
    {
        "id": 6,
        "question": "Từ ngày 01/10/2026 đến hết ngày 20/10/2026, mã QC7-5146-000 được nhập kho vào những ngày nào, từ kho nào sang kho nào, số lượng bao nhiêu và tài khoản nào tạo phiếu?",
        "topic": "Lịch sử nhập/chuyển kho",
        "expected": ["QC7-5146-000"]
    },
    {
        "id": 7,
        "question": "So sánh DO và FCST hiện tại với bản trước của mã QC7-5146-000: số lượng tăng hay giảm bao nhiêu?",
        "topic": "So sánh DO vs FCST",
        "expected": ["DO", "FCST"]
    },
    {
        "id": 8,
        "question": "Quy cách đóng gói của mã QC7-5146-000 gồm những thông tin gì? Có thể quy đổi tồn kho hiện tại theo quy cách đóng gói không?",
        "topic": "Quy cách đóng gói & Quy đổi tồn",
        "expected": ["60", "BGTD0070", "BGKP0012", "10"]
    },
    {
        "id": 9,
        "question": "Khuôn K_QC5-2919-000-V1 đã chạy tổng cộng bao nhiêu shot cho mã QC7-5146-000? Với demand của khách KH0015, có đủ dữ liệu để dự kiến thời điểm khuôn hết tuổi thọ không?",
        "topic": "Số shot & Dự báo tuổi thọ khuôn",
        "expected": ["K_QC5-2919-000-V1", "shot"]
    },
    {
        "id": 10,
        "question": "So sánh doanh thu mã QC7-5146-000 của khách KH0015 trong hai khoảng 01/09/2026–20/09/2026 và 01/10/2026–20/10/2026. Nêu số lượng và doanh thu từng kỳ.",
        "topic": "So sánh doanh thu 2 kỳ",
        "expected": ["01/09/2026", "01/10/2026", "QC7-5146-000"]
    },
    {
        "id": 11,
        "question": "Mã QC7-5146-000 hiện có tồn kho thuộc những khuôn nào? Số lượng theo từng khuôn là bao nhiêu?",
        "topic": "Tồn kho theo khuôn",
        "expected": ["QC7-5146-000", "khuôn"]
    },
    {
        "id": 12,
        "question": "Liệt kê dữ liệu đơn hàng bán của khách KH0015 từ ngày 01/10/2026 đến hết ngày 20/10/2026, gồm số đơn, ngày đặt, mã hàng, số lượng và trạng thái.",
        "topic": "Đơn hàng bán KH0015",
        "expected": ["KH0015", "001-2610-"]
    },
    {
        "id": 13,
        "question": "Lệnh giao hàng 001-2610-001811 được ghi nhận hoàn thành khi nào? Cho biết trạng thái lệnh và căn cứ thời gian được dùng.",
        "topic": "Trạng thái lệnh giao hàng",
        "expected": ["001-2610-001811"]
    },
    {
        "id": 14,
        "question": "Tồn kho hiện tại của mã QC7-5146-000 là bao nhiêu ở từng kho?",
        "topic": "Tồn kho theo từng kho",
        "expected": ["KHOTP00", "16,380", "17,740"]
    },
    {
        "id": 15,
        "question": "Mã QC7-5146-000 hiện có lot thành phẩm nào ở trạng thái QC cần chú ý? Cho biết trạng thái QC đúng như dữ liệu ERP.",
        "topic": "Trạng thái QC tem thành phẩm",
        "expected": ["3 - OK", "17,740"]
    },
    {
        "id": 16,
        "question": "Trong đơn hàng của khách KH0015 từ ngày 01/10/2026 đến hết ngày 20/10/2026, có mã hàng nào chưa có giá chuẩn được liên kết không?",
        "topic": "Đơn hàng thiếu giá chuẩn",
        "expected": ["KH0015"]
    },
    {
        "id": 17,
        "question": "Công ty TNHH Canon Việt Nam- Chi nhánh Thăng Long có mã khách hàng nào trên ERP?",
        "topic": "Mã khách hàng Canon Thăng Long",
        "expected": ["KH0015", "CANON TL"]
    },
    {
        "id": 18,
        "question": "Từ ngày 01/10/2026 đến hết ngày 20/10/2026, mã QC7-5146-000 có số lượng giao bù NG là bao nhiêu, số lượng hàng NG đã nhận lại là bao nhiêu, và còn bao nhiêu chưa giao bù hoặc chưa nhận về? Phân biệt rõ giao bù NG với giao bù hàng thiếu; nếu ERP không lưu đủ căn cứ để phân biệt thì nêu rõ.",
        "topic": "Đối soát giao bù NG",
        "expected": ["bù", "NG", "QC7-5146-000"]
    }
]

def execute_tool_call(fn_name, fn_args):
    sys.path.insert(0, ".")
    from functions.htmp_postgres_query import Tools
    tools = Tools()
    
    # Check if method exists on Tools
    fn = getattr(tools, fn_name, None)
    if fn:
        try:
            return fn(**fn_args, __user__={"id": "1"})
        except Exception as e:
            return f"Error executing {fn_name}: {e}"
            
    # Fallback to ERPNativeTools
    from erp_ai.native_tools import ERPNativeTools
    native = ERPNativeTools()
    fn_native = getattr(native, fn_name, None)
    if fn_native:
        try:
            return fn_native(**fn_args)
        except Exception as e:
            return f"Error executing native {fn_name}: {e}"
            
    return f"Tool {fn_name} not found"

def run_all_tests():
    print("=" * 80)
    print(f"RUNNING TEST ON ALL {len(QUESTIONS)} USER QUESTIONS VIA OPEN WEBUI")
    print("=" * 80)

    results = []

    for item in QUESTIONS:
        q_id = item["id"]
        q_text = item["question"]
        topic = item["topic"]
        expected = item["expected"]

        print(f"\n[{q_id:02d}/18] [{topic}]")
        print(f"USER: {q_text}")

        # TURN 1
        messages = [{"role": "user", "content": q_text}]
        payload1 = {
            "model": "htmp-nhanh",
            "messages": messages,
            "stream": False
        }
        req1 = urllib.request.Request(
            f"{BASE_URL}/api/chat/completions",
            data=json.dumps(payload1).encode("utf-8"),
            headers=HEADERS
        )
        t0 = time.time()
        try:
            with urllib.request.urlopen(req1, timeout=60) as resp1:
                res1 = json.loads(resp1.read().decode("utf-8"))
        except Exception as e:
            print(f"  -> API Error on Turn 1: {e}")
            results.append({"id": q_id, "topic": topic, "status": "FAIL", "error": str(e)})
            continue

        choice1 = res1.get("choices", [{}])[0]
        msg1 = choice1.get("message", {})
        tool_calls = msg1.get("tool_calls", [])
        tool_used = ""
        final_answer = ""

        if tool_calls:
            messages.append(msg1)
            for tc in tool_calls:
                fn_name = tc.get("function", {}).get("name", "")
                tool_used = fn_name
                fn_args_str = tc.get("function", {}).get("arguments", "{}")
                try:
                    fn_args = json.loads(fn_args_str)
                except Exception:
                    fn_args = {}
                
                print(f"  -> Tool called: {fn_name}({fn_args})")
                tool_output = execute_tool_call(fn_name, fn_args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", ""),
                    "name": fn_name,
                    "content": str(tool_output)
                })

            # TURN 2
            payload2 = {
                "model": "htmp-nhanh",
                "messages": messages,
                "stream": False
            }
            req2 = urllib.request.Request(
                f"{BASE_URL}/api/chat/completions",
                data=json.dumps(payload2).encode("utf-8"),
                headers=HEADERS
            )
            try:
                with urllib.request.urlopen(req2, timeout=60) as resp2:
                    res2 = json.loads(resp2.read().decode("utf-8"))
                    final_answer = res2.get("choices", [{}])[0].get("message", {}).get("content", "")
            except Exception as e:
                print(f"  -> API Error on Turn 2: {e}")
                final_answer = f"Error on Turn 2: {e}"
        else:
            final_answer = msg1.get("content", "")
            print("  -> Direct answer without tools")

        elapsed = time.time() - t0
        print(f"  Elapsed: {elapsed:.2f}s | Tool: {tool_used}")
        print(f"  Answer preview:\n{final_answer[:300]}...\n")

        # Verification of keywords
        matched = [k for k in expected if k.lower() in final_answer.lower()]
        passed = len(matched) >= max(1, len(expected) // 2)

        results.append({
            "id": q_id,
            "topic": topic,
            "question": q_text,
            "tool_used": tool_used,
            "elapsed_seconds": round(elapsed, 2),
            "passed": passed,
            "matched_keywords": matched,
            "expected_keywords": expected,
            "final_answer": final_answer
        })

    # Summary
    print("=" * 80)
    print("SUMMARY OF 18 USER BENCHMARK QUESTIONS:")
    print("=" * 80)
    all_passed = all(r.get("passed", False) for r in results)
    for r in results:
        status_icon = "✅ PASS" if r.get("passed") else "⚠️ CHECK"
        print(f"  Q{r['id']:02d}: {status_icon} [{r['topic']}] ({r.get('elapsed_seconds')}s) Tool: {r.get('tool_used')}")
    print(f"\nOVERALL RESULT: {'100% PASSED' if all_passed else 'SOME QUESTIONS NEED REVIEW'}")

    # Persist JSON evidence
    out_dir = "docs/evidence/ERP-18-QUESTIONS-20261107"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/ket-qua-18-cau.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Saved full records to {out_dir}/ket-qua-18-cau.json")

if __name__ == "__main__":
    run_all_tests()

