#!/usr/bin/env python3
"""Test DO and FCST comparison via Playwright CDP on Open WebUI."""

import json
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

EVIDENCE_DIR = Path("docs/evidence/ERP-UI-DO-FCST-20261110")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

PROMPT = "So sánh DO và FCST hiện tại với bản trước của mã QC7-5146-000: số lượng tăng hay giảm bao nhiêu?"

def wait_for_response(page, max_sec=60):
    for i in range(max_sec):
        time.sleep(1)
        try:
            continue_btn = page.locator('#continue-response-button')
            if continue_btn.count() > 0 and continue_btn.last.is_visible():
                break
            stop_btn = page.locator('button[aria-label="Stop response"], button[aria-label="Stop"]')
            if i > 4 and stop_btn.count() == 0:
                time.sleep(1)
                break
        except Exception:
            pass
    time.sleep(2)

def main():
    print("Connecting to Edge via CDP...")
    with sync_playwright() as p:
        browser = p.chromium.connect_over_cdp("http://127.0.0.1:19223")
        page = None
        for c in browser.contexts:
            for pg in c.pages:
                if "Open WebUI" in pg.title():
                    page = pg
                    break
            if page:
                break
        if not page:
            print("ERROR: Open WebUI not found!")
            return

        print(f"Connected to page: {page.title()} ({page.url})")
        page.goto("http://192.168.31.10/", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)

        # Select HTMP ERP model
        sel = page.locator('#model-selector-model-button').first
        sel.wait_for(timeout=30000)
        if 'HTMP ERP' not in sel.inner_text():
            print("Selecting HTMP ERP...")
            sel.click()
            page.get_by_text('HTMP ERP', exact=True).last.click(timeout=10000)
            page.wait_for_timeout(1000)

        print(f"Sending prompt: {PROMPT}")
        t0 = time.time()
        chat_box = page.locator('#chat-input')
        chat_box.fill(PROMPT)
        chat_box.press('Enter')

        wait_for_response(page, 60)
        dur = round(time.time() - t0, 1)
        print(f"Completed in {dur}s")

        shot_path = EVIDENCE_DIR / "do_fcst_comparison_result.png"
        page.screenshot(path=str(shot_path), full_page=False)
        print(f"Screenshot saved: {shot_path}")

        body_text = page.locator('body').inner_text()
        chat_part = body_text.split('Chat Conversation', 1)[-1] if 'Chat Conversation' in body_text else body_text
        print("\n=== ASSISTANT RESPONSE ===")
        print(chat_part[-1500:])

if __name__ == "__main__":
    main()

