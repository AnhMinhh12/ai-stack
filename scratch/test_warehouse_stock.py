import psycopg
from psycopg.rows import dict_row
from functions.htmp_postgres_query import connection_settings

def test_wh_stock(material_code, warehouse_code):
    with psycopg.connect(**connection_settings(), autocommit=False) as conn:
        with conn.cursor(row_factory=dict_row) as cursor:
            cursor.execute("SELECT public.sys_getstartdate(CURRENT_DATE)")
            start_date = cursor.fetchone()["sys_getstartdate"]
            
            # 1. If material_code is provided
            if material_code:
                sql = """
                    WITH opening AS (
                        SELECT c.ma_kho, sum(c.ton00) AS qty
                        FROM public.cdvt c
                        WHERE c.nam = extract(year FROM %s::date)::smallint
                          AND upper(trim(c.ma_vt)) = %s
                        GROUP BY c.ma_kho
                    ),
                    movements AS (
                        SELECT c.ma_kho, sum(c.sl_nhap - c.sl_xuat) AS qty
                        FROM public.ct70 c
                        WHERE upper(trim(c.ma_vt)) = %s
                          AND c.ngay_ct >= %s
                        GROUP BY c.ma_kho
                    ),
                    combined AS (
                        SELECT ma_kho, qty FROM opening
                        UNION ALL
                        SELECT ma_kho, qty FROM movements
                    )
                    SELECT ma_kho, sum(qty) AS ton_kho
                    FROM combined
                    GROUP BY ma_kho
                    HAVING sum(qty) > 0
                    ORDER BY ton_kho DESC;
                """
                cursor.execute(sql, (start_date, material_code, material_code, start_date))
                rows = cursor.fetchall()
                print(f"All warehouses stock for {material_code}:", [(r['ma_kho'], int(r['ton_kho'])) for r in rows])
                
                # Check specific warehouse
                if warehouse_code:
                    wh_match = [r for r in rows if r['ma_kho'].upper() == warehouse_code.upper()]
                    wh_qty = int(wh_match[0]['ton_kho']) if wh_match else 0
                    print(f"Stock of {material_code} specifically at {warehouse_code}: {wh_qty} PCS")
            else:
                # Total stock in warehouse across all materials
                sql_wh = """
                    SELECT sum(b.so_luong_ton) AS tong_ton
                    FROM (
                        SELECT sum(ton00) AS so_luong_ton
                        FROM public.cdvt
                        WHERE nam = extract(year FROM %s::date)::smallint AND upper(trim(ma_kho)) = %s
                        UNION ALL
                        SELECT sum(sl_nhap - sl_xuat) AS so_luong_ton
                        FROM public.ct70
                        WHERE ngay_ct >= %s AND upper(trim(ma_kho)) = %s
                    ) b;
                """
                cursor.execute(sql_wh, (start_date, warehouse_code, start_date, warehouse_code))
                total = cursor.fetchone()["tong_ton"]
                print(f"Total inventory in warehouse {warehouse_code} across all items: {int(total):,} PCS")

print("Testing 1014084300 at KHOTP00:")
test_wh_stock("1014084300", "KHOTP00")

print("\nTesting total at KHOTP00 (no material):")
test_wh_stock(None, "KHOTP00")
