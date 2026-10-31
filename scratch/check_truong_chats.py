import sqlite3
import json
from datetime import datetime

conn = sqlite3.connect('/app/backend/data/webui.db')
c = conn.cursor()

# Find users
print("=== USERS ===")
c.execute("SELECT id, name, email, role FROM user WHERE name LIKE '%Trường%' OR email LIKE '%4509%' OR name LIKE '%Truong%'")
users = c.fetchall()
for u in users:
    print(u)

# Find chats for Truong
if users:
    user_ids = [u[0] for u in users]
    placeholders = ','.join('?' for _ in user_ids)
    c.execute(f"SELECT id, title, created_at, updated_at, chat FROM chat WHERE user_id IN ({placeholders}) ORDER BY updated_at DESC LIMIT 10", user_ids)
else:
    c.execute("SELECT id, title, user_id, created_at, updated_at, chat FROM chat ORDER BY updated_at DESC LIMIT 10")

chats = c.fetchall()
print(f"\n=== RECENT CHATS ({len(chats)}) ===")
for row in chats:
    chat_id = row[0]
    title = row[1]
    created = datetime.fromtimestamp(row[2]) if row[2] else None
    updated = datetime.fromtimestamp(row[3]) if row[3] else None
    chat_json = json.loads(row[4]) if row[4] else {}
    print(f"\n--- Chat: {title} (ID: {chat_id}) | Updated: {updated} ---")
    
    # Get messages
    # In Open-WebUI, chat JSON usually has 'messages' or 'history'
    history = chat_json.get('history', {})
    messages = history.get('messages', {})
    if not messages and 'messages' in chat_json:
        messages = chat_json['messages']
    
    if isinstance(messages, dict):
        for msg_id, msg in messages.items():
            role = msg.get('role')
            content = msg.get('content', '')
            timestamp = msg.get('timestamp')
            print(f"  [{role}]: {content[:200]}...")
            if msg.get('error'):
                print(f"    ERROR: {msg.get('error')}")
    elif isinstance(messages, list):
        for msg in messages:
            role = msg.get('role')
            content = msg.get('content', '')
            print(f"  [{role}]: {content[:200]}...")
            if msg.get('error'):
                print(f"    ERROR: {msg.get('error')}")
