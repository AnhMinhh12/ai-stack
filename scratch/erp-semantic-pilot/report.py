import collections,csv,hashlib,json,subprocess
from pathlib import Path
root=Path('docs/evidence/ERP-SEMANTIC-PILOT-20261020')
def read(name): return [json.loads(l) for l in (root/name).read_text().splitlines()]
base=sorted(read('results.jsonl'),key=lambda x:x['id'])
assert {d['id'] for d in base}==set(range(1,19)), 'Wait for all 18 cases'
notes=json.loads(Path('scratch/erp-semantic-pilot/review.json').read_text())
counts=collections.Counter(d['status'] for d in base)
lines=['# Thử nghiệm ERP SQL agent — 20/10/2026','',
'## Kết luận','',
'Luồng catalog → model sinh SQL → PostgreSQL đã được thử trực tiếp trên đủ 18 câu mẫu. Với model nội bộ `qwen2.5-14b` và cách cung cấp catalog trong bài thử này, kết quả **chưa đủ tin cậy để triển khai**. SQL chạy thành công không đồng nghĩa trả lời đúng nghiệp vụ. Hai câu 3 và 5 khớp một phần dữ liệu mẫu, nhưng vẫn có vấn đề về mức chi tiết/phạm vi. Chưa xác nhận câu nào đạt đầy đủ cả ngữ nghĩa và tính tổng quát.',
'',f'Lượt đầu: **{counts["executed"]}/18 chạy SQL thành công**; **{18-counts["executed"]}/18 không hoàn thành truy vấn** (gồm lỗi chọn catalog/JSON/SQL và một lỗi guard của harness). Đây là tỷ lệ thực thi, không phải độ chính xác.','',
'## Phương pháp và phạm vi','',
'- Đọc nội dung câu hỏi từ XLSX; không đưa ghi chú đáp án/cột màn hình của XLSX cho model.',
'- Model chọn tối đa 4 trong 82 manifest báo cáo; nhận schema thật và SQL tham chiếu, rồi tự sinh SQL. Không gọi router/handler cố định của từng câu.',
'- Chỉ dùng endpoint model nội bộ đầu tiên trong cấu hình; không gửi dữ liệu đến endpoint model bên ngoài.',
'- DB dùng tài khoản read_htmp, transaction READ ONLY, statement timeout 20 giây, tối đa 200 dòng đọc về. Không thay đổi DB hoặc cấu hình production.',
'- Đây là kiểm toán trực tiếp DB bởi operator; **không** kiểm thử phân quyền từng phiên chat. Model đã tự bịa user_id trong một số SQL mẫu: các kết quả đó bị đánh không đạt; production phải áp scope bằng backend.',
'- Tham số mẫu: mã hàng QC7-5146-000; khách KH0034; khuôn K_QC5-0980-000-V2; kỳ 01–20/10/2026, kỳ so sánh 01–20/09/2026. Các thực thể có thật nhưng không phải một bộ có quan hệ: mã hàng thuộc KH0015 và có các khuôn khác. Context chung và ngày mặc định là hạn chế của thiết kế fixture, có thể gây nhiễu; không dùng kết quả để suy rộng thành tỷ lệ chính xác của hệ thống.',
'- Đối chiếu bằng truy vấn riêng, không chạy lại cùng SQL của AI rồi tự nhận là xác minh. Chưa mở UI ERP để kiểm tra màn hình trong lượt này. DB đang hoạt động, các truy vấn không cùng một snapshot.',
'', '## Mốc dữ liệu đối chiếu trực tiếp','',
'| Nội dung | Kết quả trên DB |','|---|---|',
'| BOM mã mẫu | PS-576D; HIPS 576H GR21 PSMT VE0271-33 Nu-0215 Dim black MBB3%; BOM 1.0, trạng thái 1, hiệu lực 01/01/2023–02/11/2032 |',
'| Giá của mã mẫu | Khách KH0015; sl_min=1; gia/gia0=0.08563 USD; hiệu lực 25/09–31/12/2026; status=1. Chưa khẳng định ý nghĩa duyệt của status nếu chưa ánh xạ. |',
'| Phiếu giao gần nhất theo quy tắc handler hiện có | 001-2610-001787; 20/10/2026; tổng lượng 480 |',
'| Xuất bán 01–20/10 | Tổng lượng 82380; SUM(tien2)=157711964.104; 303 dòng; loại ma_gd=4, giữ trạng thái post_inventory_yn của HDA |',
'| Khách khai báo của mã | KH0015 — Canon Thăng Long |',
'| Khách dùng cho câu tra khách | KH0034 — Công ty TNHH Canon Việt Nam-Chi nhánh Quế Võ |',
'| Tồn theo sổ | Đầu năm 15588 + phát sinh -9548 = 6040 |',
'| Tồn tem đang hoạt động | 16420; QC=3 (OK); die_no V1=15300, V2=1120; ma_khuon trống. Không coi đây là cùng chỉ tiêu với tồn sổ. |',
'| Đóng gói | packs0=60; packs=0; ma_thung=BGTD0070; so_luong_thung_pallet=0. Không đủ xác nhận quy đổi pallet. |',
'| Khuôn mẫu | tong_so_shot=1880302; so_shot_bh=1000000. Chưa xác nhận so_shot_bh là tuổi thọ tối đa, không suy ra ngày hết tuổi thọ. |',
'| Đơn khách KH0034 trong kỳ | 5416 chứng từ; 5495 dòng trước khi nối lịch giao |',
'| Demand | Nguồn quan sát FC/SO; ngay_tinh_toan có ngày tương lai đến 2027. Không suy ra đã có lịch sử sửa phiên bản forecast chỉ từ tên cột/manifest. |',
'', '## Đánh giá từng câu — lượt đầu','', '| STT | Câu hỏi | Thực thi | Đối chiếu / nhận xét |','|---|---|---|---|']
for d in base:
 lines.append(f"| {d['id']} | {d['question'].replace('|','/')} | {d['status']} | {notes.get(str(d['id']),'Chưa đánh giá').replace('|','/')} |")
lines += ['', '## Lượt bổ sung định nghĩa dùng chung','',
'Thử lại 6 câu 1, 2, 4, 7, 14, 17 bằng cùng model, JSON mode, bỏ SQL giao diện khỏi prompt và bổ sung định nghĩa BOM/giá/doanh thu/tồn. Không thêm handler theo câu. Đây là sửa dựa trên lỗi đã thấy, không phải tập kiểm thử độc lập.',
'', '| Câu | Kết quả |', '|---|---|',
'| 1 | Parser chọn catalog gặp object thay vì string; sau sửa parser chung và chạy lại, model chọn sai nguồn và lấy mau_nhua của một khuôn không liên quan; trả chuỗi trống. |',
'| 2 | Chọn catalog không hợp lệ; ban đầu trả thiếu schema. Sau bổ sung log và kiểm tra, thấy model trả literal "id" thay vì ID báo cáo. Đây là lỗi retrieval, không phải DB không có giá. |',
'| 4 | Dùng đúng tien2 nhưng đảo ma_gd <> 4 thành = 4 và lấy ma_ct thay vì status trong subquery; trả rỗng sai. |',
'| 7 | SQL chạy, nhưng vẫn coi ngay_tinh_toan là phiên bản và trả rỗng. Chưa được xác minh về nghĩa dữ liệu. |',
'| 14 | Bịa cột ngay_chungtu; nối trực tiếp số dư và phát sinh có nguy cơ nhân bản. SQL không chạy. |',
'| 17 | So tên viết gọn bằng tên đầy đủ, vẫn trả rỗng dù khách có trong DB. |',
'', '## Hướng tiếp theo từ bằng chứng','',
'1. Tách entity resolver (mã/tên/alias và context đúng phạm vi) khỏi bộ sinh SQL; không để model tự thêm mã khách/khuôn.',
'2. Xây catalog theo dataset/metric/join/grain với quy tắc thực thi được. Các phép tính doanh thu, tồn, trạng thái phải được backend hoặc semantic views bảo đảm, không chỉ ghi bằng lời trong prompt.',
'3. Cho AI tổ hợp lọc/nhóm/so sánh/xếp hạng trên các dataset chuẩn đó; chỉ dùng SQL linh hoạt cho phần chưa biểu diễn được và phải qua kiểm tra cấu trúc/ngữ nghĩa.',
'4. Retrieval cần ID có schema ràng buộc và kiểm tra tập hợp lệ; không chấp nhận catalog rỗng như bằng chứng thiếu dữ liệu. Có thể dùng tìm kiếm metadata/reranking thay vì chỉ để model chọn từ danh sách.',
'5. Cần benchmark thêm model/cách cung cấp schema trên fixture liên kết đúng thực thể và các câu chưa dùng để chỉnh catalog. Bài thử hiện tại không tách được đầy đủ ảnh hưởng model, prompt, retrieval và fixture.',
'', '## Bằng chứng và tái chạy','',
'- [SQL, kết quả và lỗi đủ 18 câu](results.jsonl)',
'- [Truy vấn đối chiếu độc lập](reference.jsonl) và [bổ sung](reference-extra.jsonl). Probe forecast đầu tiên có lỗi alias `rows`; bản bổ sung đã chạy lại với `row_count`.',
'- [Lượt cải tiến 6 câu](improved.jsonl) và [kiểm tra lại retrieval 2 câu](retrieval-recheck.jsonl)',
'- [Hướng dẫn chạy](../../../scratch/erp-semantic-pilot/README.md)',
'', 'Lỗi riêng của harness: guard baseline nhận nhầm literal DO là lệnh DO; đã sửa cách kiểm tra string literal trong bản cải tiến. Parser retrieval ban đầu giả định danh sách string; đã bổ sung đọc ID từ object và chặn ID không hợp lệ. Những lỗi này được giữ trong log, không gán toàn bộ cho model.',
'']
(root/'report.md').write_text('\n'.join(lines))
with (root/'summary.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['id','question','execution_status','seconds','review'])
 for d in base:w.writerow([d['id'],d['question'],d['status'],d['seconds'],notes.get(str(d['id']), '')])
metadata={'workbook_sha256':hashlib.sha256(Path('sales_question.xlsx').read_bytes()).hexdigest(),'git_head':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip(),'model':'qwen2.5-14b','baseline_count':len(base),'execution_counts':dict(counts),'production_changed':False,'full_business_pass_rate':'not established'}
(root/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n')
print(json.dumps(metadata,ensure_ascii=False))
