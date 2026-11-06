import psycopg

conn = psycopg.connect(
    host="10.0.6.2",
    port="5410",
    dbname="3SERP_HTMP_DATA",
    user="read_htmp",
    password="P@ss@Htmp@W0rd!2025",
    connect_timeout=10,
)
cur = conn.cursor()

# Check function volatility
cur.execute("SELECT proname, provolatile FROM pg_proc WHERE proname = 'sys_getstartdate'")
print("sys_getstartdate volatility:", cur.fetchall(), flush=True)

# First fetch the start_date in python!
cur.execute("SELECT public.sys_getstartdate(CURRENT_DATE)")
start_date = cur.fetchone()[0]
print("Computed start_date in python:", start_date, flush=True)

conn.close()
