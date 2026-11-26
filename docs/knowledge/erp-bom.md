# Cấu trúc sản phẩm và định mức BOM

## Nguồn và dữ liệu
Cấu trúc sản phẩm lưu tại public.mfbom (header BOM) và public.mfbom_material (chi tiết nguyên vật liệu).
product_code là mã sản phẩm mẹ (ma_sp_me), material_code là mã nguyên vật liệu hoặc mã nhựa (ma_btp_vt).
Trường ten_vt trong danh mục vật tư public.dmvt mô tả tên loại nhựa hoặc tên vật tư.
sl_dinh_muc (quantity) là số lượng định mức trên một đơn vị thành phẩm, đơn vị tính uom.

## Quy tắc nghiệp vụ
Khi hỏi mã hàng dùng loại nhựa gì hoặc định mức NVL, tra cứu theo bom_code còn hiệu lực của mã hàng.
