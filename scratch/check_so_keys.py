import sys, json
sys.path.insert(0, '/tmp')
from htmp_postgres_query import Tools

tool = Tools()
res = tool._sales_order_register('Bảng kê đơn hàng bán của khách hàng mã KH0047')
data = json.loads(res)
print('Keys in data:', list(data.keys()))
print('Lookup:', data.get('lookup'))
rows = data.get('rows', [])
print('Rows count:', len(rows))
if rows:
    print('Sample row keys:', list(rows[0].keys()))
    print('Sample row:', rows[0])
