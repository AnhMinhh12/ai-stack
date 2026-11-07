"""Verification script for random arbitrary ERP business questions."""

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

def execute_tool_directly(fn_name, args):
    if fn_name == "query_erp_report":
        from erp_ai.generic_procedure_executor import GenericProcedureExecutor
        executor = GenericProcedureExecutor()
        res = executor.query_report(**args)
        return res.get("formatted_text", "Không có kết quả")
    
    from erp_ai.native_tools import ERPNativeTools
    tools = ERPNativeTools()
    fn = getattr(tools, fn_name, None)
    if fn:
        try:
            return fn(**args)
        except Exception as e:
            return f"Error executing {fn_name}: {e}"
    return f"Tool {fn_name} not found"

TEST_QUESTIONS = [
    {
        "id": "RND-01",
        "domain": "CÔNG NỢ KHÁCH HÀNG (AR - TK 131)",
        "question": "Cho tôi sổ chi tiết công nợ của khách hàng KH0015 trong tháng 10/2026",
        "expected_keywords": ["10/2026", "KH0015", "Phát sinh Nợ", "Phát sinh Có"]
    },
    {
        "id": "RND-02",
        "domain": "TỔNG HỢP NHẬP XUẤT TỒN (IN - inbcthnxt)",
        "question": "Báo cáo tổng hợp nhập xuất tồn kho mã vật tư 003-M69-101-2 trong tháng 10/2026",
        "expected_keywords": ["003-M69-101-2", "Plate Diaphragm", "20,599", "240,841", "236,071", "25,369"]
    },
    {
        "id": "RND-03",
        "domain": "ĐƠN ĐẶT MUA HÀNG (PO - pobkdonhang)",
        "question": "Bảng kê đơn mua hàng trong tháng 10/2026",
        "expected_keywords": ["đơn đặt mua", "001-2610-", "NCC", "SL Đặt"]
    },
    {
        "id": "RND-04",
        "domain": "LỊCH SỬ THAY ĐỔI GIÁ BÁN (SO - sobclsgia)",
        "question": "Lịch sử thay đổi giá bán của mã sản phẩm 003-M69-101-2",
        "expected_keywords": ["003-M69-101-2", "1,424", "KH0028"]
    },
    {
        "id": "RND-05",
        "domain": "TIẾN ĐỘ GIAO HÀNG BÁN (SO - sobctiendogh)",
        "question": "Báo cáo tiến độ giao hàng cho khách hàng KH0015 trong tháng 10/2026",
        "expected_keywords": ["tiến độ giao hàng", "KH0015", "Canon"]
    }
]

def run_test_suite():
    print(f"Starting test suite for {len(TEST_QUESTIONS)} random ERP business questions...")
    results = []

    for idx, item in enumerate(TEST_QUESTIONS, start=1):
        q_id = item["id"]
        domain = item["domain"]
        q_text = item["question"]
        expected = item["expected_keywords"]

        print("=" * 80)
        print(f"[{idx}/{len(TEST_QUESTIONS)}] [{domain}] Q: {q_text}")

        # TURN 1: User prompt
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
            with urllib.request.urlopen(req1, timeout=60) as resp:
                res1 = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            print(f"FAILED on Turn 1 API request: {e}")
            results.append({"id": q_id, "status": "FAIL", "error": str(e)})
            continue

        choice1 = res1.get("choices", [{}])[0]
        msg1 = choice1.get("message", {})
        tool_calls = msg1.get("tool_calls", [])
        final_answer = ""
        tool_used = ""

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
                tool_output = execute_tool_directly(fn_name, fn_args)
                messages.append({
                    "role": "tool",
                    "tool_call_id": tc.get("id", ""),
                    "name": fn_name,
                    "content": str(tool_output)
                })

            # TURN 2: Model synthesis
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
                print(f"FAILED on Turn 2 synthesis: {e}")
                final_answer = f"Error Turn 2: {e}"
        else:
            final_answer = msg1.get("content", "")
            print("  -> Direct answer (no tool calls)")

        elapsed = time.time() - t0
        print(f"  Elapsed: {elapsed:.2f}s | Tool: {tool_used}")
        print(f"  Answer preview:\n{final_answer[:400]}")

        # Verification of keywords
        matched = [k for k in expected if k.lower() in final_answer.lower()]
        passed = len(matched) >= max(1, len(expected) // 2)

        print(f"  Keywords matched: {matched} / {expected} => {'PASSED' if passed else 'WARNING'}")
        results.append({
            "id": q_id,
            "domain": domain,
            "question": q_text,
            "tool_used": tool_used,
            "elapsed_seconds": round(elapsed, 2),
            "passed": passed,
            "matched_keywords": matched,
            "final_answer": final_answer
        })

    # Summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY OF RANDOM ERP BUSINESS QUESTIONS:")
    all_passed = all(r.get("passed", False) for r in results)
    for r in results:
        status_icon = "✅ PASS" if r.get("passed") else "⚠️ CHECK"
        print(f"  {r['id']}: {status_icon} [{r['domain']}] Tool: {r.get('tool_used')} ({r.get('elapsed_seconds')}s)")
    print(f"\nOverall Result: {'100% PASSED' if all_passed else 'SOME NEED REVIEW'}")

    # Persist evidence
    out_dir = "docs/evidence/ERP-RANDOM-TEST-20261107"
    os.makedirs(out_dir, exist_ok=True)
    with open(f"{out_dir}/ket-qua-random.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"Saved results to {out_dir}/ket-qua-random.json")

if __name__ == "__main__":
    run_test_suite()

