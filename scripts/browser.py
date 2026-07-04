import time, random, os
from config import LINKEDIN_USERNAME, LINKEDIN_PASSWORD, MAX_ACCEPT_PER_RUN, MIN_DELAY_SEC, MAX_DELAY_SEC
from message_template import get_message
from playwright.sync_api import sync_playwright

def random_delay():
    time.sleep(random.uniform(MIN_DELAY_SEC, MAX_DELAY_SEC))

def run():
    if not LINKEDIN_USERNAME or not LINKEDIN_PASSWORD:
        print("LinkedIn credentials not configured.")
        return

    total_accepted = 0
    total_messaged = 0

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("Navigating to LinkedIn...")
        page.goto("https://www.linkedin.com/", timeout=60000, wait_until="domcontentloaded")
        time.sleep(3)

        current_url = page.url
        print(f"Current URL: {current_url}")

        if "/login" in current_url:
            print("Already on login page. Filling credentials...")
        else:
            signin_btn = page.query_selector("a[href*='login'], a:has-text('Sign in'), a:has-text('Sign In')")
            if signin_btn:
                print("Clicking Sign in button...")
                signin_btn.click()
                time.sleep(3)

        page.wait_for_selector("input[name='session_key'], input[name='username'], #username", timeout=20000)

        username_input = page.query_selector("input[name='session_key']") or page.query_selector("#username")
        password_input = page.query_selector("input[name='session_password']") or page.query_selector("#password")

        if not username_input or not password_input:
            print("Could not find login fields. Page title: " + page.title())
            page.screenshot(path="debug_login.png")
            browser.close()
            return

        username_input.fill(LINKEDIN_USERNAME)
        random_delay()
        password_input.fill(LINKEDIN_PASSWORD)
        random_delay()
        page.click("button[type=submit]")
        time.sleep(5)

        current_url = page.url
        print(f"After login URL: {current_url}")

        if "checkpoint" in current_url or "challenge" in current_url:
            print("Login blocked! Challenge/2FA page detected.")
            page.screenshot(path="debug_challenge.png")
            browser.close()
            return

        if "feed" not in current_url and "mynetwork" not in current_url:
            page.screenshot(path="debug_login_fail.png")
            print(f"Login may have failed. Page title: {page.title()}")
            browser.close()
            return

        print("Login successful.")

        page.goto("https://www.linkedin.com/mynetwork/", timeout=30000, wait_until="domcontentloaded")
        time.sleep(4)

        accept_buttons = page.query_selector_all("button:has-text('Accept')")
        if not accept_buttons:
            accept_buttons = page.query_selector_all("[aria-label*='Accept']")
        if not accept_buttons:
            accept_buttons = page.query_selector_all("button:has-text('Accept'), [aria-label*='accept']")

        print(f"Pending requests found: {len(accept_buttons)}")
        to_accept = accept_buttons[:MAX_ACCEPT_PER_RUN]

        for i, btn in enumerate(to_accept):
            try:
                btn.click()
                random_delay()
                total_accepted += 1
                print(f"  Accepted ({i+1}/{len(to_accept)})")

                msg_btn = page.query_selector("button:has-text('Message')")
                if msg_btn:
                    msg_btn.click()
                    time.sleep(2)
                    editor = page.query_selector("div[contenteditable='true'][role='textbox'], div.editor, div[data-placeholder]")
                    if editor:
                        editor.fill(get_message())
                        random_delay()
                        send_btn = page.query_selector("button:has-text('Send')")
                        if send_btn:
                            send_btn.click()
                            total_messaged += 1
                            print(f"  Message sent ({total_messaged})")
                            random_delay()
                    close_btn = page.query_selector("button[aria-label='Close'], button:has-text('Close')")
                    if close_btn:
                        close_btn.click()
                        time.sleep(1)
                else:
                    print("  No message button found, skipping message")

            except Exception as e:
                print(f"  Error: {e}")
                continue

        browser.close()

    print(f"\nDone. Accepted: {total_accepted}, Messaged: {total_messaged}")
