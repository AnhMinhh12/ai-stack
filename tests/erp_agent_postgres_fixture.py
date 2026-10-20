"""Emit a psql script for a disposable, empty PostgreSQL database ONLY.

Fixture setup writes synthetic tables; agent queries run in READ ONLY transactions.
Never run this against any existing project database.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
QUERY = (ROOT/'sql/erp-reports/agent-sales-lines.sql').read_text()
RECEIPT_QUERY = (ROOT/'sql/erp-reports/agent-receipt-lines.sql').read_text()

def query(uid=12, material='TEST-A', limit=50):
    args=[str(uid), "'"+material+"'", "'2026-10-01'", "'2026-10-02'", str(limit)]
    pieces=QUERY.split('%s')
    return ''.join(p+v for p,v in zip(pieces,args))+pieces[-1]

def receipt_query(uid=12, material='TEST-A', limit=50):
    args=["'"+material+"'", "'2026-10-01'", "'2026-10-02'", str(uid), str(limit)]
    pieces=RECEIPT_QUERY.split('%s')
    return (''.join(p+v for p,v in zip(pieces,args))+pieces[-1]).strip().removesuffix(';')

print('''\nCREATE TABLE userinfo(user_id int, is_super int, ds_branchs text, ds_stocks text);
CREATE TABLE ph81(stt_rec text, ngay_lct date, ngay_ct date, so_ct text, ma_dvcs text, ma_kh text, status text, ma_gd int);
CREATE TABLE ct81(stt_rec text, ln int, ma_vt text, ma_kho text, dvt text, so_luong numeric);
INSERT INTO userinfo VALUES (12,0,'BR1','WH1'),(13,0,'',''),(14,1,'',''),(16,0,'BR1','WH2');
INSERT INTO ph81 VALUES
('A','2026-10-01','2026-10-01','DOC-A','BR1','C1','0',1),
('B','2026-10-01','2026-10-01','DOC-B','BR2','C2','0',1),
('C','2026-10-01','2026-10-01','DOC-C','BR1','C1','0',1),
('D','2026-10-01','2026-10-01','DOC-D','BR1','C1','0',4);
INSERT INTO ct81 VALUES ('A',1,'TEST-A','WH1','EA',3),('A',2,'TEST-A','WH1','EA',2),
('B',1,'TEST-A','WH1','EA',100),('C',1,'TEST-A','WH2','EA',200),('D',1,'TEST-A','WH1','EA',400);
ALTER TABLE userinfo ADD COLUMN user_name text;
UPDATE userinfo SET user_name = 'An' WHERE user_id = 12;
CREATE TABLE ct70(stt_rec text, ln int, so_ct text, ngay_ct date, date0 date, time0 text,
 ma_kho text, dvt text, sl_nhap numeric, user_id0 int, stt_rec_dc text, ln_dc int, ma_vt text, nxt int);
INSERT INTO ct70 VALUES
('R1',1,'PN-1','2026-10-01','2026-10-01','08:00','WH1','EA',2,12,'S1',1,'TEST-A',1),
('R2',1,'PN-2','2026-10-02','2026-10-02','09:00','WH1','EA',3,12,NULL,NULL,'TEST-A',1),
('R3',1,'PN-3','2026-10-02','2026-10-02','10:00','WH2','EA',100,16,NULL,NULL,'TEST-A',1),
('S1',1,'PX-1','2026-10-01','2026-10-01','07:00','WH2','EA',0,16,NULL,NULL,'TEST-A',2);
BEGIN READ ONLY;
SET LOCAL statement_timeout='2s';
''')
for label, sql, count in [
    ('branch AND warehouse',query(),2),('empty scope denies',query(13),0),
    ('explicit superuser',query(14),4),('unknown ERP user',query(15),0),
    ('other warehouse',query(16),1),('missing material',query(material='MISSING'),0),
    ('row limit',query(limit=1),1),
]:
    print("SELECT '"+label+"' AS test, 1 / ((SELECT count(*) FROM ("+sql+") q) = "+str(count)+")::int AS passed;")
for label, sql, count in [
    ('receipt warehouse scope',receipt_query(),2),
    ('receipt empty scope',receipt_query(13),0),
    ('receipt all superuser',receipt_query(14),3),
    ('receipt row limit',receipt_query(limit=1),1),
]:
    print("SELECT '"+label+"' AS test, 1 / ((SELECT count(*) FROM ("+sql+") q) = "+str(count)+")::int AS passed;")
print("SELECT 'receipt source warehouse' AS test, 1 / ((SELECT kho_xuat = 'WH2' FROM ("+receipt_query(limit=2)+") q WHERE so_ct = 'PN-1')::int) AS passed;")
print("SELECT 'receipt full summary' AS test, 1 / ((SELECT total_lines = 2 AND total_quantity = 5 FROM ("+receipt_query(limit=1)+") q)::int) AS passed;")
print('ROLLBACK;')
