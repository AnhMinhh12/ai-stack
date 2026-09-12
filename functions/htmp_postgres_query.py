"""
title: Tra cứu PostgreSQL ERP
author: HTMP Platform
version: 1.2.0
required_open_webui_version: 0.6.0
"""

"""Global Open WebUI tools for natural-language, read-only ERP lookup."""

import json
import os
import re
from datetime import date, datetime
from decimal import Decimal
from typing import Any

MAX_ROWS = int(os.getenv("HTMP_DB_MAX_ROWS", "200"))
MAX_SCHEMA_TABLES = int(os.getenv("HTMP_DB_MAX_SCHEMA_TABLES", "100"))
TIMEOUT_MS = int(os.getenv("HTMP_DB_STATEMENT_TIMEOUT_MS", "15000"))
READ_QUERY = re.compile(r"^\s*(?:select|with)\b", re.I | re.S)
FORBIDDEN = re.compile(r"\b(?:insert|update|delete|merge|alter|drop|create|grant|revoke|copy|call|do|vacuum|analyze|truncate|listen|notify|execute|prepare|deallocate|set|show|reset|discard|lock)\b", re.I)


def json_value(value: Any) -> Any:
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, bytes):
        return value.hex()
    return value


def connection_settings() -> dict:
    settings = {
        "host": os.getenv("HTMP_DB_HOST"),
        "port": os.getenv("HTMP_DB_PORT", "5410"),
        "dbname": os.getenv("HTMP_DB_NAME", "3SERP_HTMP_DATA"),
        "user": os.getenv("HTMP_DB_USER"),
        "password": os.getenv("HTMP_DB_PASSWORD"),
        "connect_timeout": int(os.getenv("HTMP_DB_CONNECT_TIMEOUT_SECONDS", "5")),
    }
    if not settings["host"] or not settings["user"] or not settings["password"]:
        raise RuntimeError("Database connection is not configured")
    return settings


class Tools:
    def get_erp_schema(self, search: str = "") -> str:
        """Tìm bảng và cột ERP trước khi trả lời câu hỏi tự nhiên.

        Luôn gọi tool này trước khi tạo SQL, nhất là khi chưa chắc tên bảng hoặc
        cột. ``search`` là từ khóa tiếng Việt/tên nghiệp vụ để lọc; để trống sẽ
        lấy danh sách bảng đầu tiên. Không trả dữ liệu nghiệp vụ.
        """
        pattern = "%" + (search or "").strip() + "%"
        sql = """
            SELECT table_schema, table_name,
                   json_agg(json_build_object('name', column_name, 'type', data_type)
                            ORDER BY ordinal_position) AS columns
            FROM information_schema.columns
            WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
              AND (%s = '%%' OR table_name ILIKE %s OR column_name ILIKE %s)
            GROUP BY table_schema, table_name
            ORDER BY table_schema, table_name
            LIMIT %s
        """
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute(sql, (pattern, pattern, pattern, MAX_SCHEMA_TABLES))
                    rows = cursor.fetchall()
        except Exception:
            return "Không thể đọc cấu trúc DB. Kiểm tra cấu hình và quyền SELECT của tài khoản DB."
        return json.dumps(
            [{"schema": schema, "table": table, "columns": columns} for schema, table, columns in rows],
            ensure_ascii=False,
            default=str,
        )


    def _lookup_material_locations(self, value: str, lookup_column: str) -> str:
        """Look up real ERP material/warehouse fields without guessing table names."""
        needle = (value or "").strip()
        if not needle:
            return "Cần cung cấp mã vật tư hoặc mã kho để tra cứu."
        try:
            import psycopg
            from psycopg import sql
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute(
                        """
                        SELECT table_schema, table_name
                        FROM information_schema.columns
                        WHERE table_schema NOT IN ('pg_catalog', 'information_schema')
                          AND column_name IN ('ma_vt', 'ma_kho')
                        GROUP BY table_schema, table_name
                        HAVING count(DISTINCT column_name) = 2
                        ORDER BY
                          CASE table_name
                            WHEN 'cdvt13' THEN 0
                            WHEN 'cdvt' THEN 1
                            WHEN 'cdbsp' THEN 2
                            ELSE 3
                          END,
                          table_schema, table_name
                        LIMIT 12
                        """
                    )
                    tables = cursor.fetchall()
                    matches = []
                    seen = set()
                    for schema, table in tables:
                        query = sql.SQL(
                            "SELECT DISTINCT {warehouse}, {material} FROM {table} "
                            "WHERE upper(trim({lookup})) = upper(trim(%s)) LIMIT %s"
                        ).format(
                            warehouse=sql.Identifier("ma_kho"),
                            material=sql.Identifier("ma_vt"),
                            table=sql.Identifier(schema, table),
                            lookup=sql.Identifier(lookup_column),
                        )
                        cursor.execute(query, (needle, MAX_ROWS + 1))
                        rows = cursor.fetchmany(MAX_ROWS + 1)
                        for warehouse, material in rows[:MAX_ROWS]:
                            key = (warehouse, material)
                            if key in seen:
                                continue
                            seen.add(key)
                            matches.append({"source_table": f"{schema}.{table}", "ma_kho": warehouse, "ma_vt": material})
                            if len(matches) >= MAX_ROWS:
                                break
                        if len(matches) >= MAX_ROWS:
                            break
        except Exception:
            return "Không thể tra cứu cơ sở dữ liệu ERP. Kiểm tra cấu hình và quyền SELECT của tài khoản DB."
        return json.dumps(
            {"lookup": {lookup_column: needle}, "row_count": len(matches), "truncated": len(matches) >= MAX_ROWS, "rows": matches},
            ensure_ascii=False,
            default=str,
        )

    def find_material_by_code(self, ma_vt: str) -> str:
        """Tra kho chứa một mã vật tư ERP bằng cột thật ma_vt và ma_kho.

        Dùng ĐẦU TIÊN cho câu hỏi như "mã này ở kho nào?". Không tự đoán bảng
        hay viết SQL; hàm tự tìm tất cả bảng có đồng thời ma_vt và ma_kho.
        """
        return self._lookup_material_locations(ma_vt, "ma_vt")

    def find_materials_in_warehouse(self, ma_kho: str) -> str:
        """Liệt kê mã vật tư (ma_vt) của một kho ERP bằng cột thật ma_kho.

        Dùng ĐẦU TIÊN cho câu hỏi như "kho X có những mã vật tư nào?". Không tự
        đoán bảng hay viết SQL; hàm tự tìm tất cả bảng có ma_vt và ma_kho.
        """
        return self._lookup_material_locations(ma_kho, "ma_kho")

    def query_erp_database(self, sql: str) -> str:
        """Chạy đúng một SELECT/WITH chỉ đọc trên ERP, tối đa 200 dòng.

        Chỉ gọi sau ``get_erp_schema`` để dùng đúng tên bảng/cột. Tool này được
        model dùng nội bộ để trả lời câu hỏi tiếng Việt; người dùng không cần SQL.
        """
        query = (sql or "").strip().removesuffix(";").rstrip()
        if not query or ";" in query or not READ_QUERY.match(query):
            return "Chỉ chấp nhận đúng một câu lệnh SELECT hoặc WITH."
        if FORBIDDEN.search(query) or re.search(r"\bselect\b[\s\S]*\binto\b", query, re.I):
            return "Câu lệnh chứa thao tác không được phép. Tool này chỉ đọc dữ liệu."
        try:
            import psycopg
            with psycopg.connect(**connection_settings(), autocommit=False) as conn:
                with conn.cursor() as cursor:
                    cursor.execute("SET TRANSACTION READ ONLY")
                    cursor.execute("SELECT set_config('statement_timeout', %s, true)", (str(TIMEOUT_MS),))
                    cursor.execute("SELECT * FROM (" + query + ") AS htmp_result LIMIT %s", (MAX_ROWS + 1,))
                    columns = [item.name for item in cursor.description]
                    rows = cursor.fetchmany(MAX_ROWS + 1)
        except Exception:
            return "Không thể truy vấn cơ sở dữ liệu. Kiểm tra cấu hình và quyền SELECT của tài khoản DB."
        result = [dict(zip(columns, (json_value(value) for value in row))) for row in rows[:MAX_ROWS]]
        return json.dumps({"row_count": len(result), "truncated": len(rows) > MAX_ROWS, "rows": result}, ensure_ascii=False, default=str)
