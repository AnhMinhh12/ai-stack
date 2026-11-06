# scratch/view_recent_incidents.py
import sqlite3

conn = sqlite3.connect('scratch/erp-incidents.db')
cur = conn.cursor()
cur.execute('''
    SELECT id, created_at, user_name, chat_id, user_feedback, query_text, response_text 
    FROM incidents 
    ORDER BY id DESC LIMIT 5;
''')
for r in cur.fetchall():
    print('========================================')
    print(f"Incident #{r[0]} at {r[1]} by {r[2]}")
    print(f"Chat ID: {r[3]}")
    print(f"User Feedback: {r[4]}")
    print(f"Query: {r[5]}")
    print(f"Response: {r[6]}")

conn.close()
