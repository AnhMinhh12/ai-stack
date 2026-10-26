# Kế hoạch Qwen 14B ERP tự tra cứu, tự sửa và học từ kinh nghiệm

- Ngày lập: 26/10/2026.
- Hệ thống mục tiêu: trợ lý ERP sử dụng Qwen 14B, dữ liệu ERP PostgreSQL và giao diện hiện có.
- Trạng thái: đề xuất kiến trúc và kế hoạch triển khai; chưa phải báo cáo nghiệm thu.
- Phạm vi lần này: viết tài liệu, không sửa code, cấu hình hoặc triển khai hệ thống.

## 1. Mục tiêu

Cho phép người dùng hỏi bằng ngôn ngữ tự nhiên; hệ thống tự tìm nguồn dữ liệu, lập kế hoạch, thực hiện truy vấn, phát hiện lỗi, thử sửa và trả lời có căn cứ. Giảm việc phải mang từng câu sai sang một công cụ khác để tìm bảng, sửa truy vấn hoặc sửa code thủ công.

Hệ thống phải cải thiện khả năng xử lý câu mới bằng cách tích lũy **cách giải đã được xác minh**. Fine-tuning model là một bước riêng, chỉ thực hiện khi đã có dữ liệu sạch và bằng chứng về phần năng lực cần cải thiện.

Không đặt mục tiêu trả lời mọi câu hỏi bằng mọi giá. Với câu thiếu điều kiện hoặc thiếu định nghĩa nghiệp vụ, hệ thống phải biết hỏi làm rõ; với câu chưa đủ bằng chứng, trả phần đã xác minh và chỉ rõ giới hạn.

## 2. Đánh giá hướng đi

Hướng đi phù hợp với mục tiêu tự động hóa, nhưng điểm khó nhất là xác nhận một cách giải mới thực sự đúng trước khi tái sử dụng. SQL chạy thành công, số học đúng hoặc model tự nhận xét “đúng” đều chưa đủ chứng minh đúng nghiệp vụ.

| Thành phần | Quyết định |
|---|---|
| Quét cấu trúc DB | Thực hiện trong phạm vi được cấp quyền; tận dụng catalog hiện có |
| Xây định nghĩa nghiệp vụ | Bắt buộc; ưu tiên nguồn báo cáo ERP đã đối soát |
| Tự lập kế hoạch và truy vấn | Triển khai theo phạm vi nghiệp vụ được kiểm soát |
| Tự sửa lỗi truy vấn | Cho phép trong giới hạn thời gian, số lần và tài nguyên |
| Tự sửa sai nghiệp vụ | Chỉ kết luận khi có định nghĩa và bằng chứng đối soát |
| Lưu cách giải | Có trạng thái xác minh, phiên bản và cơ chế vô hiệu hóa |
| Training sau mỗi câu thất bại | Không thực hiện |
| Fine-tuning theo đợt | Xem xét sau khi đo riêng năng lực model |

## 3. Căn cứ và giới hạn hiện trạng

Những thành phần đã được đọc trong quá trình thảo luận:

- [Báo cáo kiểm thử 18 câu ngày 23/10/2026](../docs/evidence/ERP-CURRENT-MODEL-20261023.md).
- [Điểm vào ask_erp](../functions/htmp_postgres_query.py).
- [Router nghiệp vụ](../erp_ai/router.py).
- [Bộ điều phối agent](../erp_ai/agent.py).
- [Danh mục báo cáo và cấu hình agent](../config/erp-agent.json).
- [Bộ kiểm tra kết quả](../erp_ai/validator.py).

Báo cáo ngày 23/10 ghi nhận 3 câu đúng, 3 câu một phần/chưa đủ và 12 câu sai. Các lỗi gồm tách mất ngữ cảnh, nhận nhầm thực thể, chọn sai nghiệp vụ, kết quả bị giới hạn dòng và diễn giải thiếu căn cứ.

Code được đọc đã có thêm xử lý so với một số lỗi trong báo cáo. Vì vậy, không dùng kết quả lịch sử này để khẳng định chất lượng phiên bản hiện tại. Chưa kiểm tra lại runtime hoặc chạy lại kiểm thử trong lần viết tài liệu ngày 26/10. Nhiều báo cáo trong cấu hình đã đọc mang trạng thái `pending_ui_validation`; cần kiểm tra lại trước triển khai.

## 4. Phân biệt ba cơ chế cải thiện

| Cơ chế | Thời điểm | Nội dung thay đổi |
|---|---|---|
| Tự sửa trong lượt hỏi | Ngay khi xử lý câu hỏi | Cách hiểu, kế hoạch, tham số và truy vấn |
| Học bằng kho kinh nghiệm | Sau khi cách giải đạt kiểm chứng | Bổ sung cách giải có thể tìm và tái sử dụng |
| Fine-tuning | Theo đợt, sau đánh giá | Cập nhật trọng số model bằng dữ liệu đã chuẩn hóa |

Lỗi của một câu hỏi không tự động dẫn đến sửa code hoặc training. Không lưu số tồn, giá hay trạng thái giao dịch hiện tại thành đáp án cố định; những dữ liệu đó phải được truy vấn lại.

## 5. Bản đồ DB và kiến thức nghiệp vụ

### 5.1. Danh mục toàn DB

Lập chỉ mục cấu trúc trong phạm vi được cấp quyền: bảng, cột, kiểu dữ liệu, khóa, quan hệ khai báo, view, hàm, báo cáo và từ điển trạng thái. Khi cần, đọc mẫu dữ liệu có giới hạn để hiểu cách sử dụng trường.

Quét toàn bộ cấu trúc không có nghĩa là tải toàn bộ dữ liệu giao dịch vào prompt hoặc training. Quyền truy cập dữ liệu vẫn phải được kiểm tra theo người dùng ở thời điểm truy vấn.

### 5.2. Phạm vi đã hiểu và xác minh

Với mỗi nghiệp vụ, ghi rõ:

- Khái niệm, từ đồng nghĩa và phạm vi áp dụng.
- Nguồn dữ liệu chuẩn; mức chi tiết của mỗi dòng.
- Khóa nối và các quan hệ được phép sử dụng.
- Công thức, loại chứng từ, trạng thái và điều kiện hiệu lực.
- Đơn vị, tiền tệ, ngày tham chiếu và cách xử lý dữ liệu thiếu.
- Quy tắc đối soát, người phụ trách và bằng chứng xác nhận.

Ví dụ cần phân biệt: tồn sổ sách và tồn khả dụng; xuất kho và giao thực tế; xuất bán và giao bù NG; ngày tạo và ngày hoàn thành.

### 5.3. Nguồn đang khám phá

Quan hệ hoặc ý nghĩa do AI suy đoán phải mang trạng thái chưa xác nhận. Có thể dùng để điều tra nhưng chưa được mặc định làm cơ sở cho kết luận nghiệp vụ.

Danh mục cấu trúc có thể bao phủ rộng; việc hiểu sâu và xác minh triển khai theo từng nhóm nghiệp vụ. Không chờ hiểu toàn bộ ERP mới bắt đầu thí điểm.

## 6. Luồng xử lý một câu hỏi

```text
Người dùng hỏi
      ↓
Hiểu ý định, thực thể, thời gian, các ý và tham chiếu hội thoại
      ↓
Tìm định nghĩa nghiệp vụ và kinh nghiệm đã xác minh
      ↓
Lập kế hoạch lấy dữ liệu
      ↓
Thực thi công cụ / truy vấn chỉ đọc theo quyền người dùng
      ↓
Kiểm chứng kỹ thuật và nghiệp vụ
      ├── Đủ bằng chứng → Trả lời có nguồn và phạm vi
      ├── Lỗi có thể sửa → Sửa / tra thêm → Kiểm chứng lại
      └── Thiếu điều kiện hoặc định nghĩa → Hỏi làm rõ / trả phần đã xác minh
```

### 6.1. Hiểu yêu cầu

Tạo mô tả có cấu trúc gồm các ý cần trả lời, thực thể có kiểu, điều kiện thời gian, chỉ tiêu và mức chi tiết. Giữ liên kết giữa các vế cùng câu hỏi; không tách dấu câu rồi làm mất mã hoặc bộ lọc.

Với hội thoại nối tiếp, kế thừa điều kiện liên quan; điều kiện mới của người dùng thay thế điều kiện cũ tương ứng. Không dùng lại số liệu cũ thay cho truy vấn cần cập nhật.

### 6.2. Hai đường thực thi

- Nghiệp vụ đã có cách giải chuẩn: dùng công cụ hoặc mẫu truy vấn đã xác minh với tham số mới.
- Câu hỏi mới: tìm nguồn liên quan và lập kế hoạch mới; truy vấn tạo mới chỉ chạy qua lớp kiểm soát phía backend.

Backend phải áp dụng danh sách nguồn được phép, quyền người dùng, tham số hóa giá trị, giới hạn thời gian, số dòng và tài nguyên. Không dựa vào prompt để bảo đảm quyền hoặc tính chỉ đọc. Tài khoản/transaction chỉ đọc phải đi cùng kiểm soát câu lệnh và các hàm được phép.

### 6.3. Ví dụ kết hợp nghiệp vụ

Câu hỏi: “Mã A có đủ giao cho khách B tuần sau không?”

1. Xác định A, B và khoảng ngày.
2. Lấy nhu cầu giao còn lại trong khoảng đó.
3. Tra tồn theo định nghĩa phù hợp; kiểm tra hàng giữ chỗ hoặc nguồn nhập nếu định nghĩa yêu cầu.
4. Backend tính phần đủ/thiếu trên dữ liệu đầy đủ.
5. Trả kết quả và điều kiện tính.

Nếu chưa có định nghĩa tồn khả dụng hoặc dữ liệu hàng giữ chỗ, chỉ báo những phần đã xác minh; không dùng tổng tồn sổ sách để tự kết luận chắc chắn đủ giao.

## 7. Vòng tự sửa

| Vấn đề | Cách xử lý |
|---|---|
| Sai bảng/cột, SQL không chạy | Tra schema, sửa truy vấn rồi kiểm tra lại |
| Nhầm mã khách với mã hàng | Đối chiếu danh mục và xác định lại thực thể |
| Thiếu một ý trong câu hỏi | Bổ sung bước lấy dữ liệu cho ý còn thiếu |
| Kết quả bị cắt dòng | Tính tổng ở DB, phân trang hoặc xuất chi tiết phù hợp |
| Join gây nhân bản | Kiểm tra khóa và mức chi tiết trước khi sửa cách nối |
| Kết quả rỗng | Kiểm tra mã, nguồn và bộ lọc; không tự nới điều kiện rồi coi là đáp án gốc |
| Chưa rõ khái niệm nghiệp vụ | Tìm định nghĩa; hỏi làm rõ nếu chưa có |

Mỗi lần sửa phải ghi nhận nguyên nhân, thay đổi và kết quả kiểm tra. Không lặp lại cùng một phương án thất bại. Thiết lập ngân sách số vòng, số truy vấn và thời gian sau khi đo baseline.

Khi hết ngân sách, dừng và trình bày phần đã xác minh cùng phần chưa giải quyết. Không tạo con số thay thế để hoàn thành câu trả lời.

## 8. Bộ kiểm chứng

### 8.1. Kiểm chứng kỹ thuật

- Thực thể và bộ lọc khớp câu hỏi.
- Kết quả có đủ trường bắt buộc, đúng kiểu và đơn vị.
- Không nhân bản do nối bảng sai mức chi tiết.
- Tổng tính trên toàn bộ phạm vi, không chỉ trang đầu.
- Phân biệt số 0, NULL, không có bản ghi, thiếu quyền, truy vấn lỗi và dữ liệu chưa đầy đủ.
- Các số được trình bày có thể truy ngược tới kết quả hoặc phép tính xác định trong backend.

### 8.2. Kiểm chứng nghiệp vụ

- Đúng nguồn và công thức của chỉ tiêu được hỏi.
- Đúng loại chứng từ, trạng thái, ngày hiệu lực và phạm vi.
- Đạt các phép đối soát đã định nghĩa cho nghiệp vụ.
- Khi đối chiếu báo cáo ERP, dùng cùng điều kiện, quyền và thời điểm dữ liệu phù hợp.

Kiểm tra tổng khớp chi tiết không chứng minh nguồn được chọn đúng. Một model khác hoặc lần tự đánh giá của chính Qwen có thể hỗ trợ phát hiện vấn đề nhưng không thay thế bằng chứng nghiệp vụ độc lập.

## 9. Kho kinh nghiệm và điều kiện tiếp nhận

Mỗi kinh nghiệm lưu ý định, ví dụ diễn đạt, điều kiện bắt buộc, nguồn, định nghĩa nghiệp vụ, kế hoạch, truy vấn có tham số, phép kiểm chứng, phiên bản phụ thuộc và bằng chứng xác nhận.

| Trạng thái | Cách sử dụng |
|---|---|
| Thử nghiệm | Lưu để điều tra và đánh giá; chưa làm cách giải chuẩn |
| Đã xác minh | Được tìm và tái sử dụng trong phạm vi đã xác nhận |
| Ngừng sử dụng | Không được chọn cho câu hỏi mới; giữ lịch sử để truy vết |

Điều kiện tiếp nhận:

1. Cách giải tái sử dụng nguồn và công thức đã duyệt có thể được xét tự động bằng bộ kiểm tra đã định nghĩa, kèm kiểm thử trên nhiều tham số và trường hợp biên.
2. Quan hệ hoặc công thức nghiệp vụ mới cần người phụ trách xác nhận trước khi phổ biến.
3. Một lần SQL chạy được hoặc một phản hồi “đúng” không tự chứng minh tính tổng quát.
4. Phản hồi “sai” phải mở việc kiểm tra; tạm ngừng kinh nghiệm khi xác nhận có lỗi ảnh hưởng tái sử dụng.
5. Khi schema, báo cáo hoặc định nghĩa thay đổi, kiểm tra lại các kinh nghiệm phụ thuộc.
6. Kho kinh nghiệm không lưu dữ liệu người dùng rồi chia sẻ vượt quyền. Phân quyền áp dụng cả lúc tìm kinh nghiệm và lúc truy vấn lại dữ liệu.

## 10. Vai trò của Qwen 14B và fine-tuning

Đo riêng các năng lực trước khi quyết định training:

| Năng lực | Phép đánh giá |
|---|---|
| Hiểu câu | Nhận đúng ý định, thực thể, thời gian, các phần yêu cầu |
| Chọn nguồn | Chọn đúng báo cáo từ danh mục phù hợp |
| Lập kế hoạch | Xác định đủ bước và quan hệ phụ thuộc |
| Tạo truy vấn | Truy vấn đúng khi đã có nguồn và định nghĩa chuẩn |
| Diễn giải | Trả lời đúng khi nhận kết quả dữ liệu chuẩn |

Fine-tuning chỉ dùng dữ liệu đã xác minh để cải thiện phần năng lực còn yếu. Không dùng để ghi nhớ số liệu giao dịch hiện tại.

Quy trình: tích lũy ca sạch → chuẩn hóa và tách bộ kiểm thử độc lập → training bản ứng viên → so sánh với bản hiện tại → triển khai nếu đạt các cổng nghiệm thu. Không cho model tự tạo đáp án chưa xác nhận rồi đưa trực tiếp vào training.

## 11. Các giai đoạn triển khai

| Giai đoạn | Công việc và đầu ra | Cổng chuyển bước |
|---|---|---|
| 1. Đo hiện trạng | Xác định runtime, model, tool/filter, report; trace và phân loại lỗi của 18 câu | Có baseline gắn phiên bản và biết lỗi thuộc tầng nào |
| 2. Xây nền nghiệp vụ | Danh mục cấu trúc rộng; xác minh sâu tồn kho theo kho; bộ tham chiếu ERP | Định nghĩa, nguồn và kết quả phạm vi thí điểm được đối soát |
| 3. Tự tra và tự sửa | Điều phối nhiều bước, truy vấn có giới hạn, bộ kiểm chứng, trace | Giải được câu chưa thấy trong phạm vi; dừng đúng khi thiếu căn cứ |
| 4. Học bằng kinh nghiệm | Lưu phương án, kiểm tra tiếp nhận, quản lý phiên bản và vô hiệu hóa | Cách giải dùng được với mã/ngày khác; phương án sai không được phổ biến |
| 5. Mở rộng | Bổ sung đơn hàng, giao hàng và câu hỏi kết hợp; xem xét fine-tuning | Bản mới đạt kiểm thử độc lập và không làm suy giảm năng lực cũ |

Thí điểm từ tồn kho theo kho, sau đó mở sang đơn hàng và giao hàng. Không mở ngay toàn ERP. Tận dụng các module hiện có sau khi kiểm tra thực tế; chưa lựa chọn viết lại hệ thống.

## 12. Đánh giá và nghiệm thu

18 câu cũ là bộ hồi quy, không phải bằng chứng đủ về khả năng tổng quát. Bộ độc lập phải có cách diễn đạt, thực thể, thời gian và tổ hợp nghiệp vụ chưa dùng để chỉnh hệ thống.

Bao phủ câu nối tiếp, nhiều ý, dữ liệu rỗng, NULL, số 0, điều kiện mơ hồ, dữ liệu mâu thuẫn, kết quả bị giới hạn và câu ngoài phạm vi. Kiểm tra quyền trên đúng đường sử dụng thực tế, không chỉ tài khoản kiểm thử có quyền rộng.

Các chỉ số phải đo riêng:

- Tỷ lệ trả lời đúng và đầy đủ trong phạm vi hỗ trợ.
- Tỷ lệ khẳng định sai, đặc biệt sai chỉ tiêu, nguồn hoặc phạm vi.
- Tỷ lệ tự giải quyết và tỷ lệ phục hồi sau lỗi.
- Tỷ lệ hỏi làm rõ đúng lúc, từ chối không cần thiết và can thiệp thủ công.
- Thời gian phản hồi, số truy vấn và tác động lên DB.
- Tỷ lệ kinh nghiệm được tiếp nhận sai hoặc hết hiệu lực chưa được ngừng dùng.

Chốt ngưỡng định lượng sau baseline và trước khi triển khai thí điểm cho người dùng. Tài liệu này chưa đặt số chính xác khi chưa có số đo. Không nghiệm thu bằng việc chỉ vượt 18 câu quen thuộc hoặc tránh sai bằng cách từ chối gần hết câu mới.

## 13. Vận hành và giới hạn tự động hóa

Mỗi lượt cần lưu trace đủ để truy vết: phiên bản, ý định, nguồn được chọn, kế hoạch, lần sửa, kết quả kiểm tra và thời gian. Không cần lưu suy luận nội bộ của model; hạn chế dữ liệu nhạy cảm trong log.

Phân biệt ba phạm vi thay đổi:

- Truy vấn và kế hoạch của một lượt: được tự sửa trong giới hạn đã cấu hình.
- Kinh nghiệm dùng chung: qua cổng tiếp nhận và có thể vô hiệu hóa.
- Code, cấu hình và trọng số model: qua kiểm thử, phát hành có phiên bản và có phương án quay lại.

Có thể tắt riêng truy vấn tạo mới hoặc kinh nghiệm mới mà vẫn giữ các công cụ đã xác minh. Khi phát hiện lỗi quyền, ngừng tuyến bị ảnh hưởng; khi một cách giải sai nghiệp vụ, ngừng tái sử dụng cách giải đó và đánh giá phạm vi ảnh hưởng.

## 14. Trách nhiệm cần phân công

| Vai trò | Trách nhiệm |
|---|---|
| Chủ nghiệp vụ ERP | Chốt định nghĩa, nguồn chuẩn, trường hợp ngoại lệ và xác nhận công thức mới |
| Backend/AI | Điều phối, công cụ, kiểm chứng, quản lý kinh nghiệm và đo năng lực Qwen |
| DBA/vận hành | Quyền, giới hạn truy vấn, theo dõi tải, phiên bản runtime và phát hành |
| QA/người đối soát | Bộ câu hỏi độc lập, dữ liệu tham chiếu, đánh giá lỗi và hồi quy |

Chưa ấn định thời gian và nhân lực khi chưa hoàn thành baseline và xác định phần hiện có dùng được.

## 15. Quyết định đề xuất

Triển khai theo mô hình **Qwen 14B + bản đồ dữ liệu/nghiệp vụ + công cụ truy vấn + kiểm chứng + vòng tự sửa + kho kinh nghiệm đã xác minh**.

Mốc thành công đầu tiên: hệ thống tự xử lý được câu chưa gặp trong một phạm vi nghiệp vụ đã định nghĩa, phục hồi được lỗi có thể sửa và nhận ra khi chưa đủ căn cứ. Sau đó mới mở rộng khả năng tiếp nhận kinh nghiệm và phạm vi toàn ERP.

Phần cần con người tập trung vào xác nhận nghĩa nghiệp vụ mới và ngoại lệ thiếu dữ liệu. Mục tiêu là giảm dần số lần can thiệp nhờ những năng lực đã được chứng minh, không biến đáp án chưa kiểm chứng của model thành kiến thức dùng chung.
