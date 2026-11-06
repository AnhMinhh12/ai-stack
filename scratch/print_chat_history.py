import sqlite3
import json

conn = sqlite3.connect('/app/backend/data/webui.db')
c = conn.cursor()

cids = [
    '025cee32-e329-4e1c-b203-4d4c7f71d9a4',
    'bc95ab06-bd72-48ac-91d8-cf4952e91753',
    '5e43f73b-ced6-4555-9dc7-8d3a0da4edb9'
]

for cid in cids:
    print("=" * 80)
    print("CHAT ID:", cid)
    row = c.execute("SELECT chat FROM chat WHERE id = ?", (cid,)).fetchone()
    if row:
        d = json.loads(row[0])
        # OpenWebUI stores messages in d.get('messages') or d.get('history', {}).get('messages', {})
        history_msgs = d.get('history', {}).get('messages', {})
        if history_msgs:
            for mid, m in history_msgs.items():
                print(f"[{m.get('role')}]: {m.get('content')}")
                if m.get('tool_calls'):
                    print(f"  TOOL_CALLS: {m.get('tool_calls')}")
        else:
            msgs = d.get('messages', [])
            for m in msgs:
                print(f"[{m.get('role')}]: {m.get('content')}")
                if m.get('tool_calls'):
                    print(f"  TOOL_CALLS: {m.get('tool_calls')}")
