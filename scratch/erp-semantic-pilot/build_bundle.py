import os,json,zipfile,xml.etree.ElementTree as E
from pathlib import Path
z=zipfile.ZipFile('sales_question.xlsx'); ns={'m':'http://schemas.openxmlformats.org/spreadsheetml/2006/main'}
strings=[''.join(x.itertext()) for x in E.fromstring(z.read('xl/sharedStrings.xml')).findall('m:si',ns)]
cases=[]
for row in E.fromstring(z.read('xl/worksheets/sheet1.xml')).findall('.//m:row',ns):
 vals={}
 for c in row.findall('m:c',ns):
  v=c.find('m:v',ns)
  if v is not None: vals[''.join(filter(str.isalpha,c.get('r')))]=strings[int(v.text)] if c.get('t')=='s' else v.text
 if 'A' in vals and 'B' in vals: cases.append({'id':int(vals['A']),'question':vals['B']})
reports={}
for p in Path('config/erp-reports').glob('*.json'):
 d=json.loads(p.read_text()); q=Path('sql/erp-reports')/d.get('query_file','missing')
 if q.is_file(): reports[d['id']]={'manifest':d,'sql':q.read_text()}
bundle={'cases':cases,'reports':reports}
if os.getenv('ERP_PILOT_NOTES'):
 bundle['semantic_notes']=Path(os.environ['ERP_PILOT_NOTES']).read_text()
src=Path('scratch/erp-semantic-pilot/run.py').read_text().replace('BUNDLE = None  # replaced in bundled script','BUNDLE = '+repr(bundle))
Path('/tmp/erp-semantic-pilot-run.py').write_text(src)
print('Bundled',len(cases),'questions;',len(reports),'reports')
