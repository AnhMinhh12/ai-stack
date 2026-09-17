Kiến trúc AI nội bộ truy vấn ERP PostgreSQL bằng ngôn ngữ tự nhiên

1. Mục tiêu

Xây dựng chatbot/AI nội bộ có thể nhận câu hỏi bằng ngôn ngữ tự nhiên và truy vấn dữ liệu ERP PostgreSQL theo cách:

Ổn định và có thể kiểm soát.

Không để LLM tự do quyết định logic nghiệp vụ.

Chỉ đọc dữ liệu ERP.

Không cho phép DDL/DML hoặc thay đổi trạng thái DB.

Cùng một ý nghĩa nghiệp vụ phải cho cùng một cách truy vấn.

Có thể mở rộng dần sang nhiều phân hệ ERP/MES.

Nguyên tắc kiến trúc cốt lõi:

Natural Language → Semantic Request → Deterministic Query → PostgreSQL → Structured Result → Natural Language Answer

Không nên lấy hướng chính là:

Natural Language → LLM sinh SQL → PostgreSQL

2. Đánh giá kiến trúc hiện tại

Phần kết nối và bảo vệ PostgreSQL hiện tại là đúng hướng.

Các điểm nên giữ:

Runtime trong container open-webui.

Connector/tool riêng cho ERP.

psycopg kết nối PostgreSQL.

Service account chỉ đọc.

Mỗi connection chạy transaction READ ONLY.

Chỉ cho phép SELECT/WITH.

Chặn DML, DDL, COPY, CALL, SET và các câu lệnh thay đổi state.

Input người dùng luôn được parameter hóa.

Có connection timeout.

Có statement timeout.

Có giới hạn số hàng trả về.

DB error phải được phân biệt với kết quả 0 rows.

Khi 0 rows, trả lại filter thực tế đã áp dụng.

Vấn đề lớn nhất không nằm ở security mà nằm ở cơ chế:

Câu hỏi chưa có router/report
→ Planner xem schema
→ LLM sinh SELECT/WITH
→ PostgreSQL

SQL hợp lệ không đồng nghĩa với kết quả nghiệp vụ đúng.

ERP có rất nhiều semantic/business rule mà schema không thể hiện đầy đủ, ví dụ:

Chứng từ nào được tính là nhập.

Chứng từ nào được tính là xuất.

Trạng thái chứng từ nào được tính.

Ngày nào là ngày hạch toán.

Kho nào đang có hiệu lực.

Dấu +/- của số lượng.

Đơn vị tính.

Join chuẩn giữa các bảng.

Điều kiện lọc bắt buộc.

Cách tính tồn đầu, nhập, xuất, tồn cuối.

Nếu chỉ đưa schema cho LLM, model có thể tạo ra SQL nhìn có vẻ hợp lý nhưng sai nghiệp vụ.

3. Kiến trúc đề xuất

Người dùng
    ↓
Open WebUI
    ↓
LLM / NLP Parser
    ↓
Structured ERP Request
    ↓
Context Resolver
    ↓
ERP Semantic Layer
    ↓
Query Router
    ├── Fixed SQL / Registered Report
    ├── Semantic Query Compiler
    └── Restricted Planner (fallback)
            ↓
PostgreSQL ERP READ ONLY
            ↓
Result Validator
            ↓
Structured ERP Result
            ↓
LLM Answer Generator
            ↓
Người dùng

LLM chỉ nên linh hoạt ở phần hiểu ngôn ngữ và trình bày kết quả.

Logic dữ liệu nghiệp vụ phải càng deterministic càng tốt.

3.1. Hướng triển khai hiện tại: Manifest-first cho báo cáo ERP

Với các màn hình/báo cáo đã định nghĩa cột, manifest là nguồn chuẩn duy nhất cho tên cột hiển thị, alias, filter và metric. Không được yêu cầu LLM hay planner tìm lại bảng/cột cho các câu hỏi đã thuộc report đó.

Ví dụ report `Nhật ký nhập xuất tồn` định nghĩa:

```text
Mã vật tư      → ma_vt      → filter trên ct70.ma_vt
Số lượng nhập  → sl_nhap    → metric SUM(ct70.sl_nhap)
Số lượng xuất  → sl_xuat    → metric SUM(ct70.sl_xuat)
Ngày chứng từ  → ngay_ct    → filter trên ct70.ngay_ct
Số chứng từ    → so_ct      → filter trên ct70.so_ct
Mã kho         → ma_kho     → filter trên ct70.ma_kho
```

Câu hỏi `Mã vật tư VGU1A532Z có số lượng xuất là bao nhiêu?` đi qua luồng cố định:

```text
Câu hỏi
  → parser lấy ma_vt=VGU1A532Z, field=sl_xuat
  → manifest xác định sl_xuat là metric
  → metric handler cố định
  → SELECT COALESCE(SUM(a.sl_xuat), 0)
       FROM public.ct70 a
       WHERE upper(trim(a.ma_vt)) = %s
  → Structured Result { summary: { sl_xuat: ... } }
```

Không có ngày, số chứng từ hoặc kho nghĩa là tổng trên toàn bộ giao dịch khớp mã vật tư. Khi người dùng cung cấp các điều kiện này, handler thêm chúng vào `WHERE` bằng parameterized query; không được âm thầm bỏ qua filter.

Các cột không được khai báo metric vẫn là trường trực tiếp của report và có thể được tra cứu theo manifest. Truy vấn chi tiết/danh sách là intent riêng; không dùng `GROUP BY` thay cho phép tổng hợp khi người dùng hỏi “bao nhiêu”.

Triển khai gồm hai artifact được version cùng nhau:

```text
config/erp-reports/<report>.json  # cột, alias, filter, metric
sql/erp-reports/<report>.sql      # SQL cố định cho report chi tiết
```

Khi deploy, SQL có thể được đặt cạnh manifest trong `data/erp-sql`; loader hỗ trợ cả layout deploy và layout repository.

4. Structured ERP Request

LLM không nên trực tiếp sinh SQL.

Ví dụ người dùng hỏi:

Cho tôi tồn kho mã VT-001 ở kho A cuối tháng 8.

LLM chỉ chuyển câu hỏi thành một request có cấu trúc:

{
  "intent": "inventory_balance",
  "filters": {
    "ma_vt": "VT-001",
    "ma_kho": "A",
    "as_of_date": "2026-08-31"
  },
  "dimensions": [],
  "metrics": [
    "opening_qty",
    "in_qty",
    "out_qty",
    "closing_qty"
  ]
}

Sau đó code nội bộ quyết định report/query nào được phép chạy.

Ví dụ:

inventory_balance
    ↓
inventory_balance_v1
    ↓
SQL cố định / query compiler
    ↓
ct70 + dmvt + ...

Như vậy cùng một ý nghĩa nghiệp vụ sẽ luôn đi qua cùng một logic dữ liệu.

5. Chia truy vấn thành 3 tầng

Tier 1 - Fixed Business Query

Dùng cho nghiệp vụ phổ biến và quan trọng.

Ví dụ:

Chi tiết chứng từ.

Nhập xuất tồn.

Tồn kho.

Nhật ký vật tư.

Doanh số.

Công nợ.

Thông tin khách hàng.

Thông tin chứng từ.

Tồn theo kho.

Doanh số theo khách hàng.

Doanh số theo vật tư.

Các query này nên dùng:

intent + entity + filters
→ query handler cố định
→ SQL cố định

Ví dụ:

document_detail
inventory_balance
inventory_ledger
material_transactions
customer_debt
sales_by_customer
sales_by_item
stock_by_warehouse

Tier 1 nên là đường chạy chính của hệ thống.

Tier 2 - Semantic Query Compiler

Không thể viết một SQL riêng cho mọi cách hỏi của người dùng.

Thay vào đó xây một semantic layer mô tả ERP.

Ví dụ:

dataset: inventory_transactions

source:
  table: ct70

dimensions:
  material:
    column: ma_vt

  warehouse:
    column: ma_kho

  voucher:
    column: so_ct

  transaction_date:
    column: ngay_ct

metrics:
  qty_in:
    expression: "..."

  qty_out:
    expression: "..."

  amount:
    expression: "..."

joins:
  material:
    table: dmvt
    on: "..."

  customer:
    table: dmkh
    on: "..."

LLM chỉ được tạo semantic query:

{
  "dataset": "inventory_transactions",
  "dimensions": ["material"],
  "metrics": ["qty_in", "qty_out"],
  "filters": {
    "warehouse": "K01"
  }
}

Sau đó query compiler sinh SQL từ semantic model.

LLM không tự quyết định:

Table nào cần join.

Join condition.

Formula metric.

Business status.

Quy tắc tính nhập/xuất/tồn.

Tier 3 - Restricted Planner

Planner chỉ dùng khi:

Không match registered report.

Không thể biểu diễn bằng semantic query hiện có.

Người dùng có quyền sử dụng query linh hoạt.

Planner vẫn phải bị giới hạn mạnh.

Ưu tiên để planner tạo semantic query spec thay vì SQL trực tiếp.

Ví dụ người dùng hỏi:

Cho tôi các giao dịch của VT-001 có số lượng trên 50, nhóm theo tháng.

Planner tạo:

{
  "dataset": "inventory_transactions",
  "dimensions": ["month"],
  "metrics": [
    "transaction_count",
    "quantity"
  ],
  "filters": {
    "ma_vt": "VT-001",
    "quantity": {
      "gt": 50
    }
  }
}

Query compiler mới sinh SQL.

SQL planner trực tiếp chỉ nên là fallback cuối cùng.

6. Entity Extraction

Tách riêng entity extractor khỏi SQL planner.

Các entity ERP phổ biến:

ma_vt
so_ct
ma_kho
ma_kh
ma_dvcs
ngay_ct
from_date
to_date
status
nhom_vt
loai_ct

Ví dụ:

"Xem phiếu CT001 của VT-001"

Entity extractor trả:

{
  "ma_vt": "VT-001",
  "so_ct": "CT001"
}

Router dùng đúng cặp điều kiện này để chọn SQL cố định.

7. Quản lý context hội thoại

Không nên chỉ gửi toàn bộ chat history cho LLM rồi yêu cầu model tự nhớ điều kiện.

Nên có ERP Conversation State riêng.

Ví dụ:

{
  "intent": "inventory_ledger",
  "filters": {
    "ma_vt": "VT-002",
    "from_date": "2026-07-01",
    "to_date": "2026-07-31"
  }
}

Ví dụ hội thoại:

User: Xem VT-001 tháng 8
User: Thế VT-002?
User: Còn tháng 7?

Không nên để LLM dựng lại toàn bộ filter sau mỗi lượt.

Thay vào đó, model chỉ trả operation:

{
  "set": {
    "date_range": "2026-07"
  },
  "keep": ["ma_vt"],
  "remove": []
}

Backend merge state một cách deterministic.

8. Pipeline xử lý chuẩn

Nên chia xử lý thành các bước rõ ràng:

1. Intent Detection
2. Entity Extraction
3. Context Resolution
4. Business Semantic Resolution
5. Query Routing
6. Query Execution
7. Result Validation
8. Answer Generation

LLM nên chủ yếu đảm nhiệm:

Intent detection.

Entity extraction.

Một phần semantic mapping.

Answer generation.

Backend/code nên đảm nhiệm:

Context merge.

Business rule.

Query selection.

SQL generation.

SQL execution.

Validation.

Pagination.

Authorization.

9. Result Validator

Result Validator là lớp rất quan trọng với ERP.

Ví dụ query tồn kho trả:

{
  "opening": 100,
  "in": 20,
  "out": 30,
  "closing": 90
}

Validator kiểm tra:

opening + in - out == closing

Nếu sai:

status = DATA_CONSISTENCY_ERROR

Không cho LLM tự giải thích kết quả sai.

Một ví dụ khác:

detail_sum = 20
aggregate = 25

Kết quả:

QUERY_VALIDATION_FAILED

Có thể thêm các validation khác:

Sum detail phải khớp aggregate.

Tồn cuối phải khớp công thức.

from_date <= to_date.

Mã vật tư phải tồn tại nếu intent yêu cầu mã bắt buộc.

Kho phải hợp lệ.

Các row phải thuộc đúng filter đã áp dụng.

10. Chuẩn hóa response từ DB

Không nên đưa raw rows trực tiếp cho LLM.

Nên chuẩn hóa response:

{
  "status": "success",
  "query": {
    "intent": "inventory_ledger",
    "filters": {
      "ma_vt": "VT-001",
      "from_date": "2026-08-01",
      "to_date": "2026-08-31"
    }
  },
  "summary": {
    "opening_qty": 100,
    "in_qty": 30,
    "out_qty": 20,
    "closing_qty": 110
  },
  "rows": [],
  "pagination": {
    "returned": 50,
    "total": 218,
    "has_more": true
  }
}

Prompt cho answer generator nên có rule:

- Không tự tính lại summary nếu backend đã tính.
- Không thay đổi filter.
- Không suy luận số liệu không có trong response.
- Nếu status != success, không trả lời như thể truy vấn thành công.
- Nếu kết quả 0 row, hiển thị filter hiệu lực.
- Nếu bị phân trang, phải nói rõ đây chưa phải toàn bộ dữ liệu.

11. Error Contract

Phải chuẩn hóa lỗi giữa connector và model.

Ví dụ:

{
  "status": "db_error",
  "error_code": "STATEMENT_TIMEOUT",
  "message": "Không thể truy vấn dữ liệu ERP tại thời điểm này."
}

Không được đổi lỗi thành:

Không tìm thấy dữ liệu.

Phân biệt rõ:

SUCCESS_WITH_DATA
SUCCESS_EMPTY
DB_ERROR
QUERY_VALIDATION_FAILED
ACCESS_DENIED
INVALID_FILTER
UNSUPPORTED_QUERY

12. Guard PostgreSQL

Giữ nguyên các guard hiện có và nên bổ sung kiểm soát ở nhiều lớp.

Database layer

Service account read-only.

Chỉ CONNECT và SELECT trên object được duyệt.

Không owner.

Không superuser.

Không quyền DDL/DML.

Connection layer

TRANSACTION READ ONLY
statement_timeout
connect_timeout

SQL Guard

Cho phép:

SELECT
WITH ... SELECT

Chặn:

INSERT
UPDATE
DELETE
MERGE
DROP
ALTER
CREATE
TRUNCATE
COPY
CALL
DO
SET
GRANT
REVOKE

Input Guard

Không bao giờ:

sql = f"SELECT ... WHERE ma_vt = '{user_input}'"

Luôn parameterized query.

13. Cấu trúc project đề xuất

erp_ai/
│
├── semantic/
│   ├── datasets/
│   │   ├── inventory.json
│   │   ├── sales.json
│   │   └── receivable.json
│   │
│   ├── metrics/
│   ├── dimensions/
│   └── joins/
│
├── intents/
│   ├── inventory_balance.py
│   ├── inventory_ledger.py
│   ├── document_detail.py
│   └── customer_debt.py
│
├── resolver/
│   ├── intent_resolver.py
│   ├── entity_resolver.py
│   ├── date_resolver.py
│   └── context_resolver.py
│
├── query/
│   ├── router.py
│   ├── compiler.py
│   ├── validator.py
│   └── executor.py
│
├── sql/
│   └── erp-reports/
│
├── manifests/
│
├── connector/
│   └── htmp_postgres_query.py
│
└── llm/
    ├── extractor.py
    └── answer_generator.py

Không nên để htmp_postgres_query.py trở thành một file chứa toàn bộ:

NLP.

Router.

Business logic.

SQL planner.

DB connector.

Context handling.

Nên giữ connector nhỏ và tách trách nhiệm.

14. File kiểm soát đề xuất

Nội dung

File

DB connection + read-only guard

connector/htmp_postgres_query.py

Intent parser

resolver/intent_resolver.py

Entity parser

resolver/entity_resolver.py

Context state

resolver/context_resolver.py

Semantic datasets

semantic/datasets/*.json

Metrics

semantic/metrics/*

Dimensions

semantic/dimensions/*

Join definitions

semantic/joins/*

Router

query/router.py

Semantic SQL compiler

query/compiler.py

Result validator

query/validator.py

SQL cố định

sql/erp-reports/*.sql

Registered reports

manifests/*.json

LLM answer formatter

llm/answer_generator.py

Regression test

tests/test_erp_report_contract.py

15. Luồng xử lý đề xuất chi tiết

User
  │
  ▼
Open WebUI
  │
  ▼
ask_erp(question, conversation_id)
  │
  ▼
Intent Resolver
  │
  ├── intent
  ├── entities
  ├── requested metrics
  └── requested dimensions
  │
  ▼
Context Resolver
  │
  ├── previous state
  ├── set filter
  ├── keep filter
  └── remove filter
  │
  ▼
Normalized ERP Request
  │
  ▼
Manifest Resolver
  │
  ├── resolve report, field, filter và metric đã đăng ký
  └── không gọi planner khi manifest đã match
  │
  ▼
Query Router
  │
  ├── Tier 1 → fixed SQL
  │
  ├── Tier 2 → semantic compiler
  │
  └── Tier 3 → restricted planner
  │
  ▼
SQL Guard
  │
  ▼
PostgreSQL READ ONLY
  │
  ▼
Structured Result
  │
  ▼
Result Validator
  │
  ▼
Answer Generator
  │
  ▼
User

16. Thứ tự triển khai đề xuất

Giai đoạn 1 - Ổn định các câu hỏi phổ biến

Ưu tiên thống kê 20-50 câu hỏi ERP được dùng nhiều nhất.

Ví dụ:

Tồn kho vật tư X hiện tại bao nhiêu?
Nhập xuất tồn của X tháng này?
Chi tiết chứng từ Y?
Phiếu Y có vật tư X không?
Lịch sử nhập xuất vật tư X?
Tồn X theo từng kho?
Doanh số khách hàng A?
Công nợ khách hàng B?

Mỗi loại ánh xạ vào intent cố định.

Với report đã có manifest, bổ sung regression test cho từng metric quan trọng: parser phải nhận đúng mã/filter, metric phải thuộc manifest, SQL phải dùng aggregate đúng (ví dụ `SUM(sl_xuat)`) và không được mất filter ngày/chứng từ/kho.

Giai đoạn 2 - Xây Semantic Layer

Tạo dictionary nghiệp vụ gồm:

Dataset.

Dimension.

Metric.

Join.

Filter.

Business rule.

Mục tiêu là giảm số lượng SQL template phải viết thủ công.

Giai đoạn 3 - Query Compiler

Compiler nhận semantic query và sinh SQL parameterized.

Ví dụ:

Semantic Query
↓
Validate dataset
↓
Validate dimension
↓
Validate metric
↓
Resolve joins
↓
Build WHERE
↓
Bind parameters
↓
Build GROUP BY
↓
Apply LIMIT
↓
SQL

Giai đoạn 4 - Context State

Tách state khỏi conversation text.

Mỗi conversation lưu:

{
  "intent": null,
  "filters": {},
  "dimensions": [],
  "metrics": []
}

Giai đoạn 5 - Result Validation

Thêm validation theo từng report/intent.

Giai đoạn 6 - Restricted Planner

Chỉ thêm planner sau khi Tier 1 + Tier 2 đã ổn định.

Không nên bắt đầu hệ thống ERP AI bằng SQL planner tự do.

17. Regression Test tối thiểu

Nên test các trường hợp:

ma_vt chứa chữ.

ma_vt chứa số.

ma_vt chứa hyphen.

ma_vt + so_ct tồn tại.

ma_vt + so_ct không tồn tại.

Follow-up kế thừa ma_vt.

Follow-up thay đổi ma_vt.

Follow-up thay đổi date range.

Follow-up remove filter.

Kết quả 0 row.

DB timeout.

DB connection error.

SQL bị từ chối bởi guard.

Query trả quá MAX_ROWS.

Pagination.

Aggregate khớp detail.

Aggregate không khớp detail.

Unsupported intent.

Quan trọng nhất là regression test từ câu hỏi tự nhiên đến intent/filter cuối cùng.

Ví dụ:

"Xem VT-001 tháng 8"

Expected:

{
  "intent": "inventory_ledger",
  "ma_vt": "VT-001",
  "from_date": "2026-08-01",
  "to_date": "2026-08-31"
}

18. Nguyên tắc để kết quả ổn định

Không để LLM sở hữu business logic

LLM không quyết định:

công thức tồn kho
join chuẩn
trạng thái chứng từ
nghiệp vụ nhập/xuất
metric
quyền truy cập

Backend sở hữu các rule này.

LLM chỉ xử lý ngôn ngữ

LLM phù hợp cho:

"phiếu này"
"mã trên"
"tháng trước"
"còn kho A?"
"thế VT-002?"

Sau đó chuyển thành dữ liệu có cấu trúc.

Deterministic càng sớm càng tốt

Sau khi hiểu được intent và entity:

LLM
↓
JSON
↓
Code deterministic

Không tiếp tục cho model quyết định pipeline.

19. Kết luận

Hướng kết nối PostgreSQL ERP hiện tại có nền tảng bảo mật tốt và có thể tiếp tục sử dụng.

Phần cần thay đổi lớn nhất là chuyển từ:

Natural Language
→ LLM sinh SQL
→ PostgreSQL

sang:

Natural Language
→ Intent + Entity + Filters
→ Semantic Layer
→ Deterministic Query
→ PostgreSQL
→ Validated Result
→ LLM trình bày

Mục tiêu cuối cùng không nên là xây một chatbot biết viết SQL, mà là xây một lớp ERP AI Query Engine có contract rõ ràng.

Tóm lại:

AI linh hoạt ở ngôn ngữ, backend cứng ở nghiệp vụ và dữ liệu.

Đây là cách phù hợp hơn để triển khai AI nội bộ cho ERP/MES khi yêu cầu chính là độ chính xác, khả năng kiểm soát và tính ổn định.