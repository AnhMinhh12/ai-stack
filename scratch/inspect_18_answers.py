"""Script to inspect ground truth in PostgreSQL database for the 18 user questions."""

import sys
sys.path.insert(0, ".")
import psycopg
from psycopg.rows import dict_row
from functions.htmp_postgres_query import Tools
from erp_ai.native_tools import connection_settings

tools = Tools()

def inspect_ground_truth():
    print("=" * 80)
    print("INSPECTING GROUND TRUTH FOR 18 QUESTIONS")
    print("=" * 80)

    # Q1: BOM & Plastic material of QC7-5146-000
    print("\n--- Q1: BOM & Loại nhựa QC7-5146-000 ---")
    print(tools.lookup_bom(product_code="QC7-5146-000"))

    # Q2: MOQ & Giá bán QC7-5146-000
    print("\n--- Q2: Giá bán & MOQ QC7-5146-000 ---")
    print(tools.lookup_sales_price(material_code="QC7-5146-000"))

    # Q5: Khách hàng của QC7-5146-000
    print("\n--- Q5: Khách hàng của QC7-5146-000 ---")
    with psycopg.connect(**connection_settings(), autocommit=False) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT v.ma_vt, v.ten_vt, v.ma_kh, k.ten_kh
                FROM dmvt v
                LEFT JOIN dmkh k ON trim(k.ma_kh) = trim(v.ma_kh)
                WHERE trim(v.ma_vt) = 'QC7-5146-000'
            """)
            print(cur.fetchall())

    # Q8: Quy cách đóng gói QC7-5146-000
    print("\n--- Q8: Quy cách đóng gói QC7-5146-000 ---")
    print(tools.lookup_general_catalog(category="quy_cach", keyword="QC7-5146-000"))

    # Q11: Tồn kho theo khuôn
    print("\n--- Q11: Tồn kho theo khuôn QC7-5146-000 ---")
    with psycopg.connect(**connection_settings(), autocommit=False) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT ma_vt, ma_lo, ma_kho, so_luong
                FROM public.ctlo
                WHERE trim(ma_vt) = 'QC7-5146-000'
                LIMIT 5
            """)
            print("ctlo:", cur.fetchall())

    # Q14: Tồn kho theo từng kho
    print("\n--- Q14: Tồn kho theo từng kho QC7-5146-000 ---")
    print(tools.lookup_inventory_stock(material_code="QC7-5146-000"))

    # Q17: Mã khách hàng của Canon Thăng Long
    print("\n--- Q17: Mã KH của Canon Thăng Long ---")
    with psycopg.connect(**connection_settings(), autocommit=False) as conn:
        with conn.cursor(row_factory=dict_row) as cur:
            cur.execute("""
                SELECT ma_kh, ten_kh
                FROM dmkh
                WHERE ten_kh ILIKE '%Canon%Thăng Long%' OR ten_kh ILIKE '%Thang Long%'
            """)
            print(cur.fetchall())

if __name__ == "__main__":
    inspect_ground_truth()

