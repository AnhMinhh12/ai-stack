"""Operator-reviewed, parameterized reference probes; never supplied to Qwen.

Not UI gold answers: preserve dates, status codes, grain, and unsupported meanings.
Run only with an explicitly verified configured ERP superuser audit scope.
"""
MATERIAL='QC7-5146-000'
CUSTOMER='KH0015'
MOLD='K_QC5-2919-000-V1'
DELIVERY='001-2610-001811'
START, END='2026-10-01','2026-10-20'

def probes():
    out=[]
    def add(name, cases, sql, params=(), caveat=''):
        out.append(dict(name=name,cases=cases,sql=sql,parameters=params,caveat=caveat))
    add('bom',[1],'''SELECT b.bom_code,b.bom_version,b.status,b.valid_from,b.valid_to,
 m.material_code,v.ten_vt,m.quantity,m.uom FROM public.mfbom b
 JOIN public.mfbom_material m USING(bom_code) LEFT JOIN public.dmvt v ON v.ma_vt=m.material_code
 WHERE b.product_code=%s AND %s::date BETWEEN b.valid_from AND b.valid_to
 ORDER BY b.bom_version DESC,m.material_code LIMIT 30''',(MATERIAL,END),'Effective BOM components; status remains raw, no inferred approval.')
    add('current_prices',[2],'''SELECT d.ma_kh,d.sl_min,d.dvt,d.gia,d.gia0,d.ma_nt,d.ngay_bd,d.ngay_kt,h.status
 FROM public.dmbanggiact d JOIN public.dmbanggia h USING(ma_bang_gia)
 WHERE d.ma_vt=%s AND %s::date BETWEEN d.ngay_bd AND d.ngay_kt
 ORDER BY d.ma_kh,d.sl_min,d.ngay_bd DESC LIMIT 30''',(MATERIAL,END),'sl_min is a threshold; do not infer upper ranges or approval from status.')
    add('latest_sales_document',[3],'''SELECT h.stt_rec,h.so_ct,h.ngay_lct,h.ngay_ct,h.status,
 array_agg(DISTINCT nullif(d.ma_lo,'')) AS lots,sum(d.so_luong) AS quantity,count(*) AS lines
 FROM public.ph81 h JOIN public.ct81 d USING(stt_rec)
 WHERE d.ma_vt=%s AND h.ma_gd<>4 AND h.ngay_lct<=%s::date
 GROUP BY h.stt_rec,h.so_ct,h.ngay_lct,h.ngay_ct,h.status
 ORDER BY h.ngay_lct DESC,h.ngay_ct DESC,h.so_ct DESC,h.stt_rec DESC LIMIT 3''',(MATERIAL,END),'Latest sales issue, not proof of actual customer delivery; blank lot is unknown.')
    add('sales_posted',[4,10],'''SELECT to_char(h.ngay_ct,'YYYY-MM') AS period,h.ma_kh,d.dvt,
 count(*) AS lines,sum(d.so_luong) AS quantity,sum(d.tien2) AS tien2_local_currency,
 sum(d.ck) AS discount_local_currency,sum(d.thue) AS tax_local_currency
 FROM public.ph81 h JOIN public.ct81 d USING(stt_rec)
 WHERE d.ma_vt=%s AND h.ma_kh=%s AND h.ma_gd<>4
 AND ((h.ngay_ct BETWEEN %s::date AND %s::date) OR (h.ngay_ct BETWEEN %s::date AND %s::date))
 AND EXISTS(SELECT 1 FROM public.sys_dmtt s WHERE s.ma_ct='HDA' AND s.status=h.status AND s.post_inventory_yn)
 GROUP BY 1,h.ma_kh,d.dvt ORDER BY 1''',(MATERIAL,CUSTOMER,'2026-09-01','2026-09-20',START,END),'tien2 follows current handler; net revenue/tax meaning still requires business definition.')
    add('sales_agent_scope',[3,4,10],'''SELECT count(*) AS lines,sum(d.so_luong) AS quantity,
 sum(d.tien2) AS tien2_local_currency,min(h.ngay_lct) AS first_date,max(h.ngay_lct) AS last_date
 FROM public.ph81 h JOIN public.ct81 d USING(stt_rec)
 WHERE d.ma_vt=%s AND h.ma_gd<>4 AND h.ngay_lct BETWEEN %s::date AND %s::date''',(MATERIAL,START,END),'Matches pilot date/status scope; full count, no LIMIT before aggregate.')
    add('material_customer',[5,17],'''SELECT v.ma_vt,v.ma_kh,k.ten_kh FROM public.dmvt v
 LEFT JOIN public.dmkh k ON k.ma_kh=v.ma_kh WHERE v.ma_vt=%s''',(MATERIAL,),'Declared customer, not all historical transaction customers.')
    add('receipt_ledger',[6],'''SELECT a.stt_rec,a.ln,a.so_ct,a.ngay_ct,a.date0,a.time0,a.ma_kho,
 a.sl_nhap,a.stt_rec_dc,a.ln_dc,a.user_id0,u.user_name AS record_creator,
 src.ma_kho AS source_warehouse
 FROM public.ct70 a LEFT JOIN public.userinfo u ON u.user_id=a.user_id0
 LEFT JOIN public.ct70 src ON src.stt_rec=a.stt_rec_dc AND src.ln=a.ln_dc AND src.ma_vt=a.ma_vt AND src.nxt=2
 WHERE a.ma_vt=%s AND a.nxt=1 AND a.date0 BETWEEN %s::date AND %s::date
 ORDER BY a.ngay_ct DESC,a.so_ct DESC,a.stt_rec,a.ln LIMIT 10''',(MATERIAL,START,END),'Creator is not necessarily physical receiver; source warehouse only where transfer link exists.')
    add('forecast_metadata',[7,9],'''SELECT nguon_du_lieu,loai_du_lieu,count(*) AS rows,
 count(DISTINCT ngay_tinh_toan) AS calculation_dates,min(ngay_tinh_toan),max(ngay_tinh_toan)
 FROM public.mfkhsx_po_fc WHERE ma_vt=%s GROUP BY 1,2 ORDER BY 1,2''',(MATERIAL,),'Distinct calculation dates do not establish historical forecast versions. XLSX says feature absent.')
    add('packaging',[8],'''SELECT ma_vt,dvt,packs,packs0,ma_thung,ma_khay,so_luong_vt_khay,
 so_luong_thung_pallet,so_luong_sp_tui FROM public.dmvt WHERE ma_vt=%s''',(MATERIAL,),'Do not divide by zero pallet coefficient or equate label stock with ledger stock.')
    add('mold',[9],'''SELECT h.ma_khuon,h.tong_so_shot,h.so_shot_bh,s.ma_sp FROM public.dmhosokhuon h
 JOIN public.dmhosokhuonsp s USING(ma_khuon) WHERE h.ma_khuon=%s AND s.ma_sp=%s''',(MOLD,MATERIAL),'Warranty shots are not proven maximum life; no end-of-life date without demand/cavity/calendar contract.')
    add('label_stock_mold',[11,14],'''SELECT e->>'die_no' AS die_no,e->>'ma_khuon' AS mold,
 a.status_qc,sum((e->>'so_luong')::numeric) AS quantity,count(*) AS label_elements
 FROM public.intem_log a CROSS JOIN LATERAL jsonb_array_elements(
 CASE WHEN jsonb_typeof(a.data_tem::jsonb)='array' THEN a.data_tem::jsonb ELSE '[]'::jsonb END) e
 WHERE a.nxt=1 AND a.status='1' AND e->>'ma_vt'=%s GROUP BY 1,2,3 ORDER BY 1,2,3''',(MATERIAL,),'Current active labels; blank mold must not be silently replaced by die_no or ledger stock.')
    add('orders_totals',[12],'''SELECT count(DISTINCT h.stt_rec) AS documents,count(*) AS lines,
 sum(d.so_luong) AS quantity FROM public.ph64 h JOIN public.ct64 d USING(stt_rec)
 WHERE h.ma_kh=%s AND h.ngay_ct BETWEEN %s::date AND %s::date''',(CUSTOMER,START,END),'No join to delivery schedule, to avoid multiplying order lines; no inferred status filter.')
    add('orders_sample',[12],'''SELECT h.stt_rec,h.so_ct,h.ngay_ct,h.ma_kh,h.status,d.ln,d.ma_vt,d.dvt,d.so_luong
 FROM public.ph64 h JOIN public.ct64 d USING(stt_rec)
 WHERE h.ma_kh=%s AND h.ngay_ct BETWEEN %s::date AND %s::date
 ORDER BY h.ngay_ct DESC,h.stt_rec,d.ln LIMIT 10''',(CUSTOMER,START,END),'Sample only; counts from separate aggregate.')
    add('delivery_events',[13],'''SELECT h.stt_rec,h.so_ct,h.status,s.statusname,h.date0,h.time0,
 min(x.ngay_ct) AS first_linked_issue_date,max(x.ngay_ct) AS last_linked_issue_date,
 count(DISTINCT x.stt_rec) AS linked_issues
 FROM public.ph96 h LEFT JOIN public.sys_dmtt s ON s.ma_ct='TO2' AND s.status=h.status
 LEFT JOIN public.ct81 x ON x.stt_rec_to2=h.stt_rec
 WHERE h.so_ct=%s GROUP BY h.stt_rec,h.so_ct,h.status,s.statusname,h.date0,h.time0''',(DELIVERY,),'Creation and linked issue dates are not necessarily completion timestamp; inspect status first.')
    add('ledger_stock',[14,8],'''SELECT 'opening' AS kind,sum(ton00) AS quantity FROM public.cdvt WHERE ma_vt=%s AND nam=2026
 UNION ALL SELECT 'movement',sum(sl_nhap-sl_xuat) FROM public.ct70
 WHERE ma_vt=%s AND ngay_ct BETWEEN %s::date AND %s::date''',(MATERIAL,MATERIAL,'2026-01-01',END),'Year opening + YTD movement; does not equal current label stock.')
    add('label_qc',[15],'''SELECT a.status_qc,o.form_name,e->>'ma_lo' AS lot,
 sum((e->>'so_luong')::numeric) AS quantity FROM public.intem_log a
 CROSS JOIN LATERAL jsonb_array_elements(CASE WHEN jsonb_typeof(a.data_tem::jsonb)='array' THEN a.data_tem::jsonb ELSE '[]'::jsonb END) e
 LEFT JOIN public.sys_listoptions o ON o.form='OQC' AND o.form_type='TYPE_ST' AND o.form_value=a.status_qc::text
 WHERE a.nxt=1 AND a.status='1' AND e->>'ma_vt'=%s GROUP BY 1,2,3 ORDER BY 1,3 LIMIT 30''',(MATERIAL,),'QC names from DB dictionary, no invented locked/quarantine literals.')
    add('qc_dictionary',[15],"SELECT form_value,form_name FROM public.sys_listoptions WHERE form='OQC' AND form_type='TYPE_ST' ORDER BY form_value")
    add('price_link_candidates',[16],'''SELECT d.ma_vt,count(*) AS lines,
 count(*) FILTER(WHERE d.gia_chuan IS NULL) AS null_standard_price,
 count(*) FILTER(WHERE d.gia_chuan=0) AS zero_standard_price
 FROM public.ph64 h JOIN public.ct64 d USING(stt_rec)
 WHERE h.ma_kh=%s AND h.ngay_ct BETWEEN %s::date AND %s::date
 GROUP BY d.ma_vt HAVING bool_or(d.gia_chuan IS NULL OR d.gia_chuan=0)
 ORDER BY d.ma_vt LIMIT 30''',(CUSTOMER,START,END),'Candidates from null/zero standard price; not proof that every zero means missing link.')
    add('customer_by_name',[17],'''SELECT ma_kh,ten_kh FROM public.dmkh WHERE lower(ten_kh)=lower(%s) LIMIT 10''',('Công ty TNHH Canon Việt Nam- Chi nhánh Thăng Long',))
    add('replacement_orders',[18],'''SELECT h.so_ct,h.ma_gd,h.dien_giai,h.status,sum(d.so_luong) AS quantity
 FROM public.ph96 h JOIN public.ct96 d USING(stt_rec)
 WHERE d.ma_vt=%s AND h.ma_gd=10 AND h.ngay_ct BETWEEN %s::date AND %s::date
 GROUP BY h.so_ct,h.ma_gd,h.dien_giai,h.status ORDER BY h.so_ct LIMIT 30''',(MATERIAL,START,END),'Transaction 10 mixes NG and shortage compensation; order is not actual shipment.')
    add('return_requests',[18],'''SELECT h.so_ct,h.ma_gd,h.status,sum(d.so_luong) AS requested_quantity
 FROM public.ph66 h JOIN public.ct66 d USING(stt_rec)
 WHERE d.ma_vt=%s AND h.ngay_ct BETWEEN %s::date AND %s::date
 GROUP BY h.so_ct,h.ma_gd,h.status ORDER BY h.so_ct LIMIT 30''',(MATERIAL,START,END),'Return request is not actual goods receipt.')
    add('return_receipts',[18],'''SELECT h.so_ct,h.ma_gd,h.status,d.so_ct_rq1,
 sum(d.so_luong) AS receipt_quantity FROM public.ph76 h JOIN public.ct76 d USING(stt_rec)
 WHERE d.ma_vt=%s AND h.ngay_ct BETWEEN %s::date AND %s::date
 GROUP BY h.so_ct,h.ma_gd,h.status,d.so_ct_rq1 ORDER BY h.so_ct LIMIT 30''',(MATERIAL,START,END),'Receipt candidates; classify NG and posting status before computing outstanding compensation.')
    return out
