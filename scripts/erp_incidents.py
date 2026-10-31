#!/usr/bin/env python3
"""List recorded ERP incidents; run inside Open WebUI as an administrator."""
import argparse
import sqlite3

p = argparse.ArgumentParser()
p.add_argument('--db', default='/app/backend/data/erp-incidents.db')
p.add_argument('--limit', type=int, default=100)
a = p.parse_args()
with sqlite3.connect('file:' + a.db + '?mode=ro', uri=True) as db:
    for row in db.execute("SELECT datetime(created_at,'unixepoch','+7 hours'), user_id, chat_id, stage, code FROM incidents ORDER BY id DESC LIMIT ?", (max(1, min(a.limit, 1000)),)):
        print('\t'.join(map(str, row)))
