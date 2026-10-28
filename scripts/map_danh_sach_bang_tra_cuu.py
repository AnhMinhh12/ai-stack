#!/usr/bin/env python3
"""
Scanner & Mapper for danh-sach-bang-tra-cuu.md against live PostgreSQL catalog.
"""
import re
import os
import json
from pathlib import Path
import psycopg

ROOT = Path("/home/admin/ai-stack")
LOOKUP_FILE = ROOT / "danh-sach-bang-tra-cuu.md"

def parse_lookup_file():
    content = LOOKUP_FILE.read_text(encoding="utf-8")
    sections = re.findall(r"###\s+([^\n—\-]+)[—\-]\s*các cột\s*\n\n((?:\|[^\n]+\n)+)", content)
    tables = []
    for title, table_md in sections:
        title = title.strip()
        lines = [l.strip() for l in table_md.strip().split("\n") if l.strip()]
        cols = []
        for line in lines[2:]:  # skip header and separator
            parts = [p.strip() for p in line.split("|") if p.strip()]
            if len(parts) >= 2:
                # parts[0] is STT, parts[1] is Tên cột
                cols.append(parts[1])
        tables.append({"title": title, "columns": cols})
    return tables

def get_db_tables():
    pwd = os.getenv("HTMP_DB_PASSWORD", "P@ss@Htmp@W0rd!2025").strip('"').strip("'")
    conn = psycopg.connect(
        host=os.getenv("HTMP_DB_HOST", "10.0.6.2"),
        port=os.getenv("HTMP_DB_PORT", "5410"),
        dbname=os.getenv("HTMP_DB_NAME", "3SERP_HTMP_DATA"),
        user=os.getenv("HTMP_DB_USER", "read_htmp"),
        password=pwd,
        connect_timeout=3
    )
    cur = conn.cursor()
    cur.execute("SET statement_timeout = '3s'")
    cur.execute("SET lock_timeout = '2s'")
    cur.execute("""
        SELECT c.relname, c.relkind
        FROM pg_catalog.pg_class c
        JOIN pg_catalog.pg_namespace n ON n.oid = c.relnamespace
        WHERE n.nspname = 'public' AND c.relkind IN ('r', 'v', 'm')
        ORDER BY c.relname;
    """)
    objs = [r[0] for r in cur.fetchall()]
    conn.close()
    return objs

def main():
    print("=== Phân tích danh-sach-bang-tra-cuu.md ===", flush=True)
    tables = parse_lookup_file()
    print(f"Tổng số bảng cần tra cứu trên giao diện: {len(tables)}", flush=True)
    
    db_objs = get_db_tables()
    print(f"Tổng số đối tượng bảng/view trong DB public: {len(db_objs)}", flush=True)

    # Key known mapping dictionary between UI screen title and physical DB tables/views
    KNOWN_MAPPING = {
        "Đơn hàng (Hợp đồng)": ["ph64", "ct64", "dmkh", "dmvt"],
        "Lệnh giao hàng": ["ph96", "ct96", "dmkh", "dmvt"],
        "Phiếu xuất kho bán hàng": ["ph81", "ct81", "dmkh", "dmvt"],
        "Bảng kê phiếu xuất kho bán hàng": ["ph81", "ct81", "ct70", "dmkh", "dmvt"],
        "Bảng kê lệnh giao hàng": ["ph96", "ct96", "dmkh", "dmvt"],
        "Báo cáo tiến độ giao hàng": ["ph96", "ct96", "ph81", "ct81"],
        "Danh mục bảng giá": ["dmbanggia", "dmbanggiact", "dmkh", "dmvt"],
        "Bảng kê đơn hàng bán": ["ph64", "ct64", "dmkh", "dmvt"],
        "Tổng hợp bán hàng": ["ph81", "ct81", "dmkh", "dmvt"],
        "Doanh số bán hàng theo khách hàng": ["ph81", "ct81", "dmkh"],
        "Danh mục khách hàng": ["dmkh"],
        "Phiếu yêu cầu đổi, trả hàng bán": ["ph61", "ct61"],
        "Bảng thống kê cấp nguyên vật liệu": ["mes_oi_dong_thung", "intem_log", "ct70"],
        "Bảng kê đóng gói, đóng thùng": ["mes_oi_dong_thung", "mes_oi_dong_thung1", "intem_carton_log"],
        "Bảng kê gộp, tách thùng": ["intem_carton_log", "intem_log"],
        "Bảng kê Work Order": ["mes_oi_rework", "mfkhsx", "mes_scheduling"],
        "Bảng kê bổ sung shot": ["mes_oi_bo_shot", "dmhosokhuon"],
    }

    matched_count = 0
    summary = []
    for idx, t in enumerate(tables, 1):
        title = t["title"]
        cols = t["columns"]
        db_sources = KNOWN_MAPPING.get(title, [])
        status = "MATCHED_DIRECT" if db_sources else "CANDIDATE_SEARCH"
        if db_sources:
            matched_count += 1
        summary.append({
            "stt": idx,
            "title": title,
            "cols_count": len(cols),
            "db_sources": db_sources,
            "status": status
        })
        print(f"[{idx:02d}] {title} ({len(cols)} cột UI) -> DB: {', '.join(db_sources) if db_sources else 'Đang quét ứng viên'}")

    print(f"\nĐã khớp nguồn trực tiếp: {matched_count}/{len(tables)} bảng.", flush=True)

    # Save summary report to JSON
    out_path = ROOT / "docs" / "mapping_danh_sach_tra_cuu.json"
    out_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Đã lưu kết quả khảo sát sơ bộ vào: {out_path}", flush=True)

if __name__ == "__main__":
    main()
