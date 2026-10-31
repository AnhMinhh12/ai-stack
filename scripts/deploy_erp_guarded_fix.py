"""Deploy the audited ERP tool only when the registered version is unchanged."""
import hashlib
import sqlite3
import time
from pathlib import Path

EXPECTED = '51f263cd1db2be7de284d043cf8ad298af42161970216bd9f8f69e575c01e73d'
source = Path('/tmp/htmp_erp_guarded_source.py').read_text()
compile(source, 'htmp_postgres_query.py', 'exec')
with sqlite3.connect('/app/backend/data/webui.db', timeout=15) as db:
    db.execute('BEGIN IMMEDIATE')
    row = db.execute('SELECT content FROM tool WHERE id=?', ('htmp_postgres_query',)).fetchone()
    if not row or hashlib.sha256(row[0].encode()).hexdigest() != EXPECTED:
        raise SystemExit('Registered tool changed since audit; no update applied')
    db.execute('UPDATE tool SET content=?, updated_at=? WHERE id=?', (source, int(time.time()), 'htmp_postgres_query'))
    print('ERP tool updated with version guard')
