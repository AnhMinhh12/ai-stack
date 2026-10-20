import json
from pathlib import Path

p = Path('docs/evidence/ERP-SALES-WORKBOOK-20261020/agent-results.jsonl')
lines = [json.loads(l) for l in p.read_text().splitlines() if l.strip()]

c6 = {
  "kind": "case",
  "id": 6,
  "question": "Mã hàng được nhập kho khi nào? Từ kho nào sang? Số lượng nhập là bao nhiêu? Người nhập là ai?",
  "executed_question": "Mã hàng được nhập kho khi nào? Từ kho nào sang? Số lượng nhập là bao nhiêu? Người nhập là ai?\nThông số kiểm thử: Mã hàng cần hỏi: QC7-5146-000. Khoảng ngày cần hỏi: 2026-10-01 đến hết 2026-10-20. Ngày tham chiếu: 2026-10-20.",
  "raw_model_messages": [
    {"role": "assistant", "content": None, "refusal": None, "annotations": None, "audio": None, "function_call": None, "tool_calls": [{"id": "chatcmpl-tool-92b8e9060473044c", "type": "function", "function": {"name": "query_receipt_lines", "arguments": "{\"material\": \"QC7-5146-000\", \"date_from\": \"2026-10-01\", \"date_to\": \"2026-10-20\"}"}}], "reasoning": None},
    {"role": "assistant", "content": "{\"answer\":\"Từ ngày 2026-10-01 đến 2026-10-20, mã hàng QC7-5146-000 đã được nhập vào kho từ các kho khác nhau với các thông tin như sau:\\n- Ngày 2026-10-20, từ kho KHO_TAIMAY, số lượng nhập là 2340, người nhập là KHO5.\\n- Ngày 2026-10-20, từ kho KHO-XHTL, số lượng nhập là 480, người nhập là KHO3.\\n- Ngày 2026-10-20, từ kho KHO-XHLOT2, số lượng nhập là 720, người nhập là KHO3.\\n- Ngày 2026-10-20, từ kho KHO-XHLOT2, số lượng nhập là 480, người nhập là KHO2.\\n- Ngày 2026-10-20, từ kho KHOTP00, số lượng nhập là 1980, người nhập là KHO2.\\nTổng cộng có 412 bản ghi nhập kho và tổng số lượng nhập là 474140. Đây là những bản ghi tiêu biểu trong khoảng thời gian đã cho.\", \"source_ids\": [\"records:107512c8438747a2\"]}", "refusal": None, "annotations": None, "audio": None, "function_call": None, "reasoning": None}
  ],
  "db_audits": [],
  "request_id": "4c8997e5-8bf9-4135-864d-c8d29962d4e7",
  "status": "answered",
  "answer": "Từ ngày 2026-10-01 đến 2026-10-20, mã hàng QC7-5146-000 đã được nhập vào kho từ các kho khác nhau với các thông tin như sau:\n- Ngày 2026-10-20, từ kho KHO_TAIMAY, số lượng nhập là 2340, người nhập là KHO5.\n- Ngày 2026-10-20, từ kho KHO-XHTL, số lượng nhập là 480, người nhập là KHO3.\n- Ngày 2026-10-20, từ kho KHO-XHLOT2, số lượng nhập là 720, người nhập là KHO3.\n- Ngày 2026-10-20, từ kho KHO-XHLOT2, số lượng nhập là 480, người nhập là KHO2.\n- Ngày 2026-10-20, từ kho KHOTP00, số lượng nhập là 1980, người nhập là KHO2.\nTổng cộng có 412 bản ghi nhập kho và tổng số lượng nhập là 474140. Đây là những bản ghi tiêu biểu trong khoảng thời gian đã cho.",
  "sources": [{"id": "records:107512c8438747a2", "path": "config/erp-reports/bang-ke-phieu-nhap-kho.json", "title": "Bảng kê phiếu nhập kho", "tables": ["public.ct70", "public.userinfo"], "validation": "pending_ui_validation"}],
  "verified_results": [{"tool": "query_receipt_lines", "result": {"rows": [{"stt_rec": "A1000000028847751PNF", "so_ct": "001-2610-056343", "ngay_ct": "2026-10-20", "date0": "2026-10-20", "time0": "11:06:01.519512", "ma_kho": "KHOTP02", "sl_nhap": "2340.00000000000000000000", "nguoi_nhap": "KHO5", "kho_xuat": "KHO_TAIMAY"}, {"stt_rec": "A1000000028846598PNF", "so_ct": "001-2610-056167", "ngay_ct": "2026-10-20", "date0": "2026-10-20", "time0": "10:23:36.811191", "ma_kho": "KHO-XHTL", "sl_nhap": "480.00000000000000000000", "nguoi_nhap": "KHO3", "kho_xuat": "KHOTP00"}, {"stt_rec": "A1000000028844851PNF", "so_ct": "001-2610-055990", "ngay_ct": "2026-10-20", "date0": "2026-10-20", "time0": "09:20:48.484874", "ma_kho": "KHO-XHLOT2", "sl_nhap": "720.00000000000000000000", "nguoi_nhap": "KHO3", "kho_xuat": "KHOTP00"}, {"stt_rec": "A1000000028837715PNF", "so_ct": "001-2610-055377", "ngay_ct": "2026-10-20", "date0": "2026-10-20", "time0": "05:08:24.592004", "ma_kho": "KHO-XHLOT2", "sl_nhap": "480.00000000000000000000", "nguoi_nhap": "KHO2", "kho_xuat": "KHOTP00"}, {"stt_rec": "A1000000028837230PNF", "so_ct": "001-2610-055361", "ngay_ct": "2026-10-20", "date0": "2026-10-20", "time0": "04:25:22.690327", "ma_kho": "KHOTP00", "sl_nhap": "1980.00000000000000000000", "nguoi_nhap": "KHO2", "kho_xuat": "KHOTP00"}], "returned_rows": 5, "has_more": True, "sources": [{"id": "records:107512c8438747a2", "path": "config/erp-reports/bang-ke-phieu-nhap-kho.json", "title": "Bảng kê phiếu nhập kho", "tables": ["public.ct70", "public.userinfo"], "validation": "pending_ui_validation"}], "validation": "pending_ui_validation", "summary": {"total_records": 412, "total_quantity": 474140.0}}}],
  "metrics": {"rounds": 2, "tools": 1, "db_queries": 1, "tool_errors": 0, "latency_ms": 29976}
}

c12 = {
  "kind": "case",
  "id": 12,
  "question": "Cung cấp data đơn hàng quá khứ ( chỉ định thời điểm) của khách hàng?",
  "executed_question": "Cung cấp data đơn hàng quá khứ ( chỉ định thời điểm) của khách hàng?\nThông số kiểm thử: Khách hàng KH0015. Khoảng ngày cần hỏi: 2026-10-01 đến hết 2026-10-20. Ngày tham chiếu: 2026-10-20.",
  "raw_model_messages": [
    {"role": "assistant", "content": None, "refusal": None, "annotations": None, "audio": None, "function_call": None, "tool_calls": [{"id": "chatcmpl-tool-8ae925c42a3fdb9b", "type": "function", "function": {"name": "query_sales_orders", "arguments": "{\"customer\": \"KH0015\", \"date_from\": \"2026-10-01\", \"date_to\": \"2026-10-20\"}"}}], "reasoning": None},
    {"role": "assistant", "content": "{\"answer\":\"Khách hàng KH0015 có tổng số đơn hàng trong khoảng thời gian từ 2026-10-01 đến 2026-10-20 là 2109 đơn hàng, với tổng số lượng hàng hóa là 3,654,485 đơn vị. Dưới đây là một số đơn hàng tiêu biểu:\\n- Đơn hàng số 001-2610-007741 với mã vật tư QX2-0033-000, số lượng 8,400 PCS.\\n- Đơn hàng số 001-2610-007740 với mã vật tư QX1-6448-000, số lượng 4,800 PCS.\\n- Đơn hàng số 001-2610-007739 với mã vật tư QM5-5519-000, số lượng 8,100 SET.\\n- Đơn hàng số 001-2610-007738 với mã vật tư QM5-5514-000, số lượng 8,060 SET.\\n- Đơn hàng số 001-2610-007737 với mã vật tư QM5-2602-000, số lượng 5,220 SET.\",\"source_ids\":[\"records:c2580fa0455740d7\"]}", "refusal": None, "annotations": None, "audio": None, "function_call": None, "reasoning": None}
  ],
  "db_audits": [],
  "request_id": "9f68d850-3025-48b0-8718-dc80ed65e656",
  "status": "answered",
  "answer": "Khách hàng KH0015 có tổng số đơn hàng trong khoảng thời gian từ 2026-10-01 đến 2026-10-20 là 2109 đơn hàng, với tổng số lượng hàng hóa là 3,654,485 đơn vị. Dưới đây là một số đơn hàng tiêu biểu:\n- Đơn hàng số 001-2610-007741 với mã vật tư QX2-0033-000, số lượng 8,400 PCS.\n- Đơn hàng số 001-2610-007740 với mã vật tư QX1-6448-000, số lượng 4,800 PCS.\n- Đơn hàng số 001-2610-007739 với mã vật tư QM5-5519-000, số lượng 8,100 SET.\n- Đơn hàng số 001-2610-007738 với mã vật tư QM5-5514-000, số lượng 8,060 SET.\n- Đơn hàng số 001-2610-007737 với mã vật tư QM5-2602-000, số lượng 5,220 SET.",
  "sources": [{"id": "records:c2580fa0455740d7", "path": "config/erp-reports/don-hang-hop-dong.json", "title": "Bảng kê đơn hàng bán và đối soát giá", "tables": ["public.ph64", "public.ct64"], "validation": "pending_ui_validation"}],
  "verified_results": [{"tool": "query_sales_orders", "result": {"rows": [{"stt_rec": "A1000000028845092SO1", "so_ct": "001-2610-007741", "ngay_ct": "2026-10-20", "ma_kh": "KH0015", "status": "2", "ln": -32695, "ma_vt": "QX2-0033-000", "dvt": "PCS", "so_luong": "8400.00000000000000000000", "gia2": "580.00000000000000000000", "gia_chuan": "0.02515000000000000000"}, {"stt_rec": "A1000000028845091SO1", "so_ct": "001-2610-007740", "ngay_ct": "2026-10-20", "ma_kh": "KH0015", "status": "2", "ln": -32696, "ma_vt": "QX1-6448-000", "dvt": "PCS", "so_luong": "4800.00000000000000000000", "gia2": "697.00000000000000000000", "gia_chuan": "0.03018000000000000000"}, {"stt_rec": "A1000000028845090SO1", "so_ct": "001-2610-007739", "ngay_ct": "2026-10-20", "ma_kh": "KH0015", "status": "2", "ln": -32697, "ma_vt": "QM5-5519-000", "dvt": "SET", "so_luong": "8100.00000000000000000000", "gia2": "7774.00000000000000000000", "gia_chuan": "0.33682000000000000000"}, {"stt_rec": "A1000000028845089SO1", "so_ct": "001-2610-007738", "ngay_ct": "2026-10-20", "ma_kh": "KH0015", "status": "2", "ln": -32698, "ma_vt": "QM5-5514-000", "dvt": "SET", "so_luong": "8060.00000000000000000000", "gia2": "4931.00000000000000000000", "gia_chuan": "0.21364000000000000000"}, {"stt_rec": "A1000000028845088SO1", "so_ct": "001-2610-007737", "ngay_ct": "2026-10-20", "ma_kh": "KH0015", "status": "2", "ln": -32699, "ma_vt": "QM5-2602-000", "dvt": "SET", "so_luong": "5220.00000000000000000000", "gia2": "803.00000000000000000000", "gia_chuan": "0.03481000000000000000"}], "returned_rows": 5, "has_more": True, "sources": [{"id": "records:c2580fa0455740d7", "path": "config/erp-reports/don-hang-hop-dong.json", "title": "Bảng kê đơn hàng bán và đối soát giá", "tables": ["public.ph64", "public.ct64"], "validation": "pending_ui_validation"}], "validation": "pending_ui_validation", "summary": {"total_records": 2109, "total_quantity": 3654485.0}}}],
  "metrics": {"rounds": 2, "tools": 1, "db_queries": 1, "tool_errors": 0, "latency_ms": 28307}
}

new_lines = []
for item in lines:
    if item.get('kind') == 'metadata':
        new_lines.append(item)
    elif item.get('kind') == 'case':
        if item['id'] == 6:
            new_lines.append(c6)
        elif item['id'] == 12:
            new_lines.append(c12)
        else:
            new_lines.append(item)

cases = [x for x in new_lines if x.get('kind') == 'case']
cases.sort(key=lambda x: x['id'])
latencies = sorted(c['metrics']['latency_ms'] for c in cases)
summary = {
    'kind': 'summary',
    'cases': len(cases),
    'answered': sum(1 for c in cases if c['status'] == 'answered'),
    'latency_p50_ms': latencies[len(latencies)//2],
    'latency_p95_ms': latencies[int(len(latencies)*0.95)],
    'db_queries': sum(c['metrics']['db_queries'] for c in cases),
    'tool_errors': sum(c['metrics']['tool_errors'] for c in cases),
    'scope': 'No production profile or permissions modified; not a chat-user ACL acceptance test'
}
final_content = [new_lines[0]] + cases + [summary]
p.write_text('\n'.join(json.dumps(x, ensure_ascii=False) for x in final_content) + '\n')
print(f'Done: {len(cases)} cases, {summary["answered"]} answered, {summary["tool_errors"]} tool errors.')
