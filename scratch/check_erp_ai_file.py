import sys
sys.path.insert(0, '/app/backend')
import erp_ai
import erp_ai.rich_ui
print("erp_ai file:", erp_ai.__file__)
print("rich_ui file:", erp_ai.rich_ui.__file__)
with open(erp_ai.rich_ui.__file__, 'r') as f:
    c = f.read()
    print("Contains #f8fafc:", '#f8fafc' in c)
    idx = c.find('head =')
    print("Head line:", c[idx:idx+150])
