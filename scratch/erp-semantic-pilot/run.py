"""Offline evaluation only: no production routing changes or chat-user impersonation.
Input bundle is injected by build_bundle.py. Executes SELECT in read-only transactions.
"""
import os,json,re,time,urllib.request,concurrent.futures
import psycopg
BUNDLE = None  # replaced in bundled script
CFG=dict(host=os.getenv('HTMP_DB_HOST'),port=os.getenv('HTMP_DB_PORT','5410'),dbname=os.getenv('HTMP_DB_NAME','3SERP_HTMP_DATA'),user=os.getenv('HTMP_DB_USER'),password=os.getenv('HTMP_DB_PASSWORD'),connect_timeout=5)
BASE=(os.getenv('OPENAI_API_BASE_URLS') or 'http://vllm:8000/v1').split(';')[0].rstrip('/')
KEY=(os.getenv('OPENAI_API_KEYS') or os.getenv('VLLM_API_KEY') or '').split(';')[0]
MODEL=os.getenv('HTMP_DB_PLANNER_MODEL','qwen2.5-14b')
def query(sql):
 inspected=re.sub(r"'(?:''|[^'])*'", "''", sql)
 if re.search(r'\buserinfo\b',inspected,re.I): raise ValueError('Pilot does not accept model-chosen user identities')
 if not re.match(r'^\s*(select|with)\b',sql,re.I) or ';' in inspected.rstrip().rstrip(';') or re.search(r'\b(insert|update|delete|drop|alter|create|copy|call|do|grant|revoke|pg_sleep|dblink|pg_read_file|pg_ls_dir|set_config)\b',inspected,re.I): raise ValueError('Rejected by pilot SELECT guard')
 with psycopg.connect(**CFG) as c:
  c.execute('SET TRANSACTION READ ONLY'); c.execute("SET LOCAL statement_timeout='20s'"); c.execute("SET LOCAL lock_timeout='2s'")
  cur=c.execute(sql); rows=cur.fetchmany(201)
  return {'columns':[x.name for x in cur.description], 'rows':rows[:200], 'truncated':len(rows)>200}
def llm(prompt,tokens=1800):
 payload=dict(model=MODEL,temperature=0,max_tokens=tokens,messages=[{'role':'user','content':prompt}])
 if os.getenv('ERP_PILOT_JSON_MODE')=='1': payload['response_format']={'type':'json_object'}
 body=json.dumps(payload).encode()
 req=urllib.request.Request(BASE+'/chat/completions',data=body,headers={'Content-Type':'application/json','Authorization':'Bearer '+KEY})
 with urllib.request.urlopen(req,timeout=150) as r: content=json.load(r)['choices'][0]['message']['content']
 m=re.search(r'\{[\s\S]*\}',content)
 if not m: raise ValueError('No JSON: '+content[:200])
 return json.loads(m.group())
with psycopg.connect(**CFG) as c:
 c.execute('SET TRANSACTION READ ONLY')
 schema=c.execute("SELECT table_name,column_name,data_type FROM information_schema.columns WHERE table_schema='public' ORDER BY table_name,ordinal_position").fetchall()
CAT={}
for t,col,typ in schema: CAT.setdefault(t,[]).append(col+':'+typ)
reports=BUNDLE['reports']
index=[{'id':k,'title':v['manifest']['title'],'sources':v['manifest'].get('sources',[])} for k,v in reports.items()]
context='Ngày tham chiếu 2026-10-20. Mã hàng QC7-5146-000; khách hàng KH0034 (Canon Quế Võ); khuôn K_QC5-0980-000-V2. Khoảng thời gian nếu câu hỏi chưa điền: 2026-10-01 đến hết 2026-10-20. So sánh doanh thu: 2026-09-01..2026-09-20 với 2026-10-01..2026-10-20. Đây là kiểm toán read-only trực tiếp DB bởi người vận hành, không giả lập quyền phiên chat; không dùng user_id giả.'
def run(case):
 start=time.time(); out={'id':case['id'],'question':case['question'],'context':context,'model':MODEL}
 try:
  selection=llm('Chọn tối đa 4 báo cáo liên quan cho câu hỏi. Chỉ JSON {"reports":["id"]}.\nCâu hỏi:'+case['question']+'\nCatalog:'+json.dumps(index,ensure_ascii=False),400)
  out['selection']=selection
  titles={v['manifest']['title']:k for k,v in reports.items()}
  def selected_ids(value):
   if isinstance(value,str):
    if value in reports: yield value
    elif value in titles: yield titles[value]
   elif isinstance(value,list):
    for item in value: yield from selected_ids(item)
   elif isinstance(value,dict):
    for key,item in value.items():
     if key in reports: yield key
     yield from selected_ids(item)
  ids=list(dict.fromkeys(selected_ids(selection.get('reports',[]))))[:4]; out['retrieved_reports']=ids
  if not ids: raise ValueError('Retrieval returned no valid report IDs; this does not mean DB lacks data')
  tables=set(); knowledge=[]
  for rid in ids:
   r=reports[rid]; tables.update(r['manifest'].get('sources',[])); tables.update(re.findall(r'public\.([a-zA-Z_0-9]+)',r['sql']))
   manifest=r['manifest']
   if BUNDLE.get('semantic_notes'):
    manifest={k:v for k,v in manifest.items() if k in ('id','title','validation','sources','columns','output')}
   knowledge.append({'id':rid,'manifest':manifest,'reference_sql':r['sql']} if not BUNDLE.get('semantic_notes') else {'id':rid,'manifest':manifest})
  # Expand structural neighbors, not per-question handlers.
  for t in list(tables):
   for other in CAT:
    if other.startswith(t) and len(other)<=len(t)+3: tables.add(other)
  selected_schema={t:CAT[t] for t in sorted(tables) if t in CAT and t!='userinfo'}
  prompt='''Bạn là SQL agent ERP PostgreSQL. Trả DUY NHẤT JSON {"sql": "SELECT ..." hoặc null, "reason":"...", "limitations":[...]}. Sinh truy vấn mới cho yêu cầu, không dùng handler theo câu. Chỉ dùng bảng/cột có trong schema. Chỉ SELECT/WITH không thay đổi DB, không gọi stored function. Không truy cập userinfo. Tối đa 200 dòng. Báo cáo pending_ui_validation chỉ là gợi ý CHƯA được xác nhận. Không tự suy diễn công thức hoặc trạng thái không có bằng chứng. Thiếu dữ liệu thì trả phần trả lời được và ghi limitations; nếu không đủ để truy vấn thì sql=null. Không coi yêu cầu đổi trả là đã nhận thực tế, lệnh giao là đã giao; không coi tất cả mã giao dịch 10 là NG. Không dự đoán ngày hết tuổi thọ từ tổng demand thiếu lịch/cavity. Trạng thái/phạm vi dữ liệu theo reference phải được giữ khi có liên quan, trừ user scope: đây là kiểm toán DB bởi operator dùng tài khoản read-only, không phải endpoint người dùng. Không bịa user id. Khi cần dùng ngày và mã, dùng context đã cung cấp.\n'''+context+'\nCÂU HỎI:'+case['question']+'\nSCHEMA:'+json.dumps(selected_schema,ensure_ascii=False)+'\nKNOWLEDGE:'+json.dumps(knowledge,ensure_ascii=False)
  if BUNDLE.get('semantic_notes'):
   prompt+='\nDEFINITIONS (ưu tiên hơn suy đoán):'+BUNDLE['semantic_notes']
  for attempt in range(2):
   plan=llm(prompt); out['plan']=plan
   if not plan.get('sql'): out['status']='needs_definition'; break
   try:
    out['result']=query(plan['sql']);out['status']='executed';break
   except Exception as e:
    out.setdefault('execution_errors',[]).append(str(e)[:600]); prompt+='\nSQL trước:'+plan['sql']+'\nLỗi thật:'+str(e)[:600]+'\nSửa tên cột/SQL, không thay đổi ngữ nghĩa.';out['status']='sql_error'
 except Exception as e: out['status']='error';out['error']=str(e)[:500]
 out['seconds']=round(time.time()-start,1)
 print(json.dumps(out,ensure_ascii=False,default=str),flush=True)
cases=BUNDLE['cases']
if os.getenv('ERP_PILOT_CASES'): cases=[c for c in cases if str(c['id']) in os.environ['ERP_PILOT_CASES'].split(',')]
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool: list(pool.map(run,cases))
