#!/usr/bin/env python3
"""Test Bùi Thị Mai's exact 2-turn purchase order pricing incident via Playwright CDP on Open WebUI."""

import json
import os
import sys
import time
from pathlib import Path
from playwright.sync_api import sync_playwright

EVIDENCE_DIR = Path("docs/evidence/ERP-UI-MAI-INCIDENT-20261109")
EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)

TURN_1_PROMPT = "em check cho chị giá nhập mua của mã nhựa ABS014B này gần đây nhất"
TURN_2_PROMPT = "em check cho chị toàn bộ lịch sự giá mua mã này từ đâu năm 2026 đến giờ"

def wait_for_response_completion(page, max_wait_sec=60):
    completed = False
    for i in range(max_wait_sec):
        time.sleep(1)
        try:
            # Check for continue response button or absence of stop button
            continue_btn = page.locator('#continue-response-button')
            if continue_btn.count() > 0 and continue_btn.last.is_visible():
                completed = True
                break
            # Also check if stop button disappeared after at least 3 seconds
            stop_btn = page.locator('button[aria-label="Stop response"], button[aria-label="Stop"]')
            if i > 4 and stop_btn.count() == 0:
                # Wait an extra second to be sure
                time.sleep(1)
                completed = True
                break
        except Exception:
            pass
    time.sleep(2)
    return completed

def get_last_assistant_message(page):
    # Locate all assistant message containers
    messages = page.locator('.chat-message, div[data-role="assistant"], .message-content, .prose')
    count = messages.count()
    if count > 0:
        return messages.last.inner_text().strip()
    
    # Fallback to body text extraction
    body_text = page.locator('body').inner_text()
    return body_text

def main():
    print("Connecting to Edge browser via CDP on http://127.0.0.1:19223...")
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
            print("ERROR: Open WebUI tab not found via CDP!")
            sys.exit(1)
            
        print(f"Connected to page: {page.title()} ({page.url})")
        
        # 1. Start fresh chat
        page.goto("http://192.168.31.10/", wait_until="domcontentloaded", timeout=30000)
        page.wait_for_timeout(2000)
        
        # Ensure model is HTMP ERP
        sel = page.locator('#model-selector-model-button').first
        sel.wait_for(timeout=30000)
        if 'HTMP ERP' not in sel.inner_text():
            print("Selecting HTMP ERP model...")
            sel.click()
            page.get_by_text('HTMP ERP', exact=True).last.click(timeout=10000)
            page.wait_for_timeout(1000)
            
        # -------------------------------------------------------------
        # TURN 1
        # -------------------------------------------------------------
        print(f"\n[TURN 1] Sending prompt: {TURN_1_PROMPT}")
        t0 = time.time()
        chat_box = page.locator('#chat-input')
        chat_box.fill(TURN_1_PROMPT)
        chat_box.press('Enter')
        
        wait_for_response_completion(page, 60)
        dur1 = round(time.time() - t0, 1)
        print(f"[TURN 1] Completed in {dur1}s")
        
        # Screenshot Turn 1
        shot1_path = EVIDENCE_DIR / "turn1_abs014b_latest_price.png"
        page.screenshot(path=str(shot1_path), full_page=False)
        print(f"[TURN 1] Screenshot saved: {shot1_path}")
        
        turn1_text = get_last_assistant_message(page)
        print(f"[TURN 1] Assistant message:\n{turn1_text}\n" + "="*60)
        
        # -------------------------------------------------------------
        # TURN 2 (In same chat, testing multi-turn coreference)
        # -------------------------------------------------------------
        print(f"\n[TURN 2] Sending prompt: {TURN_2_PROMPT}")
        t0 = time.time()
        chat_box = page.locator('#chat-input')
        chat_box.fill(TURN_2_PROMPT)
        chat_box.press('Enter')
        
        wait_for_response_completion(page, 60)
        dur2 = round(time.time() - t0, 1)
        print(f"[TURN 2] Completed in {dur2}s")
        
        # Screenshot Turn 2
        shot2_path = EVIDENCE_DIR / "turn2_abs014b_year_history.png"
        page.screenshot(path=str(shot2_path), full_page=False)
        print(f"[TURN 2] Screenshot saved: {shot2_path}")
        
        turn2_text = get_last_assistant_message(page)
        print(f"[TURN 2] Assistant message:\n{turn2_text}\n" + "="*60)
        
        result_record = {
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "turn1": {
                "prompt": TURN_1_PROMPT,
                "duration_seconds": dur1,
                "screenshot": str(shot1_path),
                "response_text": turn1_text
            },
            "turn2": {
                "prompt": TURN_2_PROMPT,
                "duration_seconds": dur2,
                "screenshot": str(shot2_path),
                "response_text": turn2_text
            }
        }
        
        with open(EVIDENCE_DIR / "test_results.json", "w", encoding="utf-8") as f:
            json.dump(result_record, f, ensure_ascii=False, indent=2)
            
        print("\nTest completed successfully! Results written to docs/evidence/ERP-UI-MAI-INCIDENT-20261109/")

if __name__ == "__main__":
    main()

