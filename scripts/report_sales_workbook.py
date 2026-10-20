#!/usr/bin/env python3
"""Render reviewed workbook evidence as Markdown, CSV and an XLSX (stdlib only)."""
import csv
import json
from pathlib import Path
import zipfile
from xml.sax.saxutils import escape

ROOT=Path(__file__).resolve().parents[1]
EVIDENCE=ROOT/'docs/evidence/ERP-SALES-WORKBOOK-20261020'


def xlsx(path,sheets):
    def col(number):
        result=''
        while number:
            number,r=divmod(number-1,26);result=chr(65+r)+result
        return result
    def sheet_xml(rows):
        data=[]
        for r,values in enumerate(rows,1):
            cells=[]
            for c,value in enumerate(values,1):
                text=str(value) if value is not None else ''
                cells.append(f'<c r="{col(c)}{r}" t="inlineStr" s="{1 if r==1 else 0}"><is><t xml:space="preserve">{escape(text[:32767])}</t></is></c>')
            data.append(f'<row r="{r}" ht="{30 if r==1 else 90}" customHeight="1">'+''.join(cells)+'</row>')
        end=f'{col(len(rows[0]))}{len(rows)}'
        return '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'+f'''<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><dimension ref="A1:{end}"/><sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/></sheetView></sheetViews><cols><col min="1" max="1" width="8" customWidth="1"/><col min="2" max="{len(rows[0])}" width="52" customWidth="1"/></cols><sheetData>{''.join(data)}</sheetData><autoFilter ref="A1:{end}"/></worksheet>'''
    types=['<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>','<Default Extension="xml" ContentType="application/xml"/>','<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>','<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>']
    for i in range(1,len(sheets)+1): types.append(f'<Override PartName="/xl/worksheets/sheet{i}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>')
    with zipfile.ZipFile(path,'w',zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml','<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'+''.join(types)+'</Types>')
        z.writestr('_rels/.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/></Relationships>')
        z.writestr('xl/workbook.xml','<workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><sheets>'+''.join(f'<sheet name="{escape(name)}" sheetId="{i}" r:id="rId{i}"/>' for i,(name,_) in enumerate(sheets,1))+'</sheets></workbook>')
        z.writestr('xl/_rels/workbook.xml.rels','<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'+''.join(f'<Relationship Id="rId{i}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i}.xml"/>' for i in range(1,len(sheets)+1))+f'<Relationship Id="rId{len(sheets)+1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
        z.writestr('xl/styles.xml','''<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><fonts count="2"><font><sz val="11"/><name val="Calibri"/></font><font><b/><sz val="11"/><name val="Calibri"/></font></fonts><fills count="2"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill></fills><borders count="1"><border/></borders><cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs><cellXfs count="2"><xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf><xf numFmtId="0" fontId="1" fillId="0" borderId="0" xfId="0" applyAlignment="1"><alignment vertical="top" wrapText="1"/></xf></cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>''')
        for i,(_,rows) in enumerate(sheets,1): z.writestr(f'xl/worksheets/sheet{i}.xml',sheet_xml(rows))


def main():
    results=[json.loads(l) for l in (EVIDENCE/'agent-results.jsonl').read_text().splitlines()]
    cases=sorted((r for r in results if r.get('kind')=='case'),key=lambda r:r['id'])
    assert [r['id'] for r in cases]==list(range(1,19)), 'Need all 18 completed cases'
    refs=[json.loads(l) for l in (EVIDENCE/'db-reference.jsonl').read_text().splitlines()]
    reviews=json.loads((EVIDENCE/'review.json').read_text())
    assert set(reviews)=={str(i) for i in range(1,19)}
    rows=[['STT','Câu hỏi Excel','Thông số/câu hỏi đã chạy','Agent trả lời','Trạng thái kỹ thuật','Kết luận đối soát','DB tham chiếu','Nhận xét','Nguồn đối chiếu','Latency ms','Lượt model','Lượt DB']]
    for r in cases:
        review=reviews[str(r['id'])]
        rows.append([r['id'],r['question'],r['executed_question'],r['answer'],r['status'],review['verdict'],review['db_facts'],review['assessment'],', '.join(review['reference_probes']),r['metrics']['latency_ms'],r['metrics']['rounds'],r['metrics']['db_queries']])
    with (EVIDENCE/'comparison.csv').open('w',newline='',encoding='utf-8-sig') as f:
        csv.writer(f).writerows([["'"+v if isinstance(v,str) and v.startswith(('=','+','-','@')) else v for v in row] for row in rows])
    dbrows=[['Probe','Câu liên quan','Thời điểm snapshot','SQL tham số hóa','Parameters','Columns','Rows','Lưu ý nghiệp vụ']]
    for r in refs: dbrows.append([r['name'],','.join(map(str,r['cases'])),r['at'],r['sql'],json.dumps(r['parameters'],ensure_ascii=False),json.dumps(r.get('columns'),ensure_ascii=False),json.dumps(r.get('rows'),ensure_ascii=False),r['caveat']])
    summary=next(r for r in results if r.get('kind')=='summary')
    metadata=next(r for r in results if r.get('kind')=='metadata')
    settings=[['Thuộc tính','Giá trị'],['Luồng','ERP agent mới, chỉ allowlist sales_lines; không phải toàn bộ tool ask_erp hiện hữu'],['Phương pháp','18 template Excel + tham số có quan hệ thật; không đưa cột ghi chú Excel hay SQL đối chiếu cho model'],['Quyền','Harness riêng dùng shared ERP identity đã cấu hình; không đổi grants/runtime'],['Dữ liệu','DB live READ ONLY; reference cùng snapshot; từng query agent có aggregate đối chiếu cùng snapshot riêng'],['Giới hạn','Không UI test; business correctness chấm riêng, answered không có nghĩa đúng']]
    settings += [[k,json.dumps(v,ensure_ascii=False)] for k,v in {**metadata,**summary}.items()]
    xlsx(EVIDENCE/'sales_question_doi_chieu.xlsx',[('Doi chieu 18 cau',rows),('DB references',dbrows),('Dieu kien test',settings)])
    lines=['# Đối chiếu từng câu sales_question.xlsx','', '| STT | Câu hỏi | Kết luận | DB tham chiếu | Nhận xét |','|---|---|---|---|---|']
    for r in cases:
        v=reviews[str(r['id'])]
        vals=[r['id'],r['question'],v['verdict'],v['db_facts'],v['assessment']]
        lines.append('| '+' | '.join(str(x).replace('|','/').replace('\n',' ') for x in vals)+' |')
    (EVIDENCE/'comparison.md').write_text('\n'.join(lines)+'\n')
    print(json.dumps(summary,ensure_ascii=False))

if __name__=='__main__': main()
