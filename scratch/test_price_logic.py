import psycopg
from psycopg.rows import dict_row
from functions.htmp_postgres_query import connection_settings, clean_numeric_str

def test_price(code):
    with psycopg.connect(**connection_settings(), autocommit=False) as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            sql = """
                SELECT 
                    b.ma_bang_gia,
                    b.ten_bang_gia,
                    trim(c.ma_vt) AS ma_vt,
                    coalesce(v.ten_vt, c.ma_vt) AS ten_vt,
                    coalesce(v.dvt, c.dvt, 'PCS') AS dvt,
                    trim(c.ma_kh) AS ma_kh,
                    coalesce(k.ten_kh, c.ma_kh) AS ten_kh,
                    c.gia AS don_gia_ban,
                    coalesce(c.ma_nt, 'VND') AS ma_nt,
                    coalesce(c.sl_min, 0) AS sl_min,
                    to_char(c.ngay_bd, 'YYYY-MM-DD') AS ngay_bd,
                    to_char(c.ngay_kt, 'YYYY-MM-DD') AS ngay_kt
                FROM public.dmbanggiact c
                JOIN public.dmbanggia b ON b.ma_bang_gia = c.ma_bang_gia
                LEFT JOIN public.dmvt v ON upper(trim(v.ma_vt)) = upper(trim(c.ma_vt))
                LEFT JOIN public.dmkh k ON upper(trim(k.ma_kh)) = upper(trim(c.ma_kh))
                WHERE upper(trim(c.ma_vt)) = %s 
                   OR upper(trim(b.ma_bang_gia)) = %s 
                   OR upper(trim(c.ma_kh)) = %s
                ORDER BY c.ngay_bd DESC, c.ma_bang_gia
                LIMIT 10;
            """
            cursor.execute(sql, (code, code, code))
            rows = cursor.fetchall()
            for idx, r in enumerate(rows, 1):
                r["stt"] = idx
                if r.get("don_gia_ban") is not None:
                    r["don_gia_ban"] = clean_numeric_str(r["don_gia_ban"])
            if rows:
                first = rows[0]
                ten = first.get("ten_vt", code)
                gia = first.get("don_gia_ban", "0")
                nt = first.get("ma_nt", "VND")
                dvt = first.get("dvt", "PCS")
                kh = first.get("ten_kh", first.get("ma_kh", ""))
                bd = first.get("ngay_bd", "")
                kt = first.get("ngay_kt", "")
                bg = first.get("ten_bang_gia", first.get("ma_bang_gia", ""))
                msg = f"Giá bán của mã hàng {code} ({ten}) là {gia} {nt}/{dvt}"
                if kh:
                    msg += f" (khách hàng: {kh})"
                if bd and kt:
                    msg += f", hiệu lực: {bd} đến {kt}"
                if bg:
                    msg += f" [{bg}]."
                else:
                    msg += "."
                print(msg)
            else:
                print(f"No price for {code}")

print("Testing 156279430:")
test_price("156279430")

print("\nTesting T1015910DA:")
test_price("T1015910DA")
