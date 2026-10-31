#!/usr/bin/env python3
"""Inventory visible PostgreSQL structure, without reading business records.

Run with HTMP_DB_* connection variables set. Writes JSON to stdout; do not
publish it without reviewing schema visibility and operational sensitivity.
"""
import json
import os
import sys
from datetime import datetime, timezone

import psycopg
from psycopg.rows import dict_row


def inventory():
    settings = dict(host=os.environ['HTMP_DB_HOST'], port=os.getenv('HTMP_DB_PORT', '5410'),
                    dbname=os.environ['HTMP_DB_NAME'], user=os.environ['HTMP_DB_USER'],
                    password=os.environ['HTMP_DB_PASSWORD'], connect_timeout=5,
                    row_factory=dict_row)
    with psycopg.connect(**settings) as conn:
        with conn.cursor() as cur:
            cur.execute('SET TRANSACTION READ ONLY')
            cur.execute("SET LOCAL statement_timeout = '15s'")
            cur.execute("""SELECT table_schema, table_name, table_type
                FROM information_schema.tables WHERE table_schema = 'public'
                ORDER BY table_schema, table_name""")
            tables = cur.fetchall()
            cur.execute("""SELECT table_schema, table_name, column_name, ordinal_position,
                    data_type, is_nullable
                FROM information_schema.columns WHERE table_schema = 'public'
                ORDER BY table_schema, table_name, ordinal_position""")
            columns = cur.fetchall()
            cur.execute("""SELECT tc.table_schema, tc.table_name, tc.constraint_name,
                    kcu.column_name, kcu.ordinal_position,
                    ccu.table_schema AS referenced_schema, ccu.table_name AS referenced_table,
                    ccu.column_name AS referenced_column
                FROM information_schema.table_constraints tc
                JOIN information_schema.key_column_usage kcu
                  ON tc.constraint_catalog=kcu.constraint_catalog
                 AND tc.constraint_schema=kcu.constraint_schema
                 AND tc.constraint_name=kcu.constraint_name
                JOIN information_schema.referential_constraints rc
                  ON tc.constraint_catalog=rc.constraint_catalog
                 AND tc.constraint_schema=rc.constraint_schema
                 AND tc.constraint_name=rc.constraint_name
                JOIN information_schema.key_column_usage ccu
                  ON rc.unique_constraint_catalog=ccu.constraint_catalog
                 AND rc.unique_constraint_schema=ccu.constraint_schema
                 AND rc.unique_constraint_name=ccu.constraint_name
                 AND ccu.ordinal_position=kcu.position_in_unique_constraint
                WHERE tc.constraint_type='FOREIGN KEY' AND tc.table_schema='public'
                ORDER BY tc.table_name, tc.constraint_name, kcu.ordinal_position""")
            foreign_keys = cur.fetchall()
    return {'version': 1, 'captured_at_utc': datetime.now(timezone.utc).isoformat(),
            'scope': 'public schema visible to connection role',
            'warning': 'Structural metadata only; relationships and business meanings require validation. Not an access grant.',
            'tables': tables, 'columns': columns, 'foreign_keys': foreign_keys}


def main():
    try:
        print(json.dumps(inventory(), ensure_ascii=False, indent=2))
    except (KeyError, psycopg.Error):
        # Driver errors can contain connection details; never emit credentials.
        print('Unable to inventory ERP schema; check configuration and database access.', file=sys.stderr)
        return 1
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
