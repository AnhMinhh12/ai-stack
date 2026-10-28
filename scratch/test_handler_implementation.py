import re
import json
import unicodedata
from datetime import date, datetime
import psycopg
from psycopg.rows import dict_row

def normalize_text(value: str) -> str:
    folded = unicodedata.normalize("NFD", value or "")
    folded = "".join(char for char in folded if unicodedata.category(char) != "Mn")
    folded = folded.replace("đ", "d").replace("Đ", "d").lower()
    return re.sub(r"[^a-z0-9]+", " ", folded).strip()

def carton_packing_register(question: str):
    normalized = normalize_text(question)
    keywords = ("bang ke dong thung", "bang ke dong goi", "dong goi dong thung", "dong thung", "dong goi", "thung thanh pham", "so thung", "packing list")
    if not any(kw in normalized for kw in keywords):
        return None
    
    code_match = re.search(r"\b((?=[a-z0-9/-]*\d)[a-z0-9]+(?:[-/][a-z0-9]+)*)\b", question, re.I)
    material_code = code_match.group(1).upper() if code_match else None
    
    conn = psycopg.connect(
        host='10.0.6.2',
        port=5410,
        dbname='3SERP_HTMP_DATA',
        user='read_htmp',
        password='P@ss@Htmp@W0rd!2025',
        connect_timeout=3
    )
    cur = conn.cursor(row_factory=dict_row)
    cur.execute("SET statement_timeout = '15s'")
    
    where_clauses = ["create_date >= CURRENT_DATE - 1"]
    params = []
    if material_code:
        where_clauses.append("(upper(trim(product_code)) = %s OR upper(trim(mes_scheduling_code)) = %s)")
        params.extend([material_code, material_code])
        
    query = f"""
        SELECT 
            to_char(create_date, 'YYYY-MM-DD') as ngay_sx_thuc_te,
            station_code as ma_day_chuyen,
            mes_scheduling_code as so_wo,
            product_code as ma_san_pham,
            product_name as ten_san_pham,
            sum(quantity) as so_luong_thuc_te,
            count(serial_tem_sp) as so_luong_theo_thung,
            serial_tem_thung,
            max(create_date || ' ' || create_time) as thoi_gian_dong_thung,
            coalesce(phan_loai, 0) as phan_loai
        FROM public.mes_oi_dong_thung
        WHERE {' AND '.join(where_clauses)}
        GROUP BY 
            create_date,
            station_code,
            mes_scheduling_code,
            product_code,
            product_name,
            serial_tem_thung,
            phan_loai
        ORDER BY create_date DESC, max(create_time) DESC
        LIMIT 20;
    """
    cur.execute(query, params)
    rows = cur.fetchall()
    conn.close()
    
    return json.dumps({
        "source": "public.mes_oi_dong_thung (Bảng kê đóng gói, đóng thùng)",
        "lookup": {"ma_vt": material_code},
        "row_count": len(rows),
        "rows": rows
    }, ensure_ascii=False, default=str)

print("Test carton_packing_register:")
res = carton_packing_register("Tra cứu bảng kê đóng thùng gần đây")
parsed = json.loads(res)
print(f"Row count: {parsed['row_count']}")
for r in parsed['rows'][:3]:
    print(r)
