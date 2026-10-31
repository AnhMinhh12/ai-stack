"""Read-only raw evidence for a subset of the user's 18 ERP questions."""
import os
import psycopg

queries = [
    ('Q1 BOM', '''SELECT b.bom_code,b.bom_version,b.valid_from,b.valid_to,m.material_code,m.quantity,m.uom
        FROM public.mfbom b JOIN public.mfbom_material m USING (bom_code)
        WHERE b.product_code=%s ORDER BY b.bom_version,m.material_code LIMIT 30''', ('QC7-5146-000',)),
    ('Q1 production BOM', '''SELECT ma_sp,bom_version,ma_vt,ten_vt,so_luong_dm FROM public.mfkhsx_bom
        WHERE ma_sp=%s ORDER BY bom_version,ma_vt LIMIT 30''', ('QC7-5146-000',)),
    ('Q4 and Q10 shipment candidates', '''SELECT h.ma_kh, date_trunc('month',h.ngay_ct)::date,
        count(*),sum(d.so_luong),sum(d.tien2)
        FROM public.ph81 h JOIN public.ct81 d USING(stt_rec)
        WHERE d.ma_vt=%s AND ((h.ngay_ct BETWEEN %s AND %s) OR (h.ngay_ct BETWEEN %s AND %s))
        GROUP BY h.ma_kh,date_trunc('month',h.ngay_ct) ORDER BY 1,2''',
        ('QC7-5146-000','2026-09-01','2026-09-20','2026-10-01','2026-10-20')),
    ('Q5 material owner', 'SELECT ma_vt,ten_vt,ma_kh FROM public.dmvt WHERE ma_vt=%s', ('QC7-5146-000',)),
    ('Q6 ledger receipt candidates', '''SELECT count(*),sum(sl_nhap),min(ngay_ct),max(ngay_ct)
        FROM public.ct70 WHERE ma_vt=%s AND ngay_ct BETWEEN %s AND %s AND sl_nhap>0''',
        ('QC7-5146-000','2026-10-01','2026-10-20')),
    ('Q17 customer', 'SELECT ma_kh,ten_kh FROM public.dmkh WHERE ma_kh=%s', ('KH0015',)),
    ('Q9 mold counter', '''SELECT ma_khuon,ten_khuon,tong_so_shot,so_shot_bh FROM public.dmhosokhuon
        WHERE ma_khuon=%s''', ('K_QC5-2919-000-V1',)),
    ('Q12 order volume', '''SELECT count(distinct h.stt_rec),count(*),sum(d.so_luong)
        FROM public.ph64 h JOIN public.ct64 d USING(stt_rec)
        WHERE h.ma_kh=%s AND h.ngay_ct BETWEEN %s AND %s''', ('KH0015','2026-10-01','2026-10-20')),
    ('Q16 price candidates', '''SELECT count(distinct d.ma_vt),count(*) FROM public.ph64 h
        JOIN public.ct64 d USING(stt_rec) WHERE h.ma_kh=%s AND h.ngay_ct BETWEEN %s AND %s
        AND (d.gia_chuan IS NULL OR d.gia_chuan=0)''', ('KH0015','2026-10-01','2026-10-20')),
    ('Q2 effective price rows', '''SELECT d.ma_bang_gia,d.ma_kh,d.dvt,d.sl_min,d.ma_nt,d.gia,d.ngay_bd,d.ngay_kt,h.status
        FROM public.dmbanggiact d JOIN public.dmbanggia h USING(ma_bang_gia)
        WHERE d.ma_vt=%s AND d.ngay_bd<=current_date AND d.ngay_kt>=current_date
        ORDER BY d.ma_kh,d.sl_min,d.ngay_bd DESC LIMIT 30''', ('QC7-5146-000',)),
    ('Q14 ledger stock', '''SELECT ma_kho,sum(qty) FROM (
        SELECT ma_kho,ton00 AS qty FROM public.cdvt WHERE nam=extract(year from current_date) AND ma_vt=%s
        UNION ALL SELECT ma_kho,sl_nhap-sl_xuat FROM public.ct70 WHERE ma_vt=%s
        AND ngay_ct >= date_trunc('year',current_date) AND ngay_ct<=current_date) s
        GROUP BY ma_kho HAVING sum(qty)<>0 ORDER BY ma_kho''', ('QC7-5146-000','QC7-5146-000')),
    ('Q3 shipment document', '''SELECT h.ngay_ct,h.ngay_lct,h.so_ct,d.ma_lo,sum(d.so_luong)
        FROM public.ph81 h JOIN public.ct81 d USING(stt_rec)
        WHERE h.so_ct=%s AND d.ma_vt=%s GROUP BY h.ngay_ct,h.ngay_lct,h.so_ct,d.ma_lo''',
        ('001-2610-001884','QC7-5146-000')),
    ('Q8 packaging', '''SELECT dvt,packs0,packs,ma_thung,ma_khay,so_luong_vt_khay
        FROM public.dmvt WHERE ma_vt=%s''', ('QC7-5146-000',)),
    ('Q11 and Q15 label stock', '''SELECT e->>'die_no',e->>'mold',a.status_qc,count(*),sum((e->>'so_luong')::numeric)
        FROM public.intem_log a CROSS JOIN LATERAL jsonb_array_elements(
        CASE WHEN jsonb_typeof(a.data_tem::jsonb)='array' THEN a.data_tem::jsonb ELSE '[]'::jsonb END) e
        WHERE a.nxt=1 AND a.status='1' AND e->>'ma_vt'=%s GROUP BY 1,2,3 ORDER BY 1,2,3''', ('QC7-5146-000',)),
    ('Q13 delivery order', '''SELECT h.so_ct,h.status,s.statusname,h.date0,h.time0,count(x.stt_rec)
        FROM public.ph96 h LEFT JOIN public.sys_dmtt s ON s.ma_ct='TO2' AND s.status=h.status
        LEFT JOIN public.ct81 x ON x.stt_rec_to2=h.stt_rec WHERE h.so_ct=%s
        GROUP BY h.so_ct,h.status,s.statusname,h.date0,h.time0''', ('001-2610-001811',)),
    ('Q18 delivery candidate rows', '''SELECT count(*),coalesce(sum(d.so_luong),0) FROM public.ph96 h
        JOIN public.ct96 d USING(stt_rec) WHERE d.ma_vt=%s AND h.ma_gd=10 AND h.ngay_ct BETWEEN %s AND %s''',
        ('QC7-5146-000','2026-10-01','2026-10-20')),
    ('Q18 return request rows', '''SELECT count(*),coalesce(sum(d.so_luong),0) FROM public.ph66 h
        JOIN public.ct66 d USING(stt_rec) WHERE d.ma_vt=%s AND h.ngay_ct BETWEEN %s AND %s''',
        ('QC7-5146-000','2026-10-01','2026-10-20')),
]

with psycopg.connect(host=os.environ['HTMP_DB_HOST'],port=os.environ['HTMP_DB_PORT'],
                     dbname=os.environ['HTMP_DB_NAME'],user=os.environ['HTMP_DB_USER'],
                     password=os.environ['HTMP_DB_PASSWORD'],connect_timeout=5,
                     options='-c default_transaction_read_only=on -c statement_timeout=15000') as conn:
    for title, sql, params in queries:
        try:
            with conn.transaction():
                with conn.cursor() as cur:
                    cur.execute(sql, params)
                    print(title, cur.fetchall(), flush=True)
        except Exception as exc:
            print(title, 'ERROR', str(exc).splitlines()[0], flush=True)
