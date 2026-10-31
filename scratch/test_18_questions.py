import sys
sys.path.insert(0, '.')
from functions.htmp_postgres_query import Tools

questions = [
    "1. Mã hàng QC7-5146-000 dùng loại nhựa gì? Cấu trúc sản phẩm của mã hàng này gồm những gì?",
    "2. MOQ báo giá hiện tại của mã QC7-5146-000 là bao nhiêu? Giá áp dụng hiện tại theo từng mức MOQ là bao nhiêu?",
    "3. Tính đến ngày 20/10/2026, lot gần nhất được xuất giao của mã QC7-5146-000 là lot nào? Ngày xuất và số lượng bao nhiêu?",
    "4. Từ ngày 01/10/2026 đến hết ngày 20/10/2026, tổng số lượng xuất bán và doanh thu của mã QC7-5146-000 là bao nhiêu?",
    "5. Mã hàng QC7-5146-000 được khai báo thuộc khách hàng nào?",
    "6. Từ ngày 01/10/2026 đến hết ngày 20/10/2026, mã QC7-5146-000 được nhập kho vào những ngày nào, từ kho nào sang kho nào, số lượng bao nhiêu và tài khoản nào tạo phiếu?",
    "7. So sánh DO và FCST hiện tại với bản trước của mã QC7-5146-000: số lượng tăng hay giảm bao nhiêu?",
    "8. Quy cách đóng gói của mã QC7-5146-000 gồm những thông tin gì? Có thể quy đổi tồn kho hiện tại theo quy cách đóng gói không?",
    "9. Khuôn K_QC5-2919-000-V1 đã chạy tổng cộng bao nhiêu shot cho mã QC7-5146-000? Với demand của khách KH0015, có đủ dữ liệu để dự kiến thời điểm khuôn hết tuổi thọ không?",
    "10. So sánh doanh thu mã QC7-5146-000 của khách KH0015 trong hai khoảng 01/09/2026–20/09/2026 và 01/10/2026–20/10/2026. Nêu số lượng và doanh thu từng kỳ.",
    "11. Mã QC7-5146-000 hiện có tồn kho thuộc những khuôn nào? Số lượng theo từng khuôn là bao nhiêu?",
    "12. Liệt kê dữ liệu đơn hàng bán của khách KH0015 từ ngày 01/10/2026 đến hết ngày 20/10/2026, gồm số đơn, ngày đặt, mã hàng, số lượng và trạng thái.",
    "13. Lệnh giao hàng 001-2610-001811 được ghi nhận hoàn thành khi nào? Cho biết trạng thái lệnh và căn cứ thời gian được dùng.",
    "14. Tồn kho hiện tại của mã QC7-5146-000 là bao nhiêu ở từng kho?",
    "15. Mã QC7-5146-000 hiện có lot thành phẩm nào ở trạng thái QC cần chú ý? Cho biết trạng thái QC đúng như dữ liệu ERP.",
    "16. Trong đơn hàng của khách KH0015 từ ngày 01/10/2026 đến hết ngày 20/10/2026, có mã hàng nào chưa có giá chuẩn được liên kết không?",
    "17. Công ty TNHH Canon Việt Nam- Chi nhánh Thăng Long có mã khách hàng nào trên ERP?",
    "18. Từ ngày 01/10/2026 đến hết ngày 20/10/2026, mã QC7-5146-000 có số lượng giao bù NG là bao nhiêu, số lượng hàng NG đã nhận lại là bao nhiêu, và còn bao nhiêu chưa giao bù hoặc chưa nhận về? Phân biệt rõ giao bù NG với giao bù hàng thiếu; nếu ERP không lưu đủ căn cứ để phân biệt thì nêu rõ."
]

t = Tools()
for i, q in enumerate(questions, 1):
    clean_q = q.split(". ", 1)[-1]
    res = t.ask_erp(clean_q)
    print(f"\n==========================================")
    print(f"QUESTION {i}: {clean_q}")
    if isinstance(res, tuple):
        answer_text, meta = res
        print(f"Type: TUPLE | Answer Text: {answer_text[:150]}")
        print(f"Meta summary: {meta.get('summary')}")
        print(f"Meta row_count: {meta.get('row_count')}")
        print(f"Meta result_displayed: {meta.get('result_displayed')}")
        if meta.get('rows'):
            print(f"Rows count: {len(meta.get('rows'))} | First row keys: {list(meta.get('rows')[0].keys())}")
    else:
        print(f"Type: STRING | Length: {len(str(res))}")
        print(f"Preview: {str(res)[:300]}")
