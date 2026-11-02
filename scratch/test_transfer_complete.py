import sys, re
sys.path.append('functions')
from htmp_postgres_query import connection_settings, clean_numeric_str, extract_iso_date_range, extract_erp_entities, normalize_text, TIMEOUT_MS
import psycopg
from psycopg.rows import dict_row
import json

def internal_warehouse_transfer_register(question: str) -> str | None:
    normalized = normalize_text(question)
    keywords = (
        'nhap kho noi bo', 'xuat kho noi bo', 'phieu nhap noi bo', 'phieu xuat noi bo',
        'nhap kho tu sx', 'nhap kho tu san xuat', 'nhap tu sx', 'nhap tu san xuat',
        'bang ke nhap kho tu san xuat', 'bang ke nhap kho tu sx',
        'bang ke phieu nhap noi bo', 'bang ke phieu xuat noi bo', 'phieu pnd', 'phieu pxa', 'chuyen kho noi bo',
        'tu kho nao sang', 'tu kho nao den', 'sang kho nao', 'chuyen kho', 'dieu chuyen kho', 'luan chuyen kho',
        'duoc nhap kho', 'nhap kho vao nhung ngay nao', 'nhap kho khi nao', 'nhap kho ngay nao',
        'ai lap phieu', 'ai tao phieu', 'tai khoan nao tao phieu', 'tai khoan nao lap phieu', 'nguoi lap phieu', 'nguoi tao phieu'
    )
    is_kw = any(kw in normalized for kw in keywords) or ('nhap kho' in normalized and ('tu kho' in normalized or 'ai' in normalized or 'tai khoan' in normalized))
    if not is_kw:
        return None

    ents = extract_erp_entities(question)
    code = ents.get('ma_vt') or ''
    so_ct = ents.get('so_ct') or ''

    if not code:
        m_vt = re.search(r'\b(?:m[aã]\s+(?:h[aà]ng|v[aậ]t\s+t[uư]|vt)?\s*[:#-]?\s*)([A-Z0-9]+(?:[-/.][A-Z0-9]+)+)\b', question, re.I)
        if m_vt:
            code = m_vt.group(1).upper()
    if not so_ct:
        m_ct = re.search(r'\b(\d{3}-\d{4}-\d{5,6})\b', question)
        if m_ct:
            so_ct = m_ct.group(1).upper()

    if code in ('ERP', 'MES', 'HTMP', 'XLSX', 'PDF', 'DOCX', 'PND', 'PXA', 'PXD', 'PNF', 'PXB'):
        code = ''

    d_from, d_to = extract_iso_date_range(question, '2026-10-01', '2026-10-31')

    try:
        with psycopg.connect(**connection_settings(), autocommit=False) as conn:
            with conn.cursor(row_factory=dict_row) as cursor:
                cursor.execute('SET TRANSACTION READ ONLY')
                cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))

                # Case 1: Specific voucher number
                if so_ct:
                    cursor.execute('''
                        SELECT 
                            h.so_ct, to_char(h.ngay_ct, 'DD/MM/YYYY') AS ngay_ct, h.ma_ct,
                            d.ma_vt, coalesce(v.ten_vt, d.ma_vt) AS ten_vt, d.dvt,
                            d.ma_kho, coalesce(w.ten_kho, d.ma_kho) AS ten_kho,
                            d.so_luong, h.dien_giai, u.user_name, coalesce(u.ten, u.user_name) AS nguoi_lap
                        FROM public.ph74 h
                        JOIN public.ct74 d USING(stt_rec)
                        LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
                        LEFT JOIN public.dmkho w ON w.ma_kho = d.ma_kho
                        LEFT JOIN public.userinfo u ON u.user_id = h.user_id0
                        WHERE h.so_ct = %s
                    ''', (so_ct,))
                    rows_ct = cursor.fetchall()
                    if not rows_ct:
                        cursor.execute('''
                            SELECT 
                                h.so_ct, to_char(h.ngay_ct, 'DD/MM/YYYY') AS ngay_ct, h.ma_ct,
                                d.ma_vt, coalesce(v.ten_vt, d.ma_vt) AS ten_vt, d.dvt,
                                h.ma_kho AS kho_xuat, coalesce(kx.ten_kho, h.ma_kho) AS ten_kho_xuat,
                                h.ma_khon AS kho_nhan, coalesce(kn.ten_kho, h.ma_khon) AS ten_kho_nhan,
                                d.so_luong, h.dien_giai, u.user_name, coalesce(u.ten, u.user_name) AS nguoi_lap
                            FROM public.ph85 h
                            JOIN public.ct85 d USING(stt_rec)
                            LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
                            LEFT JOIN public.dmkho kx ON kx.ma_kho = h.ma_kho
                            LEFT JOIN public.dmkho kn ON kn.ma_kho = h.ma_khon
                            LEFT JOIN public.userinfo u ON u.user_id = h.user_id0
                            WHERE h.so_ct = %s
                        ''', (so_ct,))
                        rows_ct = cursor.fetchall()

                    if rows_ct:
                        formatted_rows = []
                        md_lines = [
                            f"### Chi tiết chứng từ nội bộ số **{so_ct}**",
                            f"- **Ngày chứng từ:** {rows_ct[0]['ngay_ct']} | **Loại phiếu:** {rows_ct[0]['ma_ct']}",
                            f"- **Người tạo:** {rows_ct[0]['user_name']} ({rows_ct[0]['nguoi_lap']}) | **Diễn giải:** {rows_ct[0].get('dien_giai') or 'Không có'}\n",
                            "| STT | Mã vật tư | Tên vật tư | ĐVT | Kho xuất / nhận | Số lượng |",
                            "| :---: | :--- | :--- | :---: | :--- | :---: |"
                        ]
                        for idx, r in enumerate(rows_ct, 1):
                            sl = float(r["so_luong"] or 0)
                            sl_str = f"{sl:,.0f}" if sl.is_integer() else f"{sl:,.2f}"
                            kho_str = f"{r.get('kho_xuat', '')} ➔ {r.get('kho_nhan', '')}" if 'kho_xuat' in r else r.get('ten_kho', '')
                            md_lines.append(f"| {idx} | `{r['ma_vt']}` | {r['ten_vt']} | {r.get('dvt') or 'PCS'} | {kho_str} | {sl_str} |")
                            formatted_rows.append({
                                'stt': idx,
                                'so_ct': r['so_ct'],
                                'ma_vt': r['ma_vt'],
                                'ten_vt': r['ten_vt'],
                                'so_luong': sl_str
                            })
                        return json.dumps({
                            'source': 'public.ph74/ct74 hoặc public.ph85/ct85',
                            'row_count': len(formatted_rows),
                            'rows': formatted_rows,
                            'message': '\n'.join(md_lines)
                        }, ensure_ascii=False, default=str)

                # Case 2: Material code provided
                if code:
                    cursor.execute('SELECT ten_vt, dvt FROM public.dmvt WHERE ma_vt = %s', (code,))
                    vt_info = cursor.fetchone() or {'ten_vt': code, 'dvt': 'PCS'}
                    ten_vt = vt_info['ten_vt']
                    dvt = vt_info.get('dvt') or 'PCS'

                    # 1. PND (SX -> Kho)
                    cursor.execute('''
                        SELECT 
                            to_char(h.ngay_ct, 'DD/MM/YYYY') AS ngay_ct_str,
                            h.ngay_ct,
                            h.so_ct,
                            c.ma_kho AS kho_nhan,
                            coalesce(kn.ten_kho, c.ma_kho) AS ten_kho_nhan,
                            c.so_luong,
                            u.user_name,
                            coalesce(u.ten, u.user_name) AS ten_nguoi_lap
                        FROM public.ct74 c
                        JOIN public.ph74 h USING (stt_rec)
                        LEFT JOIN public.dmkho kn ON kn.ma_kho = c.ma_kho
                        LEFT JOIN public.userinfo u ON u.user_id = h.user_id0
                        WHERE c.ma_vt = %s AND h.ngay_ct BETWEEN %s AND %s
                        ORDER BY h.ngay_ct, h.so_ct
                    ''', (code, d_from, d_to))
                    pnd_rows = cursor.fetchall()

                    # Fallback if no records in date range
                    if not pnd_rows:
                        cursor.execute('''
                            SELECT 
                                to_char(h.ngay_ct, 'DD/MM/YYYY') AS ngay_ct_str,
                                h.ngay_ct,
                                h.so_ct,
                                c.ma_kho AS kho_nhan,
                                coalesce(kn.ten_kho, c.ma_kho) AS ten_kho_nhan,
                                c.so_luong,
                                u.user_name,
                                coalesce(u.ten, u.user_name) AS ten_nguoi_lap
                            FROM public.ct74 c
                            JOIN public.ph74 h USING (stt_rec)
                            LEFT JOIN public.dmkho kn ON kn.ma_kho = c.ma_kho
                            LEFT JOIN public.userinfo u ON u.user_id = h.user_id0
                            WHERE c.ma_vt = %s
                            ORDER BY h.ngay_ct DESC, h.so_ct DESC
                            LIMIT 15
                        ''', (code,))
                        pnd_rows = cursor.fetchall()

                    # 2. ct85 transfer routes
                    cursor.execute('''
                        SELECT 
                            h.ma_kho AS kho_xuat,
                            coalesce(kx.ten_kho, h.ma_kho) AS ten_kho_xuat,
                            h.ma_khon AS kho_nhan,
                            coalesce(kn.ten_kho, h.ma_khon) AS ten_kho_nhan,
                            count(distinct h.so_ct) AS so_phieu,
                            sum(c.so_luong) AS tong_sl,
                            string_agg(distinct u.user_name, ', ') AS ds_tai_khoan,
                            string_agg(distinct coalesce(u.ten, u.user_name), ', ') AS ds_nguoi_lap,
                            to_char(min(h.ngay_ct), 'DD/MM') AS min_date,
                            to_char(max(h.ngay_ct), 'DD/MM') AS max_date
                        FROM public.ct85 c
                        JOIN public.ph85 h USING (stt_rec)
                        LEFT JOIN public.dmkho kx ON kx.ma_kho = h.ma_kho
                        LEFT JOIN public.dmkho kn ON kn.ma_kho = h.ma_khon
                        LEFT JOIN public.userinfo u ON u.user_id = h.user_id0
                        WHERE c.ma_vt = %s AND h.ngay_ct BETWEEN %s AND %s
                        GROUP BY h.ma_kho, kx.ten_kho, h.ma_khon, kn.ten_kho
                        ORDER BY tong_sl DESC
                    ''', (code, d_from, d_to))
                    transfer_routes = cursor.fetchall()

                    # Format response
                    total_pnd_sl = sum(float(r['so_luong'] or 0) for r in pnd_rows)
                    total_transfer_sl = sum(float(r['tong_sl'] or 0) for r in transfer_routes)
                    total_transfer_vouchers = sum(int(r['so_phieu'] or 0) for r in transfer_routes)

                    pnd_dates = sorted(list(set(r['ngay_ct_str'] for r in pnd_rows)))

                    md = []
                    md.append(f"### Báo cáo lịch sử nhập kho và luân chuyển kho mã **{code}**")
                    md.append(f"- **Tên sản phẩm/vật tư:** {ten_vt}")
                    md.append(f"- **Khoảng thời gian tra cứu:** Từ ngày **{d_from}** đến hết ngày **{d_to}**\n")
                    
                    md.append("#### 📌 Tóm tắt kết quả tra cứu:")
                    if pnd_rows:
                        pnd_days_preview = ', '.join(d[:5] for d in pnd_dates[:10]) + (f' (+{len(pnd_dates)-10} ngày khác)' if len(pnd_dates) > 10 else '')
                        md.append(f"1. **Nhập kho từ sản xuất (PND):** Nhập vào **{len(pnd_dates)} ngày** ({pnd_days_preview}) với tổng số lượng **{total_pnd_sl:,.0f} {dvt}** qua **{len(pnd_rows)} phiếu nhập**, vào kho `{pnd_rows[0]['kho_nhan']}` ({pnd_rows[0]['ten_kho_nhan']}). Tài khoản tạo phiếu: **{pnd_rows[0]['user_name']}**.")
                    else:
                        md.append(f"1. **Nhập kho từ sản xuất (PND):** Không phát sinh phiếu PND trong kỳ.")

                    if transfer_routes:
                        top_routes_text = []
                        for r in transfer_routes[:4]:
                            top_routes_text.append(f"`{r['kho_xuat']}` ➔ `{r['kho_nhan']}`: {float(r['tong_sl']):,.0f} {dvt}")
                        md.append(f"2. **Điều chuyển giữa các kho (PNF/PXB):** Phát sinh **{total_transfer_vouchers} phiếu điều chuyển** ({len(transfer_routes)} tuyến kho) với tổng lượng luân chuyển **{total_transfer_sl:,.0f} {dvt}**. Các luồng luân chuyển chính: {'; '.join(top_routes_text)}.")
                        all_tf_users = set()
                        for r in transfer_routes:
                            for u in (r['ds_tai_khoan'] or '').split(','):
                                if u.strip(): all_tf_users.add(u.strip())
                        md.append(f"3. **Tài khoản tạo phiếu điều chuyển:** **{', '.join(sorted(all_tf_users))}**.")
                    md.append("")

                    # Table 1: Route summary
                    if transfer_routes:
                        md.append("#### 1. Tổng hợp luồng điều chuyển qua các kho:")
                        md.append("| STT | Kho xuất | Kho nhận | Số lượng (PCS) | Số phiếu | Thời gian | Tài khoản tạo phiếu | Họ tên người lập |")
                        md.append("| :---: | :--- | :--- | :---: | :---: | :---: | :--- | :--- |")
                        for idx, r in enumerate(transfer_routes, 1):
                            sl = float(r['tong_sl'] or 0)
                            sl_str = f"{sl:,.0f}" if sl.is_integer() else f"{sl:,.2f}"
                            md.append(f"| {idx} | **{r['kho_xuat']}** ({r['ten_kho_xuat']}) | **{r['kho_nhan']}** ({r['ten_kho_nhan']}) | {sl_str} | {r['so_phieu']} | {r['min_date']} - {r['max_date']} | {r['ds_tai_khoan']} | {r['ds_nguoi_lap']} |")
                        md.append("")

                    # Table 2: PND detail
                    if pnd_rows:
                        md.append("#### 2. Chi tiết các phiếu nhập kho từ sản xuất (PND):")
                        md.append("| STT | Số chứng từ | Ngày CT | Kho nhận | Số lượng (PCS) | Tài khoản | Họ tên người lập |")
                        md.append("| :---: | :--- | :---: | :--- | :---: | :--- | :--- |")
                        for idx, r in enumerate(pnd_rows, 1):
                            sl = float(r['so_luong'] or 0)
                            sl_str = f"{sl:,.0f}" if sl.is_integer() else f"{sl:,.2f}"
                            md.append(f"| {idx} | `{r['so_ct']}` | {r['ngay_ct_str']} | {r['ten_kho_nhan']} (`{r['kho_nhan']}`) | {sl_str} | {r['user_name']} | {r['ten_nguoi_lap']} |")
                        md.append("")

                    # Mermaid Flowchart
                    if transfer_routes:
                        md.append("#### 3. Sơ đồ chu trình luân chuyển kho thực tế:")
                        md.append("```mermaid")
                        md.append("flowchart LR")
                        pnd_user_str = pnd_rows[0]['user_name'] if pnd_rows else 'SX'
                        md.append(f'    SX["Xưởng Sản Xuất"] -->|"Nhập SX: {total_pnd_sl:,.0f} PCS<br/>User: {pnd_user_str}"| TM["Kho tại máy<br/>(KHO_TAIMAY)"]')
                        added_edges = 0
                        for r in transfer_routes:
                            if r['kho_xuat'] != r['kho_nhan'] and added_edges < 6:
                                kx_id = r['kho_xuat'].replace('-', '_')
                                kn_id = r['kho_nhan'].replace('-', '_')
                                sl_val = float(r['tong_sl'])
                                md.append(f'    {kx_id}["{r["kho_xuat"]}<br/>({r["ten_kho_xuat"]})"] -->|"{sl_val:,.0f} PCS<br/>User: {r["ds_tai_khoan"]}"| {kn_id}["{r["kho_nhan"]}<br/>({r["ten_kho_nhan"]})"]')
                                added_edges += 1
                        md.append("```")
                        md.append("")

                    formatted_rows = []
                    for idx, r in enumerate(transfer_routes, 1):
                        formatted_rows.append({
                            'stt': idx,
                            'kho_xuat': r['kho_xuat'],
                            'kho_nhan': r['kho_nhan'],
                            'tong_sl': float(r['tong_sl'] or 0),
                            'so_phieu': r['so_phieu'],
                            'tai_khoan': r['ds_tai_khoan']
                        })

                    return json.dumps({
                        'source': 'public.ph85 / public.ct85 (Phiếu chuyển kho) & public.ph74 / public.ct74 (Nhập kho SX)',
                        'lookup': {'ma_vt': code, 'tu_ngay': d_from, 'den_ngay': d_to},
                        'row_count': len(formatted_rows),
                        'rows': formatted_rows,
                        'message': '\n'.join(md)
                    }, ensure_ascii=False, default=str)

                # Case 3: Recent PND list
                cursor.execute('''
                    SELECT 
                        h.so_ct,
                        to_char(h.ngay_ct, 'DD/MM/YYYY') AS ngay_ct,
                        h.ma_ct AS loai_phieu,
                        d.ma_vt,
                        coalesce(v.ten_vt, d.ma_vt) AS ten_vt,
                        d.dvt,
                        d.ma_kho,
                        coalesce(w.ten_kho, d.ma_kho) AS ten_kho,
                        d.so_luong,
                        u.user_name,
                        coalesce(u.ten, u.user_name) AS nguoi_lap
                    FROM public.ph74 h
                    JOIN public.ct74 d USING(stt_rec)
                    LEFT JOIN public.dmvt v ON v.ma_vt = d.ma_vt
                    LEFT JOIN public.dmkho w ON w.ma_kho = d.ma_kho
                    LEFT JOIN public.userinfo u ON u.user_id = h.user_id0
                    ORDER BY h.ngay_ct DESC, h.stt_rec DESC, d.ln
                    LIMIT 20;
                ''')
                rows_rec = cursor.fetchall()
                formatted_rows = []
                md_lines = [
                    "### Bảng kê phiếu nhập kho nội bộ từ sản xuất phát sinh gần đây",
                    "| STT | Số chứng từ | Ngày CT | Mã vật tư | Tên vật tư | ĐVT | Kho nhận | Số lượng (PCS) | Người lập |",
                    "| :---: | :--- | :---: | :--- | :--- | :---: | :--- | :---: | :--- |"
                ]
                for idx, r in enumerate(rows_rec, 1):
                    sl = float(r["so_luong"] or 0)
                    sl_str = f"{sl:,.0f}" if sl.is_integer() else f"{sl:,.2f}"
                    md_lines.append(f"| {idx} | `{r['so_ct']}` | {r['ngay_ct']} | `{r['ma_vt']}` | {r['ten_vt']} | {r.get('dvt') or 'PCS'} | {r['ten_kho']} (`{r['ma_kho']}`) | {sl_str} | {r['user_name']} ({r['nguoi_lap']}) |")
                    formatted_rows.append({
                        'stt': idx,
                        'so_ct': r['so_ct'],
                        'ngay_ct': r['ngay_ct'],
                        'ma_vt': r['ma_vt'],
                        'so_luong': sl_str
                    })
                return json.dumps({
                    'source': 'public.ph74 / public.ct74 (Phiếu nhập kho nội bộ)',
                    'row_count': len(formatted_rows),
                    'rows': formatted_rows,
                    'message': '\n'.join(md_lines)
                }, ensure_ascii=False, default=str)
    except Exception as e:
        import traceback
        traceback.print_exc()
        return None

if __name__ == '__main__':
    q = 'Từ ngày 01/10/2026 đến hết ngày 20/10/2026, mã QC7-5146-000 được nhập kho vào những ngày nào, từ kho nào sang kho nào, số lượng bao nhiêu và tài khoản nào tạo phiếu?'
    res = internal_warehouse_transfer_register(q)
    data = json.loads(res)
    print("SUCCESS! Output:")
    print(data['message'])

