import json
import time
import os
import sys
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor, as_completed
import statistics

sys.path.insert(0, '/home/admin/ai-stack')
sys.path.insert(0, '/home/admin/ai-stack/functions')
from htmp_postgres_query import Tools

BASE_URL = "http://127.0.0.1:80"

# 20 distinct real operational questions across departments
BENCHMARK_QUESTIONS = [
    {"dept": "Bán hàng (Sales)", "q": "Cho tôi biết sản lượng và doanh thu xuất bán của mã QC7-5146-000 từ ngày 01/10/2026 đến 20/10/2026"},
    {"dept": "Kinh doanh (Sales)", "q": "Top 5 khách hàng đặt hàng lớn nhất trong tháng 10/2026"},
    {"dept": "Kế toán (Accounting)", "q": "Đối soát đơn đặt hàng SO và thực tế xuất bán HDA của mã QC7-5146-000 trong tháng 10/2026"},
    {"dept": "Kho vận (Logistics)", "q": "Kiểm tra trạng thái các lệnh giao hàng TO2 của mã QC7-5146-000"},
    {"dept": "Kho vận (Logistics)", "q": "Lô xuất hàng gần nhất của mã QC7-5146-000 là chứng từ nào?"},
    {"dept": "Kỹ thuật (Engineering)", "q": "Mã sản phẩm QC7-5146-000 sử dụng loại hạt nhựa nào và định mức bao nhiêu?"},
    {"dept": "Kỹ thuật (BOM)", "q": "Cấu trúc BOM sản xuất của mã 009-M66-198 gồm những linh kiện và hạt nhựa gì?"},
    {"dept": "Kinh doanh (Pricing)", "q": "Bảng giá và MOQ hiện hành của mã QC7-5146-000 là bao nhiêu?"},
    {"dept": "Kiểm soát (Internal Audit)", "q": "Hệ thống có đơn hàng nào bị thiếu giá niêm yết hoặc giá chuẩn bằng 0 không?"},
    {"dept": "Kho vận (Inventory)", "q": "Mã hàng QC7-5146-000 hiện đang tồn ở những kho nào và số lượng bao nhiêu?"},
    {"dept": "Kho vận (Inventory)", "q": "Lịch sử nhập kho của mã QC7-5146-000 từ 01/10/2026 đến 20/10/2026"},
    {"dept": "MES Đóng gói (Packaging)", "q": "Quy cách đóng gói của mã QC7-5146-000 là gì và tồn kho quy đổi ra được bao nhiêu thùng?"},
    {"dept": "MES Pallet (Warehouse)", "q": "Tra cứu danh sách pallet đóng thùng thành phẩm mới nhất ngày 29/10/2026"},
    {"dept": "Xưởng SX (Workshops)", "q": "Tình hình xuất nguyên vật liệu cho các xưởng sản xuất trong tháng 10/2026"},
    {"dept": "Xưởng SX (Workshops)", "q": "Tình hình nhập kho thành phẩm hoàn thành từ xưởng sản xuất trong tháng 10/2026"},
    {"dept": "Khuôn mẫu (Tooling)", "q": "Khuôn 25HI83 hiện tại đã chạy được bao nhiêu shot?"},
    {"dept": "Khuôn mẫu (Tooling)", "q": "Danh sách các khuôn có số shot chạy thực tế cao nhất hệ thống"},
    {"dept": "Khuôn mẫu (Tooling)", "q": "Mã hàng QC7-5146-000 đang có tồn kho theo các mã Die nào?"},
    {"dept": "Quản lý Chất lượng (OQC)", "q": "Trạng thái kiểm tra QC của các tem hàng mã QC7-5146-000 thế nào?"},
    {"dept": "Quản lý Chất lượng (IQC)", "q": "Chi tiết kết quả kiểm tra chất lượng IQC của nhà cung cấp NCC0619 trong tháng 10/2026"}
]

def run_single_user_session(user_info, question_info, worker_id):
    user_id = user_info["id"]
    user_name = user_info["name"]
    user_email = user_info["email"]
    token = user_info["token"]
    dept = question_info["dept"]
    question = question_info["q"]
    
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }
    
    t_start = time.time()
    t_turn1_start = t_start
    status = "FAILED"
    error_msg = ""
    ai_answer = ""
    turn1_time = 0
    tool_time = 0
    turn2_time = 0
    
    try:
        # Step 1: Initial Turn (User asks question)
        payload1 = {
            "model": "htmp-nhanh",
            "messages": [{"role": "user", "content": question}],
            "stream": False
        }
        req1 = urllib.request.Request(
            f"{BASE_URL}/api/chat/completions",
            data=json.dumps(payload1).encode("utf-8"),
            headers=headers
        )
        with urllib.request.urlopen(req1, timeout=180) as resp1:
            res1 = json.loads(resp1.read().decode("utf-8"))
        
        turn1_time = time.time() - t_turn1_start
        assistant_turn1 = res1["choices"][0]["message"]
        tool_calls = assistant_turn1.get("tool_calls")
        
        if tool_calls:
            tc = tool_calls[0]
            tc_name = tc.get("function", {}).get("name", "")
            tc_args_str = tc.get("function", {}).get("arguments", "{}")
            tc_args = json.loads(tc_args_str) if tc_args_str else {}
            
            # Step 2: Tool Execution (Query Live ERP DB)
            t_tool_start = time.time()
            tools_instance = Tools()
            tool_output = tools_instance.ask_erp(**tc_args)
            tool_time = time.time() - t_tool_start
            
            # Step 3: Second Turn (Pass tool result to synthesize final answer)
            t_turn2_start = time.time()
            payload2 = {
                "model": "htmp-nhanh",
                "messages": [
                    {"role": "user", "content": question},
                    assistant_turn1,
                    {
                        "role": "tool",
                        "tool_call_id": tc["id"],
                        "content": tool_output
                    }
                ],
                "stream": False
            }
            req2 = urllib.request.Request(
                f"{BASE_URL}/api/chat/completions",
                data=json.dumps(payload2).encode("utf-8"),
                headers=headers
            )
            with urllib.request.urlopen(req2, timeout=180) as resp2:
                res2 = json.loads(resp2.read().decode("utf-8"))
            
            turn2_time = time.time() - t_turn2_start
            ai_answer = res2["choices"][0]["message"].get("content", "").strip()
            status = "SUCCESS" if ai_answer else "EMPTY_RESPONSE"
        else:
            # Model directly answered (e.g. general knowledge)
            ai_answer = assistant_turn1.get("content", "").strip()
            status = "SUCCESS" if ai_answer else "EMPTY_RESPONSE"
            
    except Exception as e:
        status = "ERROR"
        error_msg = str(e)
        ai_answer = f"Exception: {e}"
    
    t_end = time.time()
    total_latency = t_end - t_start
    
    return {
        "worker_id": worker_id,
        "user_id": user_id,
        "user_name": user_name,
        "user_email": user_email,
        "department": dept,
        "question": question,
        "status": status,
        "total_latency_s": round(total_latency, 2),
        "turn1_latency_s": round(turn1_time, 2),
        "tool_latency_s": round(tool_time, 2),
        "turn2_latency_s": round(turn2_time, 2),
        "ai_answer_preview": ai_answer[:200].replace("\n", " "),
        "error_msg": error_msg
    }

def main():
    tokens_file = "/home/admin/ai-stack/scratch/20_user_tokens.json"
    with open(tokens_file, "r") as f:
        users = json.load(f)
    
    total_users = min(len(users), len(BENCHMARK_QUESTIONS))
    print(f"=== BẮT ĐẦU TEST TẢI HIỆU NĂNG: {total_users} TÀI KHOẢN ĐỒNG THỜI ===")
    print(f"Mô hình: HTMP ERP (Qwen 2.5 14B @ vLLM)")
    print(f"Hệ quản trị CSDL: PostgreSQL 3SERP_HTMP_DATA (10.0.6.2:5410)")
    print(f"Cổng API: Open WebUI Gateway (:80)")
    print("----------------------------------------------------------------------")
    
    start_wall_time = time.time()
    results = []
    
    with ThreadPoolExecutor(max_workers=total_users) as executor:
        futures = {
            executor.submit(run_single_user_session, users[i], BENCHMARK_QUESTIONS[i], i + 1): i
            for i in range(total_users)
        }
        
        for future in as_completed(futures):
            res = future.result()
            results.append(res)
            print(f"[{res['worker_id']:02d}/20] {res['user_name']} ({res['department']}) -> {res['status']} ({res['total_latency_s']}s)")
    
    end_wall_time = time.time()
    total_duration = end_wall_time - start_wall_time
    
    # Sort by worker_id for clean presentation
    results.sort(key=lambda x: x["worker_id"])
    
    # Metrics
    success_count = sum(1 for r in results if r["status"] == "SUCCESS")
    latencies = [r["total_latency_s"] for r in results if r["status"] == "SUCCESS"]
    
    min_lat = min(latencies) if latencies else 0
    max_lat = max(latencies) if latencies else 0
    mean_lat = statistics.mean(latencies) if latencies else 0
    median_lat = statistics.median(latencies) if latencies else 0
    p90_lat = statistics.quantiles(latencies, n=10)[8] if len(latencies) >= 10 else max_lat
    p95_lat = statistics.quantiles(latencies, n=20)[18] if len(latencies) >= 20 else max_lat
    
    summary = {
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_concurrent_users": total_users,
        "success_count": success_count,
        "success_rate_pct": round((success_count / total_users) * 100, 1),
        "total_wall_clock_duration_s": round(total_duration, 2),
        "throughput_requests_per_sec": round((total_users * 2) / total_duration, 2), # 2 LLM turns per user
        "latency_metrics": {
            "min_s": min_lat,
            "max_s": max_lat,
            "mean_s": round(mean_lat, 2),
            "median_p50_s": round(median_lat, 2),
            "p90_s": round(p90_lat, 2),
            "p95_s": round(p95_lat, 2)
        },
        "details": results
    }
    
    out_file = "/home/admin/ai-stack/scratch/ket_qua_test_20_tai_khoan_dong_thoi.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, ensure_ascii=False)
        
    print("----------------------------------------------------------------------")
    print(f"=== KẾT QUẢ TỔNG QUÁT ===")
    print(f"- Thành công: {success_count}/{total_users} ({summary['success_rate_pct']}%)")
    print(f"- Tổng thời gian hoàn tất 20 yêu cầu: {summary['total_wall_clock_duration_s']} giây")
    print(f"- Thông lượng (Throughput): {summary['throughput_requests_per_sec']} req/s")
    print(f"- Độ trễ trung bình (Mean Latency): {summary['latency_metrics']['mean_s']} giây")
    print(f"- Độ trễ P50 (Trung vị): {summary['latency_metrics']['median_p50_s']} giây")
    print(f"- Độ trễ P90: {summary['latency_metrics']['p90_s']} giây")
    print(f"- Độ trễ P95: {summary['latency_metrics']['p95_s']} giây")
    print(f"- Độ trễ nhỏ nhất: {summary['latency_metrics']['min_s']}s | Lớn nhất: {summary['latency_metrics']['max_s']}s")
    print(f"Đã lưu kết quả chi tiết vào: {out_file}")

if __name__ == "__main__":
    main()
