(() => {
  'use strict';

  // --- 1. Model Picker Compact View ---
  const ALL_LABELS = new Set(['tất cả', 'all']);
  const compactText = (value) => (value || '').replace(/\s+/g, ' ').trim().toLowerCase();

  const hideModelPickerFilter = () => {
    for (const input of document.querySelectorAll('input[placeholder]')) {
      if (!/model/i.test(input.getAttribute('placeholder') || '')) continue;

      let container = input.parentElement;
      for (let depth = 0; container && depth < 5; depth += 1, container = container.parentElement) {
        const filter = Array.from(container.querySelectorAll('button')).find(
          (button) => ALL_LABELS.has(compactText(button.textContent))
        );
        if (!filter) continue;

        filter.hidden = true;
        filter.setAttribute('aria-hidden', 'true');
        input.parentElement?.style.setProperty('flex-grow', '1');
        break;
      }

      const inputRect = input.getBoundingClientRect();
      for (const button of document.querySelectorAll('button')) {
        const rect = button.getBoundingClientRect();
        if (
          rect.width > 0 &&
          rect.height > 0 &&
          rect.left >= inputRect.left &&
          rect.left <= inputRect.right + 8 &&
          rect.top < inputRect.bottom &&
          rect.bottom > inputRect.top
        ) {
          button.hidden = true;
          button.setAttribute('aria-hidden', 'true');
        }
      }

      let popup = input.parentElement;
      for (let depth = 0; popup && depth < 8; depth += 1, popup = popup.parentElement) {
        const rect = popup.getBoundingClientRect();
        if (rect.height > 120 && rect.width >= inputRect.width && rect.width < 600) {
          popup.style.setProperty('width', '15rem', 'important');
          popup.style.setProperty('min-width', '15rem', 'important');
          popup.style.setProperty('max-width', 'calc(100vw - 2rem)', 'important');
          break;
        }
      }
    }
  };

  // --- 2. Comprehensive Vietnamese Localization Engine ---
  const DICT = {
    // General Settings (Screen in Screenshot)
    'Choose the color theme used by the interface.': 'Chọn chủ đề màu sắc cho giao diện.',
    'Choose the language used for interface text.': 'Chọn ngôn ngữ hiển thị giao diện.',
    'Set the default system prompt for new chats.': 'Đặt prompt hệ thống mặc định cho các đoạn chat mới.',
    'Model parameters': 'Tham số mô hình',
    'Model Parameters': 'Tham số mô hình',
    'Show or hide custom generation parameters.': 'Hiển thị hoặc ẩn các tham số sinh phản hồi tùy chỉnh.',
    'Select a theme': 'Chọn một chủ đề',
    'Select a language': 'Chọn một ngôn ngữ',
    'Enter system prompt here': 'Nhập prompt hệ thống tại đây',

    // Sidebar Tab Group Headers & Items
    'Personal': 'Cá nhân',
    'Basics': 'Cơ bản',
    'Preferences': 'Tùy chọn',
    'Keyboard': 'Bàn phím',
    'Services': 'Dịch vụ',
    'Data': 'Dữ liệu',
    'Data Controls': 'Kiểm soát dữ liệu',
    'Usage': 'Mức sử dụng',
    'Profile': 'Hồ sơ',
    'System': 'Hệ thống',
    'General': 'Cài đặt chung',
    'Interface': 'Giao diện',
    'Audio': 'Âm thanh',
    'Account': 'Tài khoản',
    'About': 'Giới thiệu',
    'Search': 'Tìm kiếm',
    'Notification': 'Thông báo',
    'Notifications': 'Thông báo',
    'Shortcuts': 'Phím tắt',
    'Connections': 'Kết nối',
    'Integrations': 'Tích hợp',
    'Personalization': 'Cá nhân hóa',
    'Archived Chats': 'Lưu các cuộc Chat',
    'Save': 'Lưu',
    'Cancel': 'Hủy',
    'Close': 'Đóng',
    'Back': 'Quay lại',
    'Done': 'Hoàn tất',
    'Delete': 'Xóa',
    'Edit': 'Sửa',
    'Add': 'Thêm',
    'Key': 'Khóa',
    'Value': 'Giá trị',
    'Show': 'Hiển thị',
    'Hide': 'Ẩn',

    // Account tab
    'Name': 'Tên hiển thị',
    'Enter your name': 'Nhập họ và tên',
    'Set the display name shown across your account.': 'Đặt tên hiển thị dùng trên toàn bộ tài khoản.',
    'Bio': 'Tiểu sử',
    'Share your background and interests': 'Chia sẻ thông tin giới thiệu và sở thích',
    'Add optional profile context visible where profiles are shown.': 'Thêm thông tin tiểu sử hiển thị trên hồ sơ.',
    'Gender': 'Giới tính',
    'Choose the gender value stored on your profile.': 'Chọn giới tính lưu trong hồ sơ của bạn.',
    'Birth Date': 'Ngày sinh',
    'Set the birth date saved with your profile.': 'Cài đặt ngày sinh lưu trong hồ sơ của bạn.',
    'Change Password': 'Đổi mật khẩu',
    'Current Password': 'Mật khẩu hiện tại',
    'New Password': 'Mật khẩu mới',
    'Confirm Password': 'Xác nhận mật khẩu mới',
    'Update password': 'Cập nhật mật khẩu',
    'Enter your current password': 'Nhập mật khẩu hiện tại',
    'Enter your new password': 'Nhập mật khẩu mới',
    'Confirm your new password': 'Xác nhận mật khẩu mới',
    'Update the password used for email and password sign-in.': 'Cập nhật mật khẩu dùng để đăng nhập bằng mã nhân viên và mật khẩu.',
    'API keys': 'Khóa API',
    'API Key': 'Khóa API',
    'JWT Token': 'JWT Token phiên làm việc',
    'Secrets': 'Bảo mật & Bí mật',
    'Show or hide sensitive account secrets.': 'Hiển thị hoặc ẩn thông tin bảo mật tài khoản.',
    'Copy Token': 'Sao chép Token',
    'Copy the current session token for authenticated requests.': 'Sao chép mã phiên làm việc hiện tại để xác thực.',
    'Copy API Key': 'Sao chép Khóa API',
    'Create new key': 'Tạo khóa mới',
    'Create new secret key': 'Tạo khóa bí mật mới',
    'Create, copy, or rotate your API key.': 'Tạo, sao chép hoặc xoay vòng khóa API của bạn.',
    'Delete API Key?': 'Xóa Khóa API?',
    'This will revoke the current API key.': 'Thao tác này sẽ thu hồi khóa API hiện tại.',
    'User Variables': 'Biến người dùng',
    'Add User Variable': 'Thêm biến người dùng',
    'Edit User Variable': 'Chỉnh sửa biến người dùng',
    'No user variables configured.': 'Chưa có biến người dùng nào được cấu hình.',
    'Variable key': 'Khóa biến',
    'Variable value': 'Giá trị biến',

    // About tab
    'Version': 'Phiên bản',
    'View the installed version and check release updates.': 'Xem phiên bản hiện tại và kiểm tra bản cập nhật.',
    'Check for updates': 'Kiểm tra cập nhật',
    'See what\'s new': 'Xem điểm mới',
    'Community': 'Cộng đồng',

    // Interface tab
    'Landing Page': 'Trang khởi đầu',
    'Chat Direction': 'Hướng văn bản',
    'Chat Background Image': 'Hình nền trò chuyện',
    'User Location': 'Vị trí người dùng',
    'Widescreen Mode': 'Chế độ màn hình rộng',
    'Collapse code blocks by default': 'Mặc định thu gọn khối mã',
    'Display emoji in call': 'Hiển thị biểu tượng cảm xúc trong cuộc gọi',
    'Allow voice interruption in call': 'Cho phép ngắt lời bằng giọng nói trong cuộc gọi',
    'Auto-copy response to clipboard': 'Tự động sao chép phản hồi vào clipboard',
    'Always expand details': 'Luôn mở rộng chi tiết',
    'Rich text input for chat': 'Trình soạn thảo văn bản phong phú cho chat',
    'Paste large text as file': 'Dán văn bản dài dưới dạng tệp',
    'Scroll on branch change': 'Cuộn khi đổi nhánh hội thoại',
    'Detect artifacts automatically': 'Tự động nhận diện artifacts',
    'Default Model': 'Mô hình mặc định',
    'Show username': 'Hiển thị tên người dùng',

    // Audio tab
    'Text-to-Speech Engine': 'Công cụ chuyển văn bản thành giọng nói',
    'Speech-to-Text Engine': 'Công cụ chuyển giọng nói thành văn bản',
    'Choose the browser voice used for speech output.': 'Chọn giọng đọc trình duyệt cho âm thanh.',
    'Choose the configured text-to-speech service voice.': 'Chọn giọng đọc của dịch vụ TTS đã cấu hình.',
    'Choose the engine used to read assistant responses aloud.': 'Chọn công cụ đọc to phản hồi của trợ lý.',
    'Choose the engine used to transcribe voice input.': 'Chọn công cụ chuyển giọng nói thành văn bản.',
    'Choose whether Enter sends immediately or uses Ctrl+Enter.': 'Chọn gửi tin nhắn bằng Enter hoặc dùng Ctrl+Enter.',
    'Choose whether the app opens to the default home or chat view.': 'Chọn mở ứng dụng ở trang chủ mặc định hay khung chat.',
    'Auto-playback response': 'Tự động phát lại phản hồi',
    'Voice': 'Giọng nói',

    // Data Controls tab
    'Import Chats': 'Nhập cuộc trò chuyện',
    'Export Chats': 'Xuất cuộc trò chuyện',
    'Archive all chats': 'Lưu trữ tất cả cuộc trò chuyện',
    'Delete all chats': 'Xóa tất cả cuộc trò chuyện'
  };

  let translating = false;

  const translateText = (raw) => {
    if (!raw) return raw;
    const trimmed = raw.trim();
    if (DICT[trimmed]) {
      return raw.replace(trimmed, DICT[trimmed]);
    }
    return raw;
  };

  const translateDomNode = (node) => {
    if (!node) return;
    if (node.nodeType === Node.TEXT_NODE) {
      const current = node.nodeValue;
      if (!current) return;
      const translated = translateText(current);
      if (translated !== current) {
        node.nodeValue = translated;
      }
    } else if (node.nodeType === Node.ELEMENT_NODE) {
      // Input placeholders
      if (node.tagName === 'INPUT' || node.tagName === 'TEXTAREA') {
        const ph = node.getAttribute('placeholder');
        if (ph && DICT[ph.trim()]) {
          node.setAttribute('placeholder', DICT[ph.trim()]);
        }
      }
      // Aria labels & titles
      const aria = node.getAttribute('aria-label');
      if (aria && DICT[aria.trim()]) {
        node.setAttribute('aria-label', DICT[aria.trim()]);
      }
      const title = node.getAttribute('title');
      if (title && DICT[title.trim()]) {
        node.setAttribute('title', DICT[title.trim()]);
      }

      for (let child = node.firstChild; child; child = child.nextSibling) {
        translateDomNode(child);
      }
    }
  };

  const runTranslation = () => {
    if (translating) return;
    translating = true;
    try {
      translateDomNode(document.body || document.documentElement);
    } finally {
      translating = false;
    }
  };

  // Run on initial load
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', runTranslation);
  } else {
    runTranslation();
  }

  // Observe DOM changes: childList, subtree, and characterData
  const observer = new MutationObserver((mutations) => {
    if (translating) return;
    hideModelPickerFilter();

    let needsTranslation = false;
    for (const m of mutations) {
      if (m.type === 'characterData') {
        const text = m.target.nodeValue;
        if (text && DICT[text.trim()]) {
          needsTranslation = true;
          break;
        }
      } else if (m.type === 'childList' && m.addedNodes.length > 0) {
        needsTranslation = true;
        break;
      }
    }
    if (needsTranslation) {
      runTranslation();
    }
  });

  observer.observe(document.documentElement, {
    childList: true,
    subtree: true,
    characterData: true,
  });

  // Also hook into user interactions that open modals or switch tabs
  window.addEventListener('click', () => {
    setTimeout(runTranslation, 20);
    setTimeout(runTranslation, 150);
  }, { passive: true });

  window.addEventListener('keydown', () => {
    setTimeout(runTranslation, 50);
  }, { passive: true });
})();
