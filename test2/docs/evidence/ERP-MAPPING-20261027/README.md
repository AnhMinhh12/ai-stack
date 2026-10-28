# ERP Read-Only Mapping Evidence — 2026-10-27

## 1. Scope, Objective, and Safety Guardrails

- **Objective**: Establish a strict, read-only mapping of the ERP system from Menu / UI Screens / UI Columns → Request / API Endpoints → Function / View / Query → DB Tables / DB Columns and Business Formulas.
- **Safety Guarantee**:
  - **Zero write operations**: No save (`SaveAdd`, `SaveEdit`), approval (`Approve`), delete (`Delete`), posting, import (`ImportExcelUpdate`), or unverified mutating endpoints were invoked.
  - Only read-only authentication (`Check_login`), menu tree resolution (`GetTree_Module`), grid schema initialization (`LookUpConfigAPI/InitGridMenu`), and bundle code analysis were executed.
  - Any field or screen lacking live empirical proof remains explicitly marked `UNVERIFIED`.

---

## 2. Live Connectivity & Environment Verification

| Check | Target | Status | Result / Details |
|---|---|---|---|
| TCP Port | `10.0.6.2:1004` | **OPEN** | Succeeded via TCP connection |
| HTTP Web Server | `http://10.0.6.2:1004/Solution/ERP/` | **HTTP 200 OK** | Microsoft-IIS/10.0, ASP.NET Web API backend |
| Login Interface | `http://10.0.6.2:1004/Account/Login` | **HTTP 200 OK** | AngularJS client (`ModuleLogin`) |
| Grafana Host | `http://10.0.6.2:1006/` | **VERIFIED** | Host for embedded `type: "GDB"` Dashboards |

---

## 3. Authentication & Session Verification (LIVE)

Authentication was successfully performed using credentials `IT.ERP` / `9966` and branch `001 / HTMP QM`.

### 3.1 HTTP Request Shape
- **Endpoint**: `POST /SysAPI/api/LoginAPI/Check_login/`
- **Required Custom Headers**:
  ```http
  user_name: IT.ERP
  module: ERP
  Content-Type: application/json
  ```
- **JSON Payload**:
  ```json
  {
    "user_name": "IT.ERP",
    "pass": "9966",
    "ma_dvcs": "001",
    "languages": "vi-VN"
  }
  ```

### 3.2 Authenticated Identity Profile
- **Token Issued**: `e7871210-c5c8-42b3-b362-60c08a042287-ty7sKsHUhkoF1uB3iG4Et0CbNoOOzo`
- **User ID**: `78`
- **User Name**: `IT.ERP`
- **Display Name**: `Nhóm IT-ERP`
- **Unit / Branch (`ma_dvcs`)**: `001` (`HTMP QM`)
- **Privileges**: `is_admin = 1`, `is_super = 0`
- **Live Browser Session**: Verified via browser agent navigating to `http://10.0.6.2:1004/Solution/ERP/#/Main/Dashboards`.

---

## 4. Menu Tree & Module Permissions Architecture

- **Menu Tree Read Endpoint**:
  `GET /SysAPI/api/LoginAPI/GetTree_Module/?user_id=78&module=ERP`
- **Authentication Headers for API Calls**:
  ```http
  Token: <token>
  user_name: IT.ERP
  user_id: 78
  lang: vi-VN
  ma_dvcs: 001
  module: ERP
  ```
- **Total Menu Items**: **337** items in hierarchy.
- **Total Leaf Screens**: **171** executable screens across all functional modules:

| Module | Module Name | Total Menus | Leaf Screens | Primary Business Functions |
|---|---|---|---|---|
| **SO** | Bán hàng (Sales Order) | 59 | 37 | Báo giá (SQ1), Đơn hàng (SO1), Kế hoạch (TO2), Hóa đơn (HDA/HDF/HDG), Danh mục khách hàng, Bảng giá (DMBangGiaCT) |
| **PO** | Mua hàng (Purchase Order) | 41 | 18 | Yêu cầu mua (PR0/PR1), Đơn mua (PO1), Hóa đơn NCC (PNC/PXC), Nhà cung cấp, Bảng giá mua |
| **IN** | Kho vận (Inventory) | 68 | 37 | Nhập kho (PNA/PNF), Xuất kho (PXA/PXB/PXE), Kiểm kê (KK0/KK1), In tem QR (InTemNVL, InTemTP, InTemTui, InTemTK), Danh mục vật tư, Danh mục kho |
| **MF** | Sản xuất (Manufacturing) | 33 | 14 | Nhu cầu sản xuất (MfDemand), Kế hoạch NVL (MfTKHNVL), Định mức BOM (MfBOM), Công đoạn (MfListOperation, MfListRouting) |
| **GL** | Quản trị / Kế toán tổng hợp | 14 | 3 | Tồn kho đầu kỳ (CNTonKhoDauKy), Công nợ số dư đầu (GLCSD) |
| **QC** | Quản lý chất lượng | 6 | 1 | Tài liệu PPAP (DMTaiLieuPPAP) |
| **NM / ERP** | New Model / Kỹ thuật | 8 | 3 | Quy trình New Model (MfListProcessGroup), BomBop (MfBomBop) |
| **SYS** | Hệ thống & Dashboards | 108 | 58 | Nhóm Dashboard (`GDB_*`), Phân quyền (`sys_role`), Người dùng (`userinfo`), Đơn vị cơ sở (`sys_dvcs`) |

---

## 5. Live Verification of Dashboards (Resolved from UNVERIFIED)

Previously, Dashboards were recorded as `UNVERIFIED`. Live inspection of the ERP frontend bundle (`appjs.js`), menu tree metadata (`option_ext`), and system configurations (`sysoptions`) reveals the exact dashboard architecture:

1. **Dashboard Architecture**:
   - Dashboards are embedded **Grafana Dashboards** (`type: "GDB"`).
   - Rendered in ERP frontend within `#/Main/Dashboards` via dynamic `<iframe>` and cross-origin window messaging (`CrossOriginStorageGrafana`).
   - Dedicated Grafana Backend Host: `http://10.0.6.2:1006/`.
2. **Specific Live Dashboard Mappings**:

| Dashboard Screen State | UI Title | Embedded Grafana URL | Container Height | Source / DB Reference |
|---|---|---|---|---|
| `GDB_OEE` | Dashboard OEE | `http://10.0.6.2:1006/d/0iod4MaNz/dashboard-oee?orgId=1` | 450px | IIoT Hub / OEE engine |
| `GDB_BCTKHSX` | Dashboard báo cáo tổng kết hàng SX | `http://10.0.6.2:1006/d/2yC9hVoNz/gdb_bctkhsx?orgId=1` | 600px | Production summary |
| `GDB_BCTKHSX2` | Dashboard tổng kết hàng SX theo nhóm KH2 | `http://10.0.6.2:1006/d/mIcNf5yHk/dashboard-tong-ket-hang-san-xuat-theo-nhom-kh2?orgId=1` | 600px | Customer group 2 production |
| `GDB_THSLTK` | Dashboard tổng hợp số lần thay khuôn | `http://10.0.6.2:1006/d/N1t5Vf2Hz/dashboard-san-xuat?orgId=1` | 1000px | Mold change log |
| `GDB_TLLKTK` | Dashboard tỷ lệ lỗi khi thay khuôn | `http://10.0.6.2:1006/d/J4R6ZKoNz/dashboard-ty-le-loi-khi-thay-khuon?orgId=1` | 600px | Mold change defect rate |
| `GDB_TopLoiDCTheoNNNDC1` | Dashboard top lỗi dừng chuyền theo nhóm NN 1 | `http://10.0.6.2:1006/d/JBf2P6YHk/top-loi-dung-chuyen-theo-nhom-nguyen-nhan-dung-chuyen-1?orgId=1` | Dynamic | Downtime cause group 1 |
| `GDB_THLDC` | Dashboard tổng hợp lỗi dừng chuyền | `http://10.0.6.2:1006/d/uGdY3XhHz/dashboard-tong-hop-loi-dung-chuyen?orgId=1` | 800px | Total downtime log |
| `GDB_TopLoiDCTheoNDC1` | Top lỗi dừng chuyền theo nhóm dây chuyền 1 | `http://10.0.6.2:1006/d/GYGi-6YHz/top-loi-dung-chuyen-theo-nhom-day-chuyen-1?orgId=1` | Dynamic | Production line group 1 |
| `GDB_TLNGTHEOLSX` | Tỷ lệ lỗi ngoại quan theo lệnh SX | `http://10.0.6.2:1006/d/8u6HXsxNk/gdb_tlngtheolsx?orgId` | 600px | Visual inspection defect % |
| `GDB_TopLoiSX` | Top lỗi sản xuất | `http://10.0.6.2:1006/d/Ju2OrZ-Hz/gdb_toploisx?orgId=1` | 600px | Top production defects |
| `GDB_TYLEKHO33` | Tỷ lệ kho 33 | `http://10.0.6.2:1006/d/4twHTLTNz/gdb_tylekho33?orgId=1` | 600px | Warehouse 33 capacity % |
| `GDB_ERP` | Cảnh báo hạn sử dụng | `http://10.0.6.2:1006/d/viawBClGk35/canh-bao-han-su-dung?orgId=1` | 680px | Inventory shelf life expiry |
| `GDB_NHA_MAY` | Chung toàn nhà máy cho SX | `http://10.0.6.2:1006/d/UCDV32_Hk/chung-toan-nha-may-cho-sx?orgId=1` | 1100px | Factory-wide manufacturing |
| `GDB_NHA_MAY_QC` | Chung toàn nhà máy cho QC | `http://10.0.6.2:1006/d/FBUrQAlNz/chung-toan-nha-may-cho-qc?orgId=1` | 600px | Factory-wide quality control |
| `GDB_QLTD` | Dashboard cho SX quản lý trọng điểm | `http://10.0.6.2:1006/d/K_3L80_Hz/dashboard-cho-sx-quan-ly-trong-diem?orgId` | 800px | Key priority control |

---

## 6. Grid Column Metadata & Database Source Mapping (LIVE)

- **Grid Configuration Query Endpoint**:
  `GET /ConfigAPI/api/LookUp/LookUpConfigAPI/InitGridMenu/?gridid={gridid}&form_trans=%23`
- **Total Columns Extracted & Mapped**: **1,738 rows** in [`screen-columns.csv`](file:///C:/Users/it07/Downloads/test2/docs/evidence/ERP-MAPPING-20261027/screen-columns.csv).

### Key Examples of Live Verified UI-to-DB Column Mappings:

1. **Danh mục Khách hàng (`DMKhachHang`)**:
   - Table: `dmkh`
   - Key fields: `ma_kh` (Mã KH), `ten_kh` (Tên KH), `dia_chi` (Địa chỉ), `ma_so_thue` (MST), `dien_thoai`, `email`, `nh_kh1`..`nh_kh5`, `ma_tt` (Thanh toán), `han_tt` (Hạn thanh toán), `status` (Trạng thái).
   - Joined lookup: `sys_dmtt` on `status`, `dmnhkh` on `ma_nh`.

2. **Bảng giá Chi tiết (`DMBangGiaCT`)**:
   - Table: `dmbanggiact`
   - Key fields: `ma_bang_gia` (Mã bảng giá), `ma_vt` (Mã VT `ct64`), `dvt` (`ct94`), `ngay_bd` / `ngay_kt` (`FORMAT_DATE_GRID`), `gio_bd` / `gio_kt` (`FORMAT_TIME`), `sl_min` (`FORMAT_SL`), `ma_nt` (Ngoại tệ), `ty_gia` (`FORMAT_TY_GIA`), `gia0` (Giá NT), `ma_thue`, `thue_suat` (`FORMAT_HESO`), `gia` (Giá VND), `so_ct_sq1` (Báo giá SQ1 liên kết).

3. **Danh mục Vật tư (`DmVatTu`)**:
   - Table: `dmvt` (147 columns mapped)
   - Key fields: `ma_vt`, `ten_vt`, `ten_vt2`, `dvt`, `ma_nh0`..`ma_nh3`, `ma_kho`, `loai_vt`, `quy_cach`, `xuat_am_yn`, `sl_min`, `sl_max`.

4. **Đơn hàng Bán (`SO1Overview` / `SO1`)**:
   - Header Table: `ph` (stt_rec, so_ct, ngay_ct, ngay_lct, ma_gd, ma_kh, ong_ba, dia_chi, dien_thoai, ma_nvbh, ma_nt, ty_gia, status)
   - Detail Item Table: `ct64` (line items: ma_vt, ten_vt, dvt, so_luong, gia_chuan, gia_nt, tien, ma_thue, thue_suat, thue)
   - Delivery Schedule Table: `ctkhgh` (chi tiết kế hoạch giao hàng: ngay_gh, sl_gh, ma_vi_tri_kh, so_po)
   - Discount Table: `ctck20` (chiết khấu)
   - Business Formulas:
     - Payment due date: calculated dynamically from voucher date `ngay_ct`, payment terms `han_tt`, and cut-off day `ngay_cd`.
     - Unit price and tax lookup: fetched via `GetMainItemPriceByDate` matching `ma_vt`, customer group, and date.

---

## 7. Artifacts Generated

- [`screen-columns.csv`](file:///C:/Users/it07/Downloads/test2/docs/evidence/ERP-MAPPING-20261027/screen-columns.csv): 1,738 records detailing screen state, URL, UI label, API field, API endpoint, source object (DB table), source expression, join keys, filters, and formula notes.
- [`menu_tree_raw.json`](file:///C:/Users/it07/Downloads/test2/menu_tree_raw.json): Full 337-item authenticated menu hierarchy.
- [`session_info.json`](file:///C:/Users/it07/Downloads/test2/session_info.json): Authenticated session metadata, system options, and module registrations.
