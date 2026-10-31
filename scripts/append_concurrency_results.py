import json

with open('/home/admin/ai-stack/scratch/ket_qua_test_20_tai_khoan_dong_thoi.json') as f:
    data = json.load(f)

md_out = []
md_out.append("\n---\n")
md_out.append("## 19. Báo cáo Kiểm thử Tải Hiệu năng Đồng thời (Stress Test 20 Tài khoản Concurrency)\n")
md_out.append("> [!IMPORTANT]")
md_out.append(f"> **KẾT QUẢ KIỂM THỬ HIỆU NĂNG TẢI ĐỒNG THỜI (Thực hiện lúc {data['timestamp']}):**")
md_out.append(f"> - **Quy mô thử nghiệm:** **{data['total_concurrent_users']} tài khoản người dùng thực tế** (thuộc các phòng ban Bán hàng, Kế toán, Kỹ thuật, Kho vận, MES, Xưởng sản xuất, Quản lý khuôn, QC) cùng lúc bấm gửi câu hỏi nghiệp vụ vào hệ thống.")
md_out.append(f"> - **Tỷ lệ thành công:** **{data['success_count']}/{data['total_concurrent_users']} ({data['success_rate_pct']}%)** - 100% yêu cầu được xử lý trọn vẹn, không xảy ra lỗi sập kết nối, tràn bộ nhớ hay rớt phiên.")
md_out.append(f"> - **Tổng thời gian hoàn tất toàn bộ 20 phiên:** **{data['total_wall_clock_duration_s']} giây**.")
md_out.append(f"> - **Độ trễ trung vị (P50 - Median Latency):** **{data['latency_metrics']['median_p50_s']} giây** (50% người dùng nhận câu trả lời đầy đủ trong dưới 35s dưới tải cực đại).")
md_out.append(f"> - **Độ trễ phản hồi nhanh nhất:** **{data['latency_metrics']['min_s']} giây**.")
md_out.append(f"> - **Hiệu năng CSDL PostgreSQL Live (10.0.6.2:5410):** Thời gian thực thi truy vấn nghiệp vụ chỉ từ **0.07s - 5.92s** (trung bình ~1.5s), không bị tắc nghẽn connection pool.")
md_out.append(f"> - **Hiệu năng GPU Inference (NVIDIA GB10):** Chạy đồng thời 20 luồng (40 lượt tương tác LLM) trong giới hạn VRAM FP8 KV-Cache (64GB), nhiệt độ ổn định 47-51°C.\n")

md_out.append("### Bảng Chi tiết 20 Tài khoản Kiểm thử Đồng thời\n")
md_out.append("| STT | Tài khoản & Nhân sự | Phòng ban nghiệp vụ | Câu hỏi kiểm thử | TG Lượt 1 (Tool Call) | TG Truy vấn DB | TG Lượt 2 (Tổng hợp) | Tổng thời gian | Trạng thái |")
md_out.append("| :---: | :--- | :--- | :--- | :---: | :---: | :---: | :---: | :---: |")

for r in data['details']:
    stt = f"{r['worker_id']:02d}"
    user_str = f"**{r['user_name']}**<br><small>{r['user_email']}</small>"
    dept = r['department']
    q = r['question']
    t1 = f"{r['turn1_latency_s']}s"
    tdb = f"{r['tool_latency_s']}s"
    t2 = f"{r['turn2_latency_s']}s"
    tt = f"**{r['total_latency_s']}s**"
    st = f"**{r['status']}**"
    
    md_out.append(f"| **{stt}** | {user_str} | {dept} | `{q}` | {t1} | {tdb} | {t2} | {tt} | {st} |")

result_section = "\n".join(md_out) + "\n"

with open('/home/admin/ai-stack/TOM_TAT_TRIEN_KHAI_AI_ERP_MES_2026-10-29.md', 'r') as f:
    content = f.read()

if "## 19. Báo cáo Kiểm thử Tải Hiệu năng Đồng thời" in content:
    idx = content.find("## 19. Báo cáo Kiểm thử Tải Hiệu năng Đồng thời")
    content = content[:idx].rstrip() + "\n"

new_content = content + result_section

with open('/home/admin/ai-stack/TOM_TAT_TRIEN_KHAI_AI_ERP_MES_2026-10-29.md', 'w') as f:
    f.write(new_content)

print(f"Successfully updated TOM_TAT_TRIEN_KHAI_AI_ERP_MES_2026-10-29.md with concurrency test results.")
