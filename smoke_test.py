"""
Simple smoke test: homepage loads with no console errors.
"""

import sys
import time
from playwright.sync_api import sync_playwright

import config


def run_smoke_test(url: str) -> int:
    console_errors = []

    def on_console(msg):
        if msg.type in ("error", "pageerror"):
            console_errors.append(f"{msg.type}: {msg.text}")

    def on_page_error(err):
        console_errors.append(f"pageerror: {err}")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=config.BROWSER_HEADLESS)
        context = browser.new_context(
            viewport={"width": config.VIEWPORT_WIDTH, "height": config.VIEWPORT_HEIGHT}
        )
        page = context.new_page()
        page.on("console", on_console)
        page.on("pageerror", on_page_error)
        page.goto(url, timeout=config.PAGE_LOAD_TIMEOUT, wait_until=config.PAGE_WAIT_UNTIL)
        time.sleep(config.CRAWL_DELAY)
        browser.close()

    if console_errors:
        print("Smoke test failed. Console errors found:")
        for err in console_errors:
            print(f"- {err}")
        return 1

    print("Smoke test passed. No console errors found.")
    return 0


if __name__ == "__main__":
    target_url = config.WEBSITE_URL
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    sys.exit(run_smoke_test(target_url))
