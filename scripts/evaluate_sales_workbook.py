#!/usr/bin/env python3
"""Read-only operator evaluation of the CURRENT bounded agent on sales_question.xlsx.

--bundle prints a self-contained script for `docker exec -i open-webui python -`.
ERP_WORKBOOK_MODE=references runs independent SQL only; default runs all 18 AI cases.
No runtime config changes. Only the server-configured shared ERP identity is used,
and broad reference probes fail closed unless that existing identity is superuser.
"""
import asyncio
import hashlib
import json
import math
import os
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
import zipfile

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
sys.path.insert(0,str(ROOT/'scripts'))
from erp_eval.workbook_references import probes, MATERIAL, CUSTOMER, MOLD, DELIVERY, START, END


def workbook(path):
    ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
    with zipfile.ZipFile(path) as archive:
        strings=[''.join(n.itertext()) for n in ET.fromstring(archive.read('xl/sharedStrings.xml')).findall('m:si',ns)]
        rows=[]
        for row in ET.fromstring(archive.read('xl/worksheets/sheet1.xml')).findall('.//m:row',ns):
            values={}
            for cell in row.findall('m:c',ns):
                v=cell.find('m:v',ns)
                if v is not None:
                    col=''.join(c for c in cell.get('r') if c.isalpha())
                    values[col]=strings[int(v.text)] if cell.get('t')=='s' else v.text
            if values.get('A','').isdigit() and values.get('B'):
                rows.append({'id':int(values['A']),'question':values['B'],'reviewer_note':values.get('C','')})
        return rows


def parameters_for(case_id):
    # Deliberately no universal entity pool: attach only relevant entities.
    material=f'Mã hàng cần hỏi: {MATERIAL}.'
    period=f'Khoảng ngày cần hỏi: {START} đến hết {END}.'
    return {
        1:material,2:material,3:material+' Gần nhất tính đến ngày tham chiếu, không tự giới hạn tháng.',
        4:material+' '+period,5:material,6:material+' '+period,
        7:material+' So sánh bản hiện tại với bản trước; chưa có ID phiên bản.',
        8:material,9:f'Khuôn {MOLD}, đã xác nhận liên kết với mã {MATERIAL}, khách {CUSTOMER}.',
        10:material+f' Khách {CUSTOMER}; so sánh 2026-09-01..2026-09-20 với {START}..{END}.',
        11:material,12:f'Khách hàng {CUSTOMER}. '+period,
        13:f'Số lệnh giao hàng {DELIVERY}; cần thời điểm hoàn thành của lệnh này.',
        14:material,15:material,16:f'Khách hàng {CUSTOMER}. '+period,
        17:'Tên khách hàng: Công ty TNHH Canon Việt Nam- Chi nhánh Thăng Long.',
        18:material+' '+period,
    }[case_id]


def emit(value):
    print(json.dumps(value,ensure_ascii=False,default=str),flush=True)


def connection_config():
    return dict(host=os.environ['HTMP_DB_HOST'],port=os.getenv('HTMP_DB_PORT','5410'),
                dbname=os.environ['HTMP_DB_NAME'],user=os.environ['HTMP_DB_USER'],
                password=os.environ['HTMP_DB_PASSWORD'],connect_timeout=5)


def scope_check():
    import psycopg
    uid=int(os.environ['HTMP_ERP_SHARED_USER_ID'])
    with psycopg.connect(**connection_config()) as conn:
        conn.execute('SET TRANSACTION READ ONLY')
        conn.execute("SET LOCAL statement_timeout='10s'")
        row=conn.execute('SELECT user_id,coalesce(is_super,0)=1 FROM public.userinfo WHERE user_id=%s',(uid,)).fetchone()
        if not row or not row[1]:
            raise RuntimeError('Broad operator reference suite requires existing configured superuser; no identity substitution allowed')
    return uid


def references():
    import psycopg
    scope_check()
    with psycopg.connect(**connection_config()) as conn:
        conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
        conn.execute("SET LOCAL statement_timeout='15s'")
        conn.execute("SET LOCAL lock_timeout='1s'")
        at=conn.execute('SELECT current_timestamp').fetchone()[0]
        for item in probes():
            out=dict(kind='reference',at=at,**item)
            try:
                with conn.transaction():
                    cur=conn.execute(item['sql'],item['parameters'])
                    rows=cur.fetchmany(101)
                    out.update(columns=[d.name for d in cur.description],rows=rows[:100],truncated=len(rows)>100,status='ok')
            except psycopg.Error as error:
                out.update(status='error',sqlstate=error.sqlstate)
            emit(out)


async def evaluate():
    import httpx
    import psycopg
    from psycopg.rows import dict_row
    from erp_ai.agent import run_agent, Limits
    from erp_ai.agent_backend import ReportBackend
    from erp_ai.agent_runtime import QwenClient
    uid=scope_check()
    config=json.loads((ROOT/'config/erp-agent.json').read_text())
    rows=workbook(ROOT/'sales_question.xlsx')
    selected=set(os.getenv('ERP_WORKBOOK_CASES','').split(','))
    allowed_ids = [r['id'] for r in config['reports']]
    emit(dict(kind='metadata',workbook_sha256=hashlib.sha256((ROOT/'sales_question.xlsx').read_bytes()).hexdigest(),
              case_count=len(rows),model='qwen2.5-14b',mode='isolated operator harness; real DB; existing shared ERP scope',
              report_allowlist=allowed_ids,runtime_changed=False,limits=config['limits']))
    semaphore=asyncio.Semaphore(1)
    async def case(row):
        async with semaphore:
            audits=[]
            raw=[]
            async def database(sql,params,limits):
                async with await psycopg.AsyncConnection.connect(**connection_config(),row_factory=dict_row) as conn:
                    await conn.execute('SET TRANSACTION ISOLATION LEVEL REPEATABLE READ READ ONLY')
                    await conn.execute("SET LOCAL statement_timeout='10s'")
                    await conn.execute("SET LOCAL lock_timeout='1s'")
                    cursor=await conn.execute(sql,params)
                    result=await cursor.fetchmany(limits.rows+1)
                    # Independently aggregate the authorized population in the SAME snapshot.
                    # Never feed this benchmark-only aggregate back to the model.
                    if 'ct81' in sql and len(params) >= 5:
                        reference=await conn.execute('''SELECT count(*) AS total_lines,sum(d.so_luong) AS full_quantity,
 min(h.ngay_lct) AS min_date,max(h.ngay_lct) AS max_date
 FROM public.ct81 d JOIN public.ph81 h ON h.stt_rec=d.stt_rec
 WHERE upper(trim(d.ma_vt))=upper(%s) AND h.ngay_lct BETWEEN %s::date AND %s::date AND h.ma_gd<>4
 AND EXISTS(SELECT 1 FROM public.userinfo u WHERE u.user_id=%s
 AND (coalesce(u.is_super,0)=1 OR (h.ma_dvcs=ANY(string_to_array(coalesce(u.ds_branchs,''),','))
 AND d.ma_kho=ANY(string_to_array(coalesce(u.ds_stocks,''),',')))))''',(params[1],params[2],params[3],uid))
                        aggregate=await reference.fetchone()
                        audits.append(dict(material=params[1],date_from=params[2],date_to=params[3],fetched_rows=len(result),
                                           requested_limit=params[4],reference=aggregate,sql_sha256=hashlib.sha256(sql.encode()).hexdigest()))
                    return result
            backend=ReportBackend(ROOT,config,{'operator-audit':{'erp_user_id':uid,'reports':allowed_ids}},database)
            url=(os.getenv('OPENAI_API_BASE_URLS') or 'http://vllm:8000/v1').split(';')[0].rstrip('/')+'/'
            key=(os.getenv('OPENAI_API_KEYS') or os.getenv('VLLM_API_KEY','')).split(';')[0]
            async with httpx.AsyncClient(base_url=url,headers={'Authorization':'Bearer '+key},timeout=120,trust_env=False) as client:
                transport=QwenClient(client,'qwen2.5-14b')
                async def model(messages,tools):
                    msg=await transport(messages,tools);raw.append(msg);return msg
                question=row['question']+'\nThông số kiểm thử: '+parameters_for(row['id'])+' Ngày tham chiếu: '+END+'.'
                answer=await run_agent(question,user={'id':'operator-audit'},model=model,backend=backend,limits=Limits(**config['limits']))
            out=dict(kind='case',id=row['id'],question=row['question'],executed_question=question,
                     raw_model_messages=raw,db_audits=audits,**answer)
            emit(out)
            return out
    results=await asyncio.gather(*(case(r) for r in rows if selected=={''} or str(r['id']) in selected))
    latencies=sorted(r['metrics']['latency_ms'] for r in results)
    emit(dict(kind='summary',cases=len(results),answered=sum(r['status']=='answered' for r in results),
              latency_p50_ms=latencies[math.ceil(len(results)*.5)-1],latency_p95_ms=latencies[math.ceil(len(results)*.95)-1],
              db_queries=sum(r['metrics']['db_queries'] for r in results),
              tool_errors=sum(r['metrics']['tool_errors'] for r in results),
              scope='No production profile or permissions modified; not a chat-user ACL acceptance test'))


def bundle():
    import base64
    paths=[p.relative_to(ROOT).as_posix() for p in (ROOT/'erp_ai').glob('*.py')]
    paths+=['config/erp-agent.json', 'sales_question.xlsx',
            'scripts/evaluate_sales_workbook.py','scripts/erp_eval/workbook_references.py']
    paths+=[p.relative_to(ROOT).as_posix() for p in (ROOT/'docs/knowledge').glob('*.md')]
    paths+=[p.relative_to(ROOT).as_posix() for p in (ROOT/'sql/erp-reports').glob('agent-*.sql')]
    cfg=json.loads((ROOT/'config/erp-agent.json').read_text())
    paths+=[r['manifest'] for r in cfg['reports'] if 'manifest' in r]
    assets={p:base64.b64encode((ROOT/p).read_bytes()).decode() for p in paths}
    print('import base64,tempfile,pathlib,runpy,sys')
    print('assets='+repr(assets))
    print('''with tempfile.TemporaryDirectory(prefix='erp-workbook-audit-') as tmp:
 root=pathlib.Path(tmp)
 for name,data in assets.items():
  p=root/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(base64.b64decode(data))
 sys.argv=[str(root/'scripts/evaluate_sales_workbook.py')]
 runpy.run_path(sys.argv[0],run_name='__main__')''')

if __name__=='__main__':
    if '--bundle' in sys.argv: bundle()
    elif os.getenv('ERP_WORKBOOK_MODE')=='references': references()
    else: asyncio.run(evaluate())
