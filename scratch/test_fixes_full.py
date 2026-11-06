import re
import json
import psycopg
from psycopg.rows import dict_row
from functions.htmp_postgres_query import (
    connection_settings, clean_numeric_str, normalize_text, TIMEOUT_MS,
    ERP_CONVERSATION_STATE, extract_erp_entities
)
from erp_ai.entities import KNOWN_WAREHOUSES

def new_inventory_stock_by_warehouse(self, question: str) -> str | None:
    """Query inventory balance by warehouse for a material or total warehouse stock."""
    clean_question = re.sub(r"\b\d{1,2}:\d{2}(?::\d{2})?(?:\s+\d{1,2}\s+thg\s+\d{1,2}(?:\s+\d{4})?)?\b", "", question, flags=re.I)
    normalized = normalize_text(clean_question)
    if any(k in normalized for k in ("tu kho", "chuyen kho", "nhap kho", "ai lap", "ai tao", "tai khoan", "sang kho")):
        return None

    target_warehouse = None
    for wh in KNOWN_WAREHOUSES:
        if re.search(rf"\b{re.escape(wh)}\b", clean_question, re.I):
            target_warehouse = wh.upper()
            break

    wh_keywords = (
        "o tung kho", "tung kho", "cac kho", "theo kho", "nhung kho", "kho nao", "ton o kho", "tat ca cac kho",
        "ton o", "ton tai", "ton kho tai", "ton kho o", "ton chi tiet cac kho", "ton chi tiet", "so luong ton o",
        "so luong ton tai"
    )
    if not any(k in normalized for k in wh_keywords) and not target_warehouse:
        return None

    # Detect material code
    code_match = re.search(r"\b([a-zA-Z0-9]+(?:[-/][a-zA-Z0-9]+)+|[a-zA-Z]{2,}\d+|\d+[a-zA-Z]+\d*)\b", clean_question, re.I)
    material_code = None
    if code_match:
        c = code_match.group(1).upper()
        if c not in KNOWN_WAREHOUSES and not c.startswith("KHO") and not (c.isdigit() and len(c) < 6):
            material_code = c
    if not material_code:
        num_match = re.search(r"\b(\d{6,})\b", clean_question)
        if num_match:
            material_code = num_match.group(1)
    if not material_code and hasattr(self, "_current_conversation_id") and self._current_conversation_id:
        prior_filters = ERP_CONVERSATION_STATE._states.get(self._current_conversation_id, {})
        if prior_filters and prior_filters.get("ma_vt"):
            material_code = prior_filters["ma_vt"]

    if material_code and hasattr(self, "_current_conversation_id") and self._current_conversation_id:
        ERP_CONVERSATION_STATE.remember(self._current_conversation_id, {"ma_vt": material_code})

    try:
        import psycopg
        with psycopg.connect(**connection_settings(), autocommit=False) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SET TRANSACTION READ ONLY")
                cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                cursor.execute("SELECT public.sys_getstartdate(CURRENT_DATE)")
                start_date = cursor.fetchone()[0]

                if material_code:
                    cursor.execute("""
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
                    """, (start_date, material_code, material_code, start_date))
                    rows = cursor.fetchall()

                    cursor.execute("SELECT coalesce(ten_vt, %s), coalesce(dvt, 'PCS') FROM public.dmvt WHERE upper(trim(ma_vt)) = %s", (material_code, material_code))
                    r_vt = cursor.fetchone()
                    ten_vt = str(r_vt[0]).strip() if r_vt and r_vt[0] else material_code
                    dvt = str(r_vt[1]).strip() if r_vt and r_vt[1] else "PCS"

                    if not rows:
                        if r_vt:
                            msg = f"Mã vật tư {material_code} ({ten_vt}) có trong danh mục hệ thống nhưng hiện tại không còn tồn ở kho nào (số dư tồn kho bằng 0)."
                        else:
                            prefix = material_code[:6] if len(material_code) >= 6 else material_code
                            cursor.execute("SELECT ma_vt, ten_vt FROM public.dmvt WHERE ma_vt ILIKE %s ORDER BY ma_vt LIMIT 3", (f"%{prefix}%",))
                            suggestions = cursor.fetchall()
                            if suggestions:
                                sug_str = "; ".join(f"{s[0]} ({s[1]})" for s in suggestions)
                                msg = f"Không tìm thấy mã vật tư '{material_code}' trong hệ thống ERP. Có thể bạn muốn tìm: {sug_str}?"
                            else:
                                msg = f"Không tìm thấy mã vật tư '{material_code}' trong danh mục ERP (dmvt)."
                        return json.dumps({
                            "report": {"id": "bao-cao-ton-theo-kho", "title": "Báo cáo tồn theo kho"},
                            "lookup": {"ma_vt": material_code},
                            "rows": [],
                            "message": msg,
                        }, ensure_ascii=False, default=str)

                    parts = [f"{r[0]}: {int(r[1]):,} {dvt}" for r in rows]
                    total = sum(int(r[1]) for r in rows)

                    if target_warehouse:
                        wh_match = [r for r in rows if r[0].upper() == target_warehouse]
                        wh_qty = int(wh_match[0][1]) if wh_match else 0
                        msg = f"Tồn kho của mã {material_code} ({ten_vt}) tại kho {target_warehouse} hiện tại là {wh_qty:,} {dvt}"
                        if total > 0:
                            msg += f" (Tổng tồn toàn bộ các kho: {total:,} {dvt} gồm {'; '.join(parts)})."
                        else:
                            msg += f" (Mã {material_code} hiện tại không còn tồn ở kho nào khác)."
                        return json.dumps({
                            "report": {"id": "bao-cao-ton-theo-kho", "title": "Báo cáo tồn theo kho"},
                            "lookup": {"ma_vt": material_code, "ma_kho": target_warehouse},
                            "rows": [{"ma_kho": r[0], "ton_kho": int(r[1])} for r in rows],
                            "message": msg,
                        }, ensure_ascii=False, default=str)
                    else:
                        msg = f"Tồn kho hiện tại của mã {material_code} ({ten_vt}) ở từng kho: " + "; ".join(parts) + f" (Tổng cộng: {total:,} {dvt})."
                        return json.dumps({
                            "report": {"id": "bao-cao-ton-theo-kho", "title": "Báo cáo tồn theo kho"},
                            "lookup": {"ma_vt": material_code},
                            "rows": [{"ma_kho": r[0], "ton_kho": int(r[1])} for r in rows],
                            "message": msg,
                        }, ensure_ascii=False, default=str)
                elif target_warehouse:
                    cursor.execute("""
                        SELECT coalesce(k.ten_kho, %s), sum(b.so_luong_ton) AS tong_ton
                        FROM (
                            SELECT sum(ton00) AS so_luong_ton
                            FROM public.cdvt
                            WHERE nam = extract(year FROM %s::date)::smallint AND upper(trim(ma_kho)) = %s
                            UNION ALL
                            SELECT sum(sl_nhap - sl_xuat) AS so_luong_ton
                            FROM public.ct70
                            WHERE ngay_ct >= %s AND upper(trim(ma_kho)) = %s
                        ) b
                        LEFT JOIN public.dmkho k ON upper(trim(k.ma_kho)) = %s
                        GROUP BY k.ten_kho;
                    """, (target_warehouse, start_date, target_warehouse, start_date, target_warehouse, target_warehouse))
                    r = cursor.fetchone()
                    ten_kho = r[0] if r else target_warehouse
                    total_wh = int(r[1]) if r and r[1] else 0
                    msg = f"Tổng số lượng tồn kho tại kho {target_warehouse} ({ten_kho}) hiện tại là {total_wh:,} PCS."
                    return json.dumps({
                        "report": {"id": "bao-cao-ton-theo-kho", "title": "Báo cáo tồn theo kho"},
                        "lookup": {"ma_kho": target_warehouse},
                        "rows": [{"ma_kho": target_warehouse, "ton_kho": total_wh}],
                        "message": msg,
                    }, ensure_ascii=False, default=str)
    except Exception as e:
        return None
    return None

class Dummy:
    _current_conversation_id = "conv_test"

d = Dummy()
ERP_CONVERSATION_STATE.remember("conv_test", {"ma_vt": "1014084300"})

print("Testing new_inventory_stock_by_warehouse with prior 1014084300:")
res = new_inventory_stock_by_warehouse(d, "cho chị hỏi tồn ở KHOTP00 có bao nhiêu 15:45 6 thg 11")
print(res)

print("\nTesting new_inventory_stock_by_warehouse without prior material:")
d2 = Dummy()
d2._current_conversation_id = "conv_test_empty"
res2 = new_inventory_stock_by_warehouse(d2, "cho chị hỏi tồn ở KHOTP00 có bao nhiêu 15:45 6 thg 11")
print(res2)
