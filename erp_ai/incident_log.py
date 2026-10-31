"""Durable, content-minimized operational events for ERP lookups."""
import logging
import os
import sqlite3
import time
from pathlib import Path

LOG = logging.getLogger('htmp.erp.incidents')

def _incident_db_path() -> Path:
    if os.getenv('HTMP_ERP_INCIDENT_DB'):
        return Path(os.environ['HTMP_ERP_INCIDENT_DB'])
    if Path('/app/backend/data').exists():
        return Path('/app/backend/data/erp-incidents.db')
    return Path('/home/admin/ai-stack/scratch/erp-incidents.db')

def record(user_id, chat_id, stage, code):
    path = _incident_db_path()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd = os.open(str(path), os.O_CREAT | os.O_WRONLY, 0o600)
        os.close(fd)
        with sqlite3.connect(str(path), timeout=3) as db:
            db.execute('CREATE TABLE IF NOT EXISTS incidents (id INTEGER PRIMARY KEY, created_at INTEGER NOT NULL, user_id TEXT NOT NULL, chat_id TEXT NOT NULL, stage TEXT NOT NULL, code TEXT NOT NULL)')
            db.execute('INSERT INTO incidents(created_at,user_id,chat_id,stage,code) VALUES (?,?,?,?,?)', (int(time.time()), str(user_id or '')[:128], str(chat_id or '')[:128], str(stage)[:64], str(code)[:64]))
        os.chmod(path, 0o600)
    except Exception:
        LOG.exception('Unable to persist ERP incident user_id=%s chat_id=%s', user_id, chat_id)

def list_incidents(limit=100):
    path = _incident_db_path()
    if not path.exists():
        return []
    with sqlite3.connect(f'file:{path}?mode=ro', uri=True, timeout=3) as db:
        db.row_factory = sqlite3.Row
        return [dict(row) for row in db.execute(
            'SELECT id, created_at, user_id, chat_id, stage, code FROM incidents ORDER BY id DESC LIMIT ?',
            (max(1, min(int(limit), 1000)),))]
