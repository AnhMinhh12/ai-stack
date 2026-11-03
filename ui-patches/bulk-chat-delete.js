(() => {
	const selected = new Set();
	let toolbar;

	const chatRows = () => {
		return [...document.querySelectorAll('a#sidebar-chat-item[href^="/c/"]')]
			.map((link) => {
				const id = new URL(link.href, window.location.origin).pathname.split('/')[2];
				return id ? { id, link } : null;
			})
			.filter(Boolean);
	};

	const updateToolbar = () => {
		if (!toolbar) return;
		const count = selected.size;
		toolbar.style.display = count === 0 ? 'none' : 'flex';
		const countLabel = toolbar.querySelector('[data-count]');
		const deleteLabel = toolbar.querySelector('[data-delete]');
		if (countLabel.textContent !== `${count} đã chọn`) countLabel.textContent = `${count} đã chọn`;
		if (deleteLabel.textContent !== `Xóa (${count})`) deleteLabel.textContent = `Xóa (${count})`;
	};

	const setSelected = (id, checked) => {
		if (checked) selected.add(id);
		else selected.delete(id);
		updateToolbar();
	};

	const createToolbar = () => {
		if (toolbar) return;
		toolbar = document.createElement('div');
		toolbar.id = 'htmp-bulk-chat-delete';
		toolbar.innerHTML = `
			<span data-count></span>
			<button type="button" data-select-all>Chọn tất cả</button>
			<button type="button" data-clear>Bỏ chọn</button>
			<button type="button" data-delete></button>`;
		Object.assign(toolbar.style, {
			position: 'fixed',
			left: '12px',
			bottom: '12px',
			zIndex: '100000',
			display: 'flex',
			alignItems: 'center',
			gap: '8px',
			flexWrap: 'wrap',
			maxWidth: 'min(420px, calc(100vw - 24px))',
			padding: '10px 12px',
			border: '1px solid #d1d5db',
			borderRadius: '12px',
			background: 'Canvas',
			color: 'CanvasText',
			boxShadow: '0 8px 24px #0003',
			font: '13px system-ui, sans-serif',
		});
		for (const button of toolbar.querySelectorAll('button')) {
			Object.assign(button.style, {
				border: '0',
				borderRadius: '8px',
				padding: '6px 9px',
				background: 'color-mix(in srgb, CanvasText 10%, Canvas)',
				color: 'CanvasText',
				cursor: 'pointer',
			});
		}
		const deleteButton = toolbar.querySelector('[data-delete]');
		deleteButton.style.background = '#dc2626';
		deleteButton.style.color = '#fff';
		toolbar.querySelector('[data-select-all]').addEventListener('click', async (event) => {
			const button = event.currentTarget;
			button.disabled = true;
			button.textContent = 'Đang tải lịch sử…';
			try {
				const response = await fetch('/api/v1/chats/?include_pinned=true&include_folders=true', {
					headers: { Authorization: `Bearer ${localStorage.token}` },
					credentials: 'same-origin',
				});
				if (!response.ok) throw new Error(`HTTP ${response.status}`);
				const chats = await response.json();
				for (const chat of chats) if (chat.id) selected.add(chat.id);
				scan();
			} catch (error) {
				window.alert(`Không tải được toàn bộ lịch sử: ${error.message}`);
			} finally {
				button.disabled = false;
				button.textContent = 'Chọn tất cả lịch sử';
			}
		});
		toolbar.querySelector('[data-clear]').addEventListener('click', () => {
			selected.clear();
			scan();
		});
		deleteButton.addEventListener('click', deleteSelected);
		document.body.appendChild(toolbar);
		updateToolbar();
	};

	async function deleteSelected() {
		const ids = [...selected];
		if (!ids.length) return;
		const confirmed = window.confirm(`Xóa vĩnh viễn ${ids.length} hội thoại đã chọn?`);
		if (!confirmed) return;

		const token = localStorage.token;
		if (!token) {
			window.alert('Không tìm thấy phiên đăng nhập. Vui lòng đăng nhập lại.');
			return;
		}

		const succeeded = [];
		const failed = [];
		for (let index = 0; index < ids.length; index += 8) {
			const batch = ids.slice(index, index + 8);
			const results = await Promise.all(batch.map(async (id) => {
				try {
					const response = await fetch(`/api/v1/chats/${encodeURIComponent(id)}`, {
						method: 'DELETE',
						headers: { Authorization: `Bearer ${token}` },
						credentials: 'same-origin',
					});
					return { id, ok: response.ok };
				} catch {
					return { id, ok: false };
				}
			}));
			for (const result of results) (result.ok ? succeeded : failed).push(result.id);
		}

		const currentId = window.location.pathname.match(/^\/c\/([^/]+)/)?.[1];
		if (failed.length) {
			window.alert(`Đã xóa ${succeeded.length}/${ids.length} hội thoại. ${failed.length} hội thoại chưa xóa được.`);
		} else {
			window.alert(`Đã xóa ${succeeded.length} hội thoại.`);
		}
		if (currentId && succeeded.includes(currentId)) window.location.assign('/');
		else window.location.reload();
	}

	// ========================================================
	// HTMP ERP - Báo cáo câu trả lời sai (Incident Reporting)
	// ========================================================
	let activeReportTarget = null;
	let reportModalEl = null;

	function getOrCreateReportModal() {
		if (reportModalEl) return reportModalEl;
		const el = document.createElement('div');
		el.id = 'htmp-incident-report-modal';
		el.style.display = 'none';
		el.innerHTML = `
			<div class="htmp-crm-backdrop" style="position:fixed;inset:0;background:rgba(0,0,0,0.55);backdrop-filter:blur(3px);z-index:999999;display:flex;align-items:center;justify-content:center;padding:16px;">
				<div class="htmp-crm-box" style="background:#ffffff;color:#182232;border:1px solid #e2e8f0;border-radius:14px;width:100%;max-width:540px;box-shadow:0 20px 40px rgba(0,0,0,0.25);overflow:hidden;font-family:system-ui,-apple-system,sans-serif;">
					<div style="display:flex;align-items:center;justify-content:space-between;padding:14px 18px;border-bottom:1px solid #e2e8f0;font-weight:700;font-size:15px;">
						<div style="display:flex;align-items:center;gap:8px;">
							<span style="font-size:17px;color:#dc2626;">🚩</span>
							<span>Báo cáo câu trả lời không chính xác</span>
						</div>
						<button type="button" data-close style="background:none;border:none;font-size:18px;cursor:pointer;color:inherit;opacity:0.6;line-height:1;padding:4px;">✕</button>
					</div>
					<div style="padding:16px 18px;display:flex;flex-direction:column;gap:12px;font-size:13px;">
						<p style="margin:0;color:#64748b;line-height:1.5;">Báo cáo của bạn sẽ được ghi nhận vào trang <strong>Theo dõi sự cố ERP</strong> cùng ảnh chụp câu hỏi và kết quả để quản trị viên đối soát, khắc phục.</p>
						<div style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:8px;padding:10px 12px;max-height:120px;overflow-y:auto;">
							<div style="font-size:11px;font-weight:700;text-transform:uppercase;color:#64748b;margin-bottom:4px;">Câu hỏi của bạn:</div>
							<div data-q style="font-weight:500;white-space:pre-wrap;word-break:break-word;color:#1e293b;"></div>
						</div>
						<div>
							<label style="display:block;font-size:12px;font-weight:600;margin-bottom:5px;color:#334155;">Mô tả lỗi hoặc lý do báo cáo (tùy chọn):</label>
							<textarea data-note rows="3" placeholder="Ví dụ: Sai số lượng tồn kho, thiếu sản phẩm trong bảng, đơn giá không khớp..." style="width:100%;box-sizing:border-box;border-radius:8px;border:1px solid #cbd5e1;background:#fff;color:#182232;padding:8px 10px;font-family:inherit;font-size:13px;resize:vertical;outline:none;"></textarea>
						</div>
					</div>
					<div style="display:flex;justify-content:flex-end;gap:10px;padding:12px 18px;border-top:1px solid #e2e8f0;background:#f8fafc;">
						<button type="button" data-cancel style="border:1px solid #cbd5e1;background:#fff;color:#334155;border-radius:8px;padding:7px 14px;cursor:pointer;font-weight:500;font-size:13px;">Hủy</button>
						<button type="button" data-submit style="border:none;background:#dc2626;color:#fff;border-radius:8px;padding:7px 16px;cursor:pointer;font-weight:600;font-size:13px;">Gửi báo cáo</button>
					</div>
				</div>
			</div>
		`;

		// Adjust for dark mode
		const applyThemeToModal = () => {
			const isDark = document.documentElement.classList.contains('dark');
			const box = el.querySelector('.htmp-crm-box');
			const foot = el.querySelector('.htmp-crm-box > div:last-child');
			const preview = el.querySelector('[data-q]')?.parentElement;
			const textarea = el.querySelector('textarea');
			const cancelBtn = el.querySelector('[data-cancel]');
			if (box) {
				box.style.background = isDark ? '#1e2225' : '#ffffff';
				box.style.color = isDark ? '#edf0f2' : '#182232';
				box.style.borderColor = isDark ? '#30363a' : '#e2e8f0';
			}
			if (foot) {
				foot.style.background = isDark ? '#191c1e' : '#f8fafc';
				foot.style.borderColor = isDark ? '#30363a' : '#e2e8f0';
			}
			if (preview) {
				preview.style.background = isDark ? '#272c30' : '#f8fafc';
				preview.style.borderColor = isDark ? '#30363a' : '#e2e8f0';
			}
			if (textarea) {
				textarea.style.background = isDark ? '#191c1e' : '#fff';
				textarea.style.color = isDark ? '#edf0f2' : '#182232';
				textarea.style.borderColor = isDark ? '#40484f' : '#cbd5e1';
			}
			if (cancelBtn) {
				cancelBtn.style.background = isDark ? '#272c30' : '#fff';
				cancelBtn.style.color = isDark ? '#edf0f2' : '#334155';
				cancelBtn.style.borderColor = isDark ? '#40484f' : '#cbd5e1';
			}
		};

		el.querySelector('[data-close]').addEventListener('click', () => { el.style.display = 'none'; });
		el.querySelector('[data-cancel]').addEventListener('click', () => { el.style.display = 'none'; });
		el.querySelector('.htmp-crm-backdrop').addEventListener('click', (e) => {
			if (e.target === el.querySelector('.htmp-crm-backdrop')) el.style.display = 'none';
		});

		el.querySelector('[data-submit]').addEventListener('click', async () => {
			if (!activeReportTarget) return;
			const submitBtn = el.querySelector('[data-submit]');
			submitBtn.disabled = true;
			submitBtn.textContent = 'Đang gửi…';
			const note = el.querySelector('[data-note]').value.trim();

			try {
				const token = localStorage.getItem('token') || '';
				const response = await fetch('/openai/erp-incidents/report', {
					method: 'POST',
					headers: {
						'Content-Type': 'application/json',
						...(token ? { Authorization: 'Bearer ' + token } : {})
					},
					credentials: 'same-origin',
					body: JSON.stringify({
						chat_id: activeReportTarget.chatId,
						message_id: activeReportTarget.messageId,
						question: activeReportTarget.question,
						answer: activeReportTarget.answer,
						note: note
					})
				});

				if (!response.ok) throw new Error('HTTP ' + response.status);

				el.style.display = 'none';
				if (activeReportTarget.btn) {
					activeReportTarget.btn.disabled = true;
					activeReportTarget.btn.innerHTML = `
						<span style="color:#059669;font-weight:600;display:inline-flex;align-items:center;gap:3px;">
							<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"/></svg>
							Đã báo cáo
						</span>
					`;
				}
				window.alert('Đã gửi báo cáo sự cố thành công! Quản trị viên sẽ kiểm tra lại.');
			} catch (err) {
				window.alert('Không thể gửi báo cáo sự cố: ' + err.message);
			} finally {
				submitBtn.disabled = false;
				submitBtn.textContent = 'Gửi báo cáo';
			}
		});

		document.body.appendChild(el);
		reportModalEl = el;
		reportModalEl._applyTheme = applyThemeToModal;
		return reportModalEl;
	}

	function openReportDialog(target) {
		activeReportTarget = target;
		const modal = getOrCreateReportModal();
		modal._applyTheme();
		modal.querySelector('[data-q]').textContent = target.question || '(Không tìm thấy nội dung câu hỏi)';
		modal.querySelector('[data-note]').value = '';
		modal.style.display = 'block';
	}

	function scanReportButtons() {
		// Tìm các nút thao tác phản hồi (copy-response-button)
		for (const copyBtn of document.querySelectorAll('.copy-response-button')) {
			const parent = copyBtn.parentElement;
			if (!parent || parent.querySelector('.htmp-report-btn')) continue;

			const reportBtn = document.createElement('button');
			reportBtn.type = 'button';
			reportBtn.className = 'htmp-report-btn p-1.5 hover:bg-black/5 dark:hover:bg-white/5 rounded-lg text-gray-400 hover:text-red-500 dark:hover:text-red-400 transition inline-flex items-center gap-1 text-xs';
			reportBtn.title = 'Báo cáo câu trả lời sai hoặc có sự cố';
			reportBtn.setAttribute('aria-label', 'Báo cáo kết quả sai');
			reportBtn.innerHTML = `
				<svg class="w-3.5 h-3.5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
					<path d="M4 15s1-1 4-1 5 2 8 2 4-1 4-1V3s-1 1-4 1-5-2-8-2-4 1-4 1z"></path>
					<line x1="4" y1="22" x2="4" y2="15"></line>
				</svg>
				<span class="report-text" style="font-size:11.5px;font-weight:500;">Báo cáo</span>
			`;

			reportBtn.addEventListener('click', (e) => {
				e.stopPropagation();
				const messageItem = copyBtn.closest('[role="listitem"]') || copyBtn.closest('.chat-assistant') || copyBtn.closest('[id^="message-container"]');
				const prose = messageItem ? messageItem.querySelector('.markdown-prose') : null;
				const answerText = (prose ? prose.innerText : (messageItem ? messageItem.innerText : '')).trim();

				// Tìm câu hỏi người dùng gần nhất phía trước
				let questionText = '';
				let prev = messageItem ? messageItem.previousElementSibling : null;
				while (prev) {
					if (!prev.querySelector('.copy-response-button') && prev.innerText.trim()) {
						questionText = prev.innerText.trim();
						questionText = questionText.replace(/^markdown\s+Thu gọn\s+Sao chép\s+/i, '').trim();
						break;
					}
					prev = prev.previousElementSibling;
				}

				// Lấy Chat ID từ URL
				let chatId = '';
				const pathParts = window.location.pathname.split('/');
				if (pathParts[1] === 'c' || pathParts[1] === 's') {
					chatId = pathParts[2] || '';
				}

				// Lấy Message ID
				const infoBtn = messageItem ? messageItem.querySelector('[id^="info-"]') : null;
				const messageId = infoBtn ? infoBtn.id.replace('info-', '') : '';

				openReportDialog({
					btn: reportBtn,
					chatId: chatId,
					messageId: messageId,
					question: questionText,
					answer: answerText
				});
			});

			parent.appendChild(reportBtn);
		}
	}

	function scan() {
		if (!document.body) return;
		// The admin entry exists only in the account menu for administrators.
		// Clone its styling, but let the server enforce access to incident data.
		for (const adminLink of document.querySelectorAll('a[href="/admin"]')) {
			if (!adminLink.className.includes('h-[1.6875rem]') || !adminLink.parentElement) continue;
			if (adminLink.parentElement.querySelector('[data-htmp-erp-incidents]')) continue;
			const incidentLink = adminLink.cloneNode(true);
			incidentLink.href = '/openai/erp-incidents-page';
			incidentLink.dataset.htmpErpIncidents = 'true';
			incidentLink.setAttribute('aria-label', 'Theo dõi sự cố ERP');
			const label = incidentLink.querySelector('div.truncate');
			if (!label) continue;
			label.textContent = 'Theo dõi sự cố ERP';
			adminLink.insertAdjacentElement('afterend', incidentLink);
		}
		createToolbar();
		for (const { id, link } of chatRows()) {
			const row = link.parentElement;
			if (!row) continue;
			let checkbox = [...row.querySelectorAll('[data-htmp-chat-id]')].find((node) => node.dataset.htmpChatId === id);
			if (!checkbox) {
				checkbox = document.createElement('input');
				checkbox.type = 'checkbox';
				checkbox.dataset.htmpChatId = id;
				checkbox.className = 'htmp-chat-history-checkbox';
				checkbox.setAttribute('aria-label', `Chọn hội thoại ${link.title || link.textContent.trim()}`);
				Object.assign(checkbox.style, {
					width: '16px',
					height: '16px',
					flex: '0 0 16px',
					margin: '0 5px 0 7px',
					accentColor: '#dc2626',
					cursor: 'pointer',
				});
				checkbox.addEventListener('click', (event) => event.stopPropagation());
				checkbox.addEventListener('change', () => setSelected(id, checkbox.checked));
				row.insertBefore(checkbox, link);
			}
			checkbox.checked = selected.has(id);
		}
		updateToolbar();
		scanReportButtons();
	}

	const start = () => {
		scan();
		new MutationObserver(scan).observe(document.body, { childList: true, subtree: true });
	};
	if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
	else start();
})();
