#!/usr/bin/env python3
"""
Trích xuất toàn bộ metadata hệ thống 3S ERP / MES trực tiếp từ database PostgreSQL:
- sys_dmtt: Từ điển trạng thái chứng từ (Đã duyệt, Từ chối, Hủy, Đã ghi sổ kho...)
- sys_listoptions: Từ điển danh mục tùy chọn (QC OK/NG, hình thức...)
- sys_gridconfig: Cấu hình hiển thị cột giao diện, nhãn tiếng Việt, cột ẩn/hiện
- sys_reports: Danh mục 432 báo cáo chuẩn và liên kết mã lưới
- pg_proc: 1.258 functions API và hàm trả về bảng dữ liệu (SETOF)
"""

import os
import json
import psycopg
from collections import defaultdict
from pathlib import Path

def extract_metadata():
    conn_params = {
        'host': os.getenv('HTMP_DB_HOST', '10.0.6.2'),
        'port': os.getenv('HTMP_DB_PORT', '5410'),
        'dbname': os.getenv('HTMP_DB_NAME', '3SERP_HTMP_DATA'),
        'user': os.getenv('HTMP_DB_USER', 'read_htmp'),
        'password': os.getenv('HTMP_DB_PASSWORD', 'P@ss@Htmp@W0rd!2025'),
        'connect_timeout': 10
    }

    print("1. Đang kết nối tới PostgreSQL 3SERP_HTMP_DATA...")
    with psycopg.connect(**conn_params) as conn:
        with conn.cursor() as cur:
            # 1. sys_dmtt: Document Status Dictionary
            print("2. Đang trích xuất sys_dmtt (Từ điển trạng thái)...")
            cur.execute("""
                SELECT ma_ct, status, statusname, statusname2, appr_yn, deny_yn, close_yn, post_inventory_yn, post_ledger_yn
                FROM public.sys_dmtt
                ORDER BY ma_ct, status;
            """)
            status_dict = defaultdict(dict)
            for ma_ct, status, sname, sname2, appr, deny, close, post_inv, post_led in cur.fetchall():
                ma_ct_clean = (ma_ct or '').strip()
                status_clean = str(status).strip()
                if ma_ct_clean and status_clean:
                    status_dict[ma_ct_clean][status_clean] = {
                        "label": (sname or '').strip(),
                        "label_en": (sname2 or '').strip(),
                        "is_approved": bool(appr),
                        "is_denied": str(deny) == '1' or bool(deny),
                        "is_closed": str(close) == '1' or bool(close),
                        "is_stock_posted": bool(post_inv),
                        "is_ledger_posted": bool(post_led)
                    }

            # 2. sys_listoptions: Form options
            print("3. Đang trích xuất sys_listoptions (Từ điển tùy chọn danh mục)...")
            cur.execute("""
                SELECT form, form_value, form_name, form_name2
                FROM public.sys_listoptions
                ORDER BY form, form_value;
            """)
            list_options = defaultdict(dict)
            for form, fval, fname, fname2 in cur.fetchall():
                form_clean = (form or '').strip()
                val_clean = str(fval).strip()
                if form_clean and val_clean:
                    list_options[form_clean][val_clean] = {
                        "label": (fname or '').strip(),
                        "label_en": (fname2 or '').strip()
                    }

            # 3. sys_gridconfig: UI Grid Columns & Captions
            print("4. Đang trích xuất sys_gridconfig (Cột hiển thị & Nhãn giao diện)...")
            cur.execute("""
                SELECT gridid, tablename, fieldposition, fieldname, field_root, fieldcaption, 
                       visible, hidden_yn, aggregator, footer_total_yn
                FROM public.sys_gridconfig
                WHERE visible = 1 AND (hidden_yn IS FALSE OR hidden_yn IS NULL)
                ORDER BY gridid, fieldposition, fieldname;
            """)
            grids_dict = defaultdict(lambda: {"tables": set(), "columns": []})
            for gid, tbl, pos, fname, froot, fcaption, vis, hid, agg, footer in cur.fetchall():
                gid_clean = (gid or '').strip()
                tbl_clean = (tbl or '').strip()
                fname_clean = (fname or '').strip()
                caption_clean = (fcaption or '').strip()
                if gid_clean and fname_clean:
                    if tbl_clean:
                        grids_dict[gid_clean]["tables"].add(tbl_clean)
                    grids_dict[gid_clean]["columns"].append({
                        "position": pos,
                        "field": fname_clean,
                        "field_root": (froot or '').strip(),
                        "caption": caption_clean,
                        "table": tbl_clean,
                        "is_footer_total": bool(footer),
                        "aggregator": (agg or '').strip() if agg else None
                    })

            for g in grids_dict:
                grids_dict[g]["tables"] = sorted(list(grids_dict[g]["tables"]))

            # 4. sys_reports: Standard Reports
            print("5. Đang trích xuất sys_reports (Danh mục báo cáo chuẩn)...")
            cur.execute("""
                SELECT rep_id, rep_title, rep_text, gridid, rep_file, ma_gd
                FROM public.sys_reports
                WHERE status::text = '1' OR status IS NULL
                ORDER BY rep_id;
            """)
            reports_dict = {}
            for rep_id, rep_title, rep_text, gid, rfile, ma_gd in cur.fetchall():
                rid_clean = (rep_id or '').strip()
                if rid_clean:
                    reports_dict[rid_clean] = {
                        "title": (rep_title or rep_text or '').strip(),
                        "gridid": (gid or '').strip(),
                        "report_file": (rfile or '').strip(),
                        "ma_gd": (ma_gd or '').strip()
                    }

            # 5. Core Functions in DB
            print("6. Đang trích xuất pg_proc (Các hàm tính toán & API báo cáo)...")
            cur.execute("""
                SELECT p.proname, 
                       pg_get_function_result(p.oid) as result_type,
                       pg_get_function_arguments(p.oid) as arguments
                FROM pg_proc p
                JOIN pg_namespace n ON p.pronamespace = n.oid
                WHERE n.nspname = 'public'
                  AND (pg_get_function_result(p.oid) LIKE 'SETOF%' 
                       OR pg_get_function_arguments(p.oid) LIKE '%params%')
                ORDER BY p.proname;
            """)
            functions_dict = {}
            for fname, rtype, args in cur.fetchall():
                functions_dict[fname] = {
                    "result_type": rtype,
                    "arguments": args
                }

    bundle = {
        "version": "1.0.0",
        "extracted_at": "2026-10-30",
        "stats": {
            "document_types": len(status_dict),
            "list_option_forms": len(list_options),
            "ui_grids": len(grids_dict),
            "standard_reports": len(reports_dict),
            "core_functions": len(functions_dict)
        },
        "document_statuses": dict(status_dict),
        "list_options": dict(list_options),
        "grids": dict(grids_dict),
        "reports": reports_dict,
        "api_functions": functions_dict
    }

    out_file = Path("/home/admin/ai-stack/config/erp_metadata_dictionary.json")
    out_file.parent.mkdir(parents=True, exist_ok=True)
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(bundle, f, ensure_ascii=False, indent=2)

    print(f"\n HOÀN TẤT TRÍCH XUẤT:")
    print(f" - {len(status_dict)} loại chứng từ (SO1, TO2, HDA, PO1, PN1...)")
    print(f" - {len(list_options)} bộ tùy chọn danh mục")
    print(f" - {len(grids_dict)} màn hình/lưới giao diện với cột và nhãn tiếng Việt")
    print(f" - {len(reports_dict)} báo cáo chuẩn")
    print(f" - {len(functions_dict)} functions nghiệp vụ và API")
    print(f" - Tệp lưu tại: {out_file} ({out_file.stat().st_size / 1024:.1f} KB)")

if __name__ == "__main__":
    extract_metadata()
