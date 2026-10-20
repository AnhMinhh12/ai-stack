import os,json,psycopg
cfg=dict(host=os.getenv('HTMP_DB_HOST'),port=os.getenv('HTMP_DB_PORT','5410'),dbname=os.getenv('HTMP_DB_NAME','3SERP_HTMP_DATA'),user=os.getenv('HTMP_DB_USER'),password=os.getenv('HTMP_DB_PASSWORD'),connect_timeout=5)
queries={
 'receipt_sample':"select h.so_ct,h.ngay_ct,d.ma_kho,d.so_luong,h.user_id0 from ph74 h join ct74 d using(stt_rec) where d.ma_vt='QC7-5146-000' and h.ngay_ct between date '2026-10-01' and date '2026-10-20' order by h.ngay_ct desc,h.so_ct desc limit 5",
'order_count':"select count(distinct h.stt_rec) orders,count(*) lines,sum(d.so_luong) quantity from ph64 h join ct64 d using(stt_rec) where h.ma_kh='KH0034' and h.ngay_ct between date '2026-10-01' and date '2026-10-20'",
'price_link_columns':"select column_name,data_type from information_schema.columns where table_schema='public' and table_name='ct64' and (column_name like '%gia%' or column_name like '%price%') order by column_name",
'label_molds':"select e->>'ma_khuon' mold,e->>'die_no' die_no,sum((e->>'so_luong')::numeric) quantity from intem_log a cross join lateral jsonb_array_elements(case when jsonb_typeof(a.data_tem::jsonb)='array' then a.data_tem::jsonb else '[]'::jsonb end) e where a.nxt=1 and a.status='1' and e->>'ma_vt'='QC7-5146-000' group by 1,2",
'delivery_statuses':"select status,statusname from sys_dmtt where ma_ct='TO2' order by status",
'bom_materials':"select b.bom_code,b.bom_version,b.status,b.valid_from,b.valid_to,m.material_code,v.ten_vt,m.quantity,m.uom from mfbom b join mfbom_material m using(bom_code) left join dmvt v on v.ma_vt=m.material_code where b.product_code='QC7-5146-000' order by b.bom_version desc limit 30",
'fcst_versions':"select nguon_du_lieu,count(*) row_count,count(distinct ngay_tinh_toan) versions,min(ngay_tinh_toan),max(ngay_tinh_toan) from mfkhsx_po_fc where ma_vt='QC7-5146-000' group by 1",
'packaging':"select ma_vt,packs,packs0,ma_thung,so_luong_thung_pallet from dmvt where ma_vt='QC7-5146-000'",
'customer_material':"select ma_kh,ten_kh from dmkh where ma_kh='KH0015'",
'linked_molds':"select ma_khuon,ma_sp from dmhosokhuonsp where ma_sp='QC7-5146-000' limit 20",
'forecast_sample':"select nguon_du_lieu,ma_kh,ngay_tinh_toan,ngay_giao_hang,so_luong from mfkhsx_po_fc where ma_vt='QC7-5146-000' order by ngay_tinh_toan desc,ngay_giao_hang desc limit 5"
}
for name,sql in queries.items():
 out={'probe':name,'sql':sql}
 try:
  with psycopg.connect(**cfg) as c:
   c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='20s'");cur=c.execute(sql);out.update(columns=[x.name for x in cur.description],rows=cur.fetchmany(200))
 except Exception as e:out['error']=str(e)[:500]
 print(json.dumps(out,ensure_ascii=False,default=str),flush=True)
