import os, sys
sys.path.insert(0, '/home/admin/ai-stack')
sys.path.insert(0, '/home/admin/ai-stack/functions')
os.environ["HTMP_DB_PORT"] = "5410"
from htmp_postgres_query import Tools
import json

question = 'Top 5 khách hàng đặt hàng lớn nhất trong tháng 10/2026'
normalized = Tools.normalize_text(question) if hasattr(Tools, 'normalize_text') else None
print('normalized:', normalized)
from htmp_postgres_query import extract_iso_date_range, connection_settings
d_from, d_to = extract_iso_date_range(question, default_from="2026-10-01", default_to="2026-10-31")
print('dates:', d_from, d_to)
import psycopg
from psycopg.rows import dict_row
with psycopg.connect(**connection_settings(), autocommit=False) as conn:
    with conn.cursor(row_factory=dict_row) as cursor:
        cursor.execute("SET TRANSACTION READ ONLY")
        cursor.execute("SELECT set_config('statement_timeout', %s, true)", ('15000',))
        sql = """
            SELECT 
                h.ma_kh,
                coalesce(k.ten_kh, h.ten_kh, h.ma_kh) AS ten_kh,
                count(DISTINCT h.so_ct) AS so_don_hang,
                sum(h.t_so_luong) AS tong_so_luong_dat,
                sum(h.t_tien2) AS tong_tien2_vnd,
                sum(h.t_tien_nt2) AS tong_tien_nt2,
                max(h.ma_nt) AS ma_nt
            FROM public.ph64 h
            LEFT JOIN public.dmkh k ON k.ma_kh = h.ma_kh
            WHERE h.ma_ct = 'SO1' 
              AND h.status::text NOT IN ('14', '15')
              AND h.ngay_ct BETWEEN %s AND %s
            GROUP BY h.ma_kh, k.ten_kh, h.ten_kh
            ORDER BY tong_so_luong_dat DESC
            LIMIT 5;
        """
        cursor.execute(sql, (d_from, d_to))
        rows = cursor.fetchall()
        print('rows count:', len(rows))
        for r in rows:
            print(r)
