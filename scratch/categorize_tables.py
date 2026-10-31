import json

with open('scratch/active_tables_audit.json') as f:
    data = json.load(f)

categories = {
    '1. MES & Sản Xuất (OI, Tem, Thùng, Line Stop, Pallet, Máy)': [],
    '2. Kế Hoạch Sản Xuất & BOM (mfkhsx_*, mfdmfc*, lsx)': [],
    '3. Bán Hàng & Xuất Hàng (ph64, ct64, ph81, ct81, ct85, ctkhgh...)': [],
    '4. Mua Hàng & Nhà Cung Cấp (ph71, ct71, ph72, ct72, ph74, ct74...)': [],
    '5. Kho Vận & Tồn Kho (cdvt*, ct70*, dmkho, dmlo, ctlo...)': [],
    '6. Khuôn, Thiết Bị & Bảo Trì (dmhosokhuon, thongtin_khuon...)': [],
    '7. Danh Mục Master Data (dmvt, dmkh, dmnv, dmbanggia...)': [],
    '8. Hệ Thống, Log & Khác': []
}

for item in data:
    t = item['table']
    r = item['rows']
    if any(k in t for k in ['mes_', 'intem', 'data_in', 'pallet']):
        categories['1. MES & Sản Xuất (OI, Tem, Thùng, Line Stop, Pallet, Máy)'].append((t, r))
    elif any(k in t for k in ['mfkhsx', 'mfdmfc', 'bom', 'lsx']):
        categories['2. Kế Hoạch Sản Xuất & BOM (mfkhsx_*, mfdmfc*, lsx)'].append((t, r))
    elif t in ('ph64', 'ct64', 'ph81', 'ct81', 'ph85', 'ct85', 'ctkhgh', 'ph84', 'ct84', 'ct81tem', 'ct81ccdc', 'ct81th', 'ph88', 'ct88') or 'ban_hang' in t:
        categories['3. Bán Hàng & Xuất Hàng (ph64, ct64, ph81, ct81, ct85, ctkhgh...)'].append((t, r))
    elif t in ('ph71', 'ct71', 'ph72', 'ct72', 'ph73', 'ct73', 'ph74', 'ct74', 'ph91', 'ct91', 'ph96', 'ct96', 'ct96lo') or t.startswith('po'):
        categories['4. Mua Hàng & Nhà Cung Cấp (ph71, ct71, ph72, ct72, ph74, ct74...)'].append((t, r))
    elif t.startswith('cdvt') or t.startswith('ct70') or t in ('dmkho', 'dmlo', 'ctlo', 'ctlo_check_hil'):
        categories['5. Kho Vận & Tồn Kho (cdvt*, ct70*, dmkho, dmlo, ctlo...)'].append((t, r))
    elif 'khuon' in t or 'mold' in t or 'may' in t or 'machine' in t:
        categories['6. Khuôn, Thiết Bị & Bảo Trì (dmhosokhuon, thongtin_khuon...)'].append((t, r))
    elif t.startswith('dm') or t.startswith('dmbang'):
        categories['7. Danh Mục Master Data (dmvt, dmkh, dmnv, dmbanggia...)'].append((t, r))
    else:
        categories['8. Hệ Thống, Log & Khác'].append((t, r))

report = []
for cat, tbls in categories.items():
    report.append(f"### {cat} ({len(tbls)} bảng)")
    for t, r in sorted(tbls, key=lambda x: x[1], reverse=True):
        report.append(f"- `{t}`: **{r:,}** dòng")
    report.append("")

output_text = "\n".join(report)
print(output_text[:3000])
with open('scratch/categorized_report.md', 'w') as f:
    f.write(output_text)
