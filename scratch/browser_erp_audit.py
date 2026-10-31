"""Interactive browser audit; credentials are read from the terminal, never stored."""
import getpass
import ast
import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

email = input('Email: ').strip()
password = getpass.getpass('Password: ')
with sync_playwright() as p:
    browser = p.chromium.launch(executable_path='/tmp/htmp-playwright-browser/chrome-linux/headless_shell', headless=True, args=['--no-sandbox'])
    context = browser.new_context(ignore_https_errors=True, viewport={'width': 1440, 'height': 900})
    page = context.new_page()
    page.goto('https://192.168.31.10/auth', wait_until='networkidle', timeout=30000)
    print('LOGIN INPUTS', page.locator('input').evaluate_all("es => es.map(e => ({type:e.type,placeholder:e.placeholder,name:e.name}))"), flush=True)
    page.locator('input[type=email], input[autocomplete=username]').first.fill(email)
    page.locator('input[type=password]').first.fill(password)
    password = None
    page.locator('button[type=submit]').first.click()
    page.wait_for_timeout(5000)
    tree = ast.parse(Path('scratch/test_18_container.py').read_text())
    questions = next(ast.literal_eval(node.value) for node in tree.body
                     if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'questions' for t in node.targets))
    output = Path('scratch') / ('ui_erp_18_' + time.strftime('%Y%m%d_%H%M%S') + '.jsonl')
    print('EVIDENCE', output, flush=True)
    for i, raw in enumerate(questions, 1):
        question = raw.split('. ', 1)[-1]
        try:
            page.goto('https://192.168.31.10/', wait_until='domcontentloaded', timeout=30000)
            page.locator('#model-selector-model-button').first.wait_for(timeout=30000)
            page.locator('#model-selector-model-button').first.click()
            page.get_by_text('HTMP ERP', exact=True).last.click(timeout=10000)
            selected = page.locator('#model-selector-model-button').first.inner_text()
            if 'HTMP ERP' not in selected:
                raise RuntimeError('Wrong model selected')
            page.locator('#chat-input').fill(question)
            started = time.monotonic()
            page.locator('#chat-input').press('Enter')
            page.locator('#continue-response-button').last.wait_for(state='visible', timeout=120000)
            page.wait_for_timeout(1000)
            body = page.locator('body').inner_text()
            answer = body.split('Chat Conversation', 1)[-1]
            frames = []
            for frame in page.frames[1:]:
                try:
                    frames.append(frame.locator('body').inner_text(timeout=2000))
                except Exception:
                    frames.append('[frame unavailable]')
            result = {'id': i, 'question': question, 'model': selected.strip(), 'url': page.url,
                      'seconds': round(time.monotonic()-started, 1), 'visible': answer, 'frames': frames}
            print('Q%02d OK %.1fs %s' % (i, result['seconds'], answer[-250:].replace('\n', ' ')), flush=True)
        except Exception as exc:
            result = {'id': i, 'question': question, 'error': str(exc)[:400], 'url': page.url}
            print('Q%02d ERROR %s' % (i, str(exc)[:200]), flush=True)
        with output.open('a', encoding='utf-8') as out:
            out.write(json.dumps(result, ensure_ascii=False) + '\n')
    browser.close()
