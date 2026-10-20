"""Independent read-only DB probes; not a production business gold standard."""
import os,json,psycopg
cfg=dict(host=os.getenv('HTMP_DB_HOST'),port=os.getenv('HTMP_DB_PORT','5410'),dbname=os.getenv('HTMP_DB_NAME','3SERP_HTMP_DATA'),user=os.getenv('HTMP_DB_USER'),password=os.getenv('HTMP_DB_PASSWORD'),connect_timeout=5)
queries={
'material':"select ma_vt,ten_vt,ma_kh from dmvt where ma_vt='QC7-5146-000'",
'customer':"select ma_kh,ten_kh from dmkh where ma_kh='KH0034'",
'latest_delivery':"select h.stt_rec,h.so_ct,h.ngay_ct,h.ngay_lct,h.ma_kh,sum(d.so_luong) qty from ph81 h join ct81 d using(stt_rec) where d.ma_vt='QC7-5146-000' and h.ma_gd<>4 group by h.stt_rec,h.so_ct,h.ngay_ct,h.ngay_lct,h.ma_kh order by h.ngay_lct desc,h.ngay_ct desc,h.so_ct desc,h.stt_rec desc limit 3",
'sales':"select sum(d.so_luong) qty,sum(d.tien2) revenue,count(*) lines from ph81 h join ct81 d using(stt_rec) where d.ma_vt='QC7-5146-000' and h.ngay_ct between date '2026-10-01' and date '2026-10-20' and h.ma_gd<>4 and h.status in(select status from sys_dmtt where ma_ct='HDA' and post_inventory_yn=true)",
'sales_by_period':"select date_trunc('month',h.ngay_ct) period,sum(d.so_luong) qty,sum(d.tien2) revenue from ph81 h join ct81 d using(stt_rec) where d.ma_vt='QC7-5146-000' and h.ma_kh='KH0034' and ((h.ngay_ct between date '2026-09-01' and date '2026-09-20') or (h.ngay_ct between date '2026-10-01' and date '2026-10-20')) and h.ma_gd<>4 and h.status in(select status from sys_dmtt where ma_ct='HDA' and post_inventory_yn=true) group by 1 order by 1",
'mold':"select ma_khuon,tong_so_shot,so_shot_bh from dmhosokhuon where ma_khuon='K_QC5-0980-000-V2'",
'ledger_inventory':"select 'opening' kind,sum(ton00) qty from cdvt where ma_vt='QC7-5146-000' and nam=2026 union all select 'movement',sum(sl_nhap-sl_xuat) from ct70 where ma_vt='QC7-5146-000' and ngay_ct between date '2026-01-01' and date '2026-10-20'",
'label_inventory':"select a.status_qc,count(*) labels,sum((e->>'so_luong')::numeric) qty from intem_log a cross join lateral jsonb_array_elements(case when jsonb_typeof(a.data_tem::jsonb)='array' then a.data_tem::jsonb else '[]'::jsonb end) e where a.nxt=1 and a.status='1' and e->>'ma_vt'='QC7-5146-000' group by 1",
'qc_definitions':"select form_value,form_name from sys_listoptions where form='OQC' and form_type='TYPE_ST'",
'fcst_versions':"select nguon_du_lieu,count(*) row_count,count(distinct ngay_tinh_toan) versions,min(ngay_tinh_toan),max(ngay_tinh_toan) from mfkhsx_po_fc where ma_vt='QC7-5146-000' group by 1",
'price_rows':"select d.ma_kh,d.sl_min,d.gia,d.gia0,d.ma_nt,d.ngay_bd,d.ngay_kt,h.status from dmbanggiact d join dmbanggia h using(ma_bang_gia) where d.ma_vt='QC7-5146-000' order by d.ngay_bd desc limit 12",
'ng_reason_samples':"select h.ma_gd,h.dien_giai,sum(d.so_luong) qty from ph96 h join ct96 d using(stt_rec) where h.ma_gd=10 and d.ma_vt='QC7-5146-000' and h.ngay_ct between date '2026-10-01' and date '2026-10-20' group by 1,2 limit 15"
}
for name,sql in queries.items():
 out={'probe':name,'sql':sql}
 try:
  with psycopg.connect(**cfg) as c:
   c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='20s'")
   cur=c.execute(sql);out.update(columns=[x.name for x in cur.description],rows=cur.fetchmany(200))
 except Exception as e: out['error']=str(e)[:500]
 print(json.dumps(out,ensure_ascii=False,default=str),flush=True)
