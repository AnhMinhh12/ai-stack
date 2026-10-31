import json

with open('scratch/real_active_tables.json') as f:
    data = json.load(f)

active = data['active_tables']
empty = data['empty_tables']

print(f"Total active tables: {len(active)}")
print(f"Total empty tables: {len(empty)}")

# Categorize into functional business groups
groups = {
    '1. MES & Vận Hành Xưởng Sản Xuất': [],
    '2. Lập Kế Hoạch Sản Xuất & BOM': [],
    '3. Bán Hàng & Đơn Hàng & Xuất Kho': [],
    '4. Mua Hàng & Nhà Cung Cấp & Nhập Kho': [],
    '5. Quản Lý Kho & Tồn Kho': [],
    '6. Khuôn, Thiết Bị, Máy Móc & Bảo Trì': [],
    '7. Quản Lý Chất Lượng (QC / IQC / OQC)': [],
    '8. Danh Mục Dữ Liệu Gốc (Master Data)': [],
    '9. Báo Cáo & Khai Báo Nghiệp Vụ ERP (dmbaocao, sys_report...)': [],
    '10. Hệ Thống, Phân Quyền, Cấu Hình & Tạm (sys_*, tmp_*, log_*)': [],
    '11. Bảng Khác': []
}

for name, rows in active:
    n = name.lower()
    if any(k in n for k in ['mes_', 'intem', 'pallet', 'data_in', 'oi_']):
        groups['1. MES & Vận Hành Xưởng Sản Xuất'].append((name, rows))
    elif any(k in n for k in ['mfkhsx', 'mfdmfc', 'bom', 'lsx', 'dxnvl']):
        groups['2. Lập Kế Hoạch Sản Xuất & BOM'].append((name, rows))
    elif any(k in n for k in ['ph64', 'ct64', 'ph81', 'ct81', 'ph84', 'ct84', 'ph85', 'ct85', 'ctkhgh', 'dmbanggia', 'so', 'ban_hang', 'dsbh', 'ct86', 'ph86', 'ct66', 'ph66', 'ct67', 'ph67']):
        groups['3. Bán Hàng & Đơn Hàng & Xuất Kho'].append((name, rows))
    elif any(k in n for k in ['ph71', 'ct71', 'ph72', 'ct72', 'ph73', 'ct73', 'ph74', 'ct74', 'ph91', 'ct91', 'ph96', 'ct96', 'bgncc', 'khnh', 'dsmh', 'po']):
        groups['4. Mua Hàng & Nhà Cung Cấp & Nhập Kho'].append((name, rows))
    elif any(k in n for k in ['cdvt', 'ct70', 'dmkho', 'dmlo', 'ctlo', 'ton_kho', 'ct77', 'ph77', 'ct76', 'ph76', 'ct94', 'ph94', 'ctdnv', 'phdnv', 'ctycn', 'phycn']):
        groups['5. Quản Lý Kho & Tồn Kho'].append((name, rows))
    elif any(k in n for k in ['khuon', 'mold', 'may', 'machine', 'thietbi', 'tbi']):
        groups['6. Khuôn, Thiết Bị, Máy Móc & Bảo Trì'].append((name, rows))
    elif any(k in n for k in ['qc', 'iqc', 'oqc', 'kcs', 'loi']):
        groups['7. Quản Lý Chất Lượng (QC / IQC / OQC)'].append((name, rows))
    elif n.startswith('dm') and not any(k in n for k in ['baocao', 'bc']):
        groups['8. Danh Mục Dữ Liệu Gốc (Master Data)'].append((name, rows))
    elif any(k in n for k in ['baocao', 'report', 'grid', 'sys_report']):
        groups['9. Báo Cáo & Khai Báo Nghiệp Vụ ERP (dmbaocao, sys_report...)'].append((name, rows))
    elif any(k in n for k in ['sys_', 'tmp_', 'temp_', 'log_', 'user', 'role', 'token', 'action']):
        groups['10. Hệ Thống, Phân Quyền, Cấu Hình & Tạm (sys_*, tmp_*, log_*)'].append((name, rows))
    else:
        groups['11. Bảng Khác'].append((name, rows))

with open('scratch/active_domain_breakdown.txt', 'w', encoding='utf-8') as f:
    for g, tbls in groups.items():
        f.write(f"\n========================================\n{g}: {len(tbls)} bảng có dữ liệu\n========================================\n")
        for name, rows in sorted(tbls, key=lambda x: x[1], reverse=True):
            f.write(f"  - {name}: {rows:,} dòng\n")

print("Domain breakdown written to scratch/active_domain_breakdown.txt")
