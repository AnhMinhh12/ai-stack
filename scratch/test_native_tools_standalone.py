from erp_ai.native_tools import ERPNativeTools

t = ERPNativeTools()

print("="*60)
print("TEST 1: Incident 29: lookup_sales_price(material_code='156279430')")
print(t.lookup_sales_price(material_code="156279430"))

print("\n" + "="*60)
print("TEST 2: Incident 28: lookup_sales_price(material_code='T1015910DA')")
print(t.lookup_sales_price(material_code="T1015910DA"))

print("\n" + "="*60)
print("TEST 3: Incident 27: lookup_inventory_stock(material_code='1014084300', warehouse_code='KHOTP00')")
print(t.lookup_inventory_stock(material_code="1014084300", warehouse_code="KHOTP00"))

print("\n" + "="*60)
print("TEST 4: Warehouse total: lookup_inventory_stock(warehouse_code='KHOTP00')")
print(t.lookup_inventory_stock(warehouse_code="KHOTP00"))

print("\n" + "="*60)
print("TEST 5: Employee lookup: lookup_general_catalog(category='employee', keyword='4509')")
print(t.lookup_general_catalog(category="employee", keyword="4509"))

print("\n" + "="*60)
print("TEST 6: Mold lookup: lookup_mold_and_mes(material_code='QC7-5146-000')")
print(t.lookup_mold_and_mes(material_code="QC7-5146-000"))
