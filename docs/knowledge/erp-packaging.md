# Quy cách đóng gói vật tư sản phẩm

## Nguồn và dữ liệu
Thông tin quy cách đóng gói lưu tại danh mục vật tư `public.dmvt`.
Bao gồm:
- `packs0`: số lượng vật tư trên 1 thùng tiêu chuẩn.
- `ma_thung`: mã thùng đóng gói.
- `ma_khay`: mã khay đóng gói.
- `so_luong_vt_khay`: số lượng vật tư trên 1 khay.
- `so_luong_thung_pallet`: số lượng thùng trên 1 pallet.

## Quy tắc nghiệp vụ
Khi người dùng hỏi về quy cách đóng gói chi tiết của mã hàng, tra cứu từ `dmvt`. Nếu hệ số pallet hoặc túi bằng 0 thì báo rõ chưa khai báo hệ số đó.
