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
	}

	const start = () => {
		scan();
		new MutationObserver(scan).observe(document.body, { childList: true, subtree: true });
	};
	if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', start, { once: true });
	else start();
})();
