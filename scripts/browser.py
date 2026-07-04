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

        print("Opening LinkedIn login page...")
        page.goto("https://www.linkedin.com/login", timeout=60000)
        time.sleep(4)

        print(f"URL: {page.url}")

        email_inputs = page.locator("input[type='email']").all()
        email_input = None
        for inp in email_inputs:
            if inp.is_visible():
                email_input = inp
                break

        password_inputs = page.locator("input[type='password']").all()
        password_input = None
        for inp in password_inputs:
            if inp.is_visible():
                password_input = inp
                break

        if email_input and password_input:
            email_input.fill(LINKEDIN_USERNAME)
            random_delay()
            password_input.fill(LINKEDIN_PASSWORD)
            random_delay()

            time.sleep(3)
            print(f"After fill: {page.url}")

            if "/feed" in page.url:
                print("Login succeeded during fill!")
            else:
                try:
                    page.click("button[type=submit]", timeout=5000)
                except:
                    print("Submit button click timed out, checking URL...")
                time.sleep(3)
                print(f"After submit: {page.url}")

            if "checkpoint" in page.url or "challenge" in page.url:
                print("Challenge page detected. Please solve manually.")
                browser.close()
                return

            if "feed" in page.url:
                print("Login successful!")
            else:
                print(f"Login issue. URL: {page.url}")
                browser.close()
                return
        else:
            print("Login fields not found!")
            browser.close()
            return

        page.goto("https://www.linkedin.com/mynetwork/", timeout=30000)
        time.sleep(4)

        accept_buttons = page.query_selector_all("button:has-text('Accept')")
        if not accept_buttons:
            accept_buttons = page.query_selector_all("[aria-label*='Accept']")

        print(f"Pending requests: {len(accept_buttons)}")
        for btn in accept_buttons[:MAX_ACCEPT_PER_RUN]:
            try:
                btn.click()
                random_delay()
                total_accepted += 1
                print(f"Accepted {total_accepted}")

                msg_btn = page.query_selector("button:has-text('Message')")
                if msg_btn:
                    msg_btn.click()
                    time.sleep(2)
                    editor = page.query_selector("div[role='textbox'], div[contenteditable='true']")
                    if editor:
                        editor.fill(get_message())
                        random_delay()
                        send_btn = page.query_selector("button:has-text('Send')")
                        if send_btn:
                            send_btn.click()
                            total_messaged += 1
                            print(f"Messaged {total_messaged}")
                            random_delay()
                    close_btn = page.query_selector("button[aria-label='Close']")
                    if close_btn:
                        close_btn.click()
                        time.sleep(1)
            except Exception as e:
                print(f"Error: {e}")

        browser.close()

    print(f"\nDone. Accepted: {total_accepted}, Messaged: {total_messaged}")
