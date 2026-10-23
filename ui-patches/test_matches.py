import sys

path = "/home/admin/ai-stack/ui-patches/2.Czbv28Xq.js"
with open(path, "r", encoding="utf-8") as f:
    text = f.read()

replacements = [
    # General tab descriptions
    ('t().t("Choose the color theme used by the interface.")', 't().t("Chọn chủ đề màu sắc cho giao diện.")'),
    ('t().t("Choose the language used for interface text.")', 't().t("Chọn ngôn ngữ hiển thị giao diện.")'),
    ('t().t("Set the default system prompt for new chats.")', 't().t("Đặt prompt hệ thống mặc định cho các đoạn chat mới.")'),
    ('t().t("Model parameters")', 't().t("Tham số mô hình")'),
    ('t().t("Show or hide custom generation parameters.")', 't().t("Hiển thị hoặc ẩn các tham số sinh phản hồi tùy chỉnh.")'),
    ('t().t("Enter system prompt here")', 't().t("Nhập prompt hệ thống tại đây")'),
    ('t().t("Select a theme")', 't().t("Chọn chủ đề")'),
    ('t().t("Select a language")', 't().t("Chọn ngôn ngữ")'),
    
    # Settings modal sidebar tab categories
    ('V={general:"Basics",interface:"Basics",notifications:"Basics",shortcuts:"Basics",connections:"Services",tools:"Services",personalization:"Preferences",audio:"Preferences",data_controls:"Data",usage:"Data",archived_chats:"Data",account:"Profile",about:"Profile"}',
     'V={general:"Cơ bản",interface:"Cơ bản",notifications:"Cơ bản",shortcuts:"Bàn phím",connections:"Dịch vụ",tools:"Dịch vụ",personalization:"Tùy chọn",audio:"Tùy chọn",data_controls:"Dữ liệu",usage:"Dữ liệu",archived_chats:"Dữ liệu",account:"Hồ sơ",about:"Hồ sơ"}'),
    
    ('te={"admin:general":"System","admin:authentication":"System","admin:connections":"AI","admin:models":"AI","admin:subagents":"AI","admin:evaluations":"Quality","admin:analytics":"Quality","admin:integrations":"Tools","admin:documents":"Tools","admin:web":"Tools","admin:code-execution":"Tools","admin:pipelines":"Tools","admin:interface":"Experience","admin:audio":"Experience","admin:images":"Experience","admin:db":"Data"}',
     'te={"admin:general":"Hệ thống","admin:authentication":"Hệ thống","admin:connections":"Trí tuệ nhân tạo (AI)","admin:models":"Trí tuệ nhân tạo (AI)","admin:subagents":"Trí tuệ nhân tạo (AI)","admin:evaluations":"Chất lượng","admin:analytics":"Chất lượng","admin:integrations":"Công cụ","admin:documents":"Tài liệu & Tri thức","admin:web":"Công cụ","admin:code-execution":"Công cụ","admin:pipelines":"Công cụ","admin:interface":"Trải nghiệm","admin:audio":"Trải nghiệm","admin:images":"Trải nghiệm","admin:db":"Dữ liệu"}'),
    
    # Tab labels
    ('Se().t("Personal")', 'Se().t("Cá nhân")'),
    ('Se().t("Keyboard")', 'Se().t("Bàn phím")'),
    ('Se().t("Data Controls")', 'Se().t("Kiểm soát dữ liệu")'),
    ('Se().t("Usage")', 'Se().t("Mức sử dụng")'),
    ('Se().t("Back")', 'Se().t("Quay lại")'),
    ('Se().t("Search")', 'Se().t("Tìm kiếm")'),
    
    # Account tab
    ('t().t("Set the display name shown across your account.")', 't().t("Đặt tên hiển thị dùng trên toàn bộ tài khoản.")'),
    ('t().t("Enter your name")', 't().t("Nhập họ và tên")'),
    ('t().t("Add optional profile context visible where profiles are shown.")', 't().t("Thêm thông tin tiểu sử hiển thị trên hồ sơ.")'),
    ('t().t("Share your background and interests")', 't().t("Chia sẻ thông tin giới thiệu và sở thích")'),
    ('t().t("Choose the gender value stored on your profile.")', 't().t("Chọn giới tính lưu trong hồ sơ của bạn.")'),
    ('t().t("Set the birth date saved with your profile.")', 't().t("Cài đặt ngày sinh lưu trong hồ sơ của bạn.")'),
    ('t().t("Enter your current password")', 't().t("Nhập mật khẩu hiện tại")'),
    ('t().t("Enter your new password")', 't().t("Nhập mật khẩu mới")'),
    ('t().t("Confirm your new password")', 't().t("Xác nhận mật khẩu mới")'),
    ('t().t("Update password")', 't().t("Cập nhật mật khẩu")'),
    ('t().t("Change Password")', 't().t("Đổi mật khẩu")'),
    ('t().t("Update the password used for email and password sign-in.")', 't().t("Cập nhật mật khẩu dùng để đăng nhập bằng mã nhân viên và mật khẩu.")'),
    ('t().t("Show or hide sensitive account secrets.")', 't().t("Hiển thị hoặc ẩn thông tin bảo mật tài khoản.")'),
    ('t().t("Copy the current session token for authenticated requests.")', 't().t("Sao chép mã phiên làm việc hiện tại để xác thực.")'),
    ('t().t("Create, copy, or rotate your API key.")', 't().t("Tạo, sao chép hoặc xoay vòng khóa API của bạn.")'),
    ('t().t("Copy API Key")', 't().t("Sao chép Khóa API")'),
    ('t().t("Create new secret key")', 't().t("Tạo khóa bí mật mới")'),
    ('t().t("Create new key")', 't().t("Tạo khóa mới")'),
    ('t().t("Delete API Key?")', 't().t("Xóa Khóa API?")'),
    ('t().t("This will revoke the current API key.")', 't().t("Thao tác này sẽ thu hồi khóa API hiện tại.")'),
    
    # About tab
    ('t().t("View the installed version and check release updates.")', 't().t("Xem phiên bản hiện tại và kiểm tra bản cập nhật.")'),
    ('t().t("Check for updates")', 't().t("Kiểm tra cập nhật")'),
    ('t().t("See what\'s new")', 't().t("Xem điểm mới")'),
]

for src, dst in replacements:
    count = text.count(src)
    print(f"[{count}] {src[:60]}")
