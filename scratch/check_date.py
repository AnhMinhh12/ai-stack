import psycopg

conn = psycopg.connect(
    host='10.0.6.2',
    port=5410,
    dbname='3SERP_HTMP_DATA',
    user='read_htmp',
    password='P@ss@Htmp@W0rd!2025',
    connect_timeout=3
)
cur = conn.cursor()
cur.execute('SELECT CURRENT_DATE, CURRENT_TIMESTAMP;')
print("Server date:", cur.fetchone())
conn.close()
