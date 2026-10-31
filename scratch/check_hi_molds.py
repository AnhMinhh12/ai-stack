import psycopg
import os

def connection_settings():
    return {
        "host": os.getenv("HTMP_DB_HOST"),
        "port": os.getenv("HTMP_DB_PORT", "5410"),
        "dbname": os.getenv("HTMP_DB_NAME", "3SERP_HTMP_DATA"),
        "user": os.getenv("HTMP_DB_USER"),
        "password": os.getenv("HTMP_DB_PASSWORD"),
        "connect_timeout": int(os.getenv("HTMP_DB_CONNECT_TIMEOUT_SECONDS", "5")),
    }

conn = psycopg.connect(**connection_settings())
with conn.cursor() as c:
    c.execute("SELECT DISTINCT ten_khuon FROM dmhosokhuon WHERE ten_khuon ~ '^[0-9]{2}HI' LIMIT 20")
    print("Molds matching [0-9]{2}HI:")
    for r in c.fetchall():
        print(" ", r[0])
