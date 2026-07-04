import time, random
from config import LINKEDIN_EMAIL, LINKEDIN_PASSWORD, MAX_ACCEPT_PER_RUN, MIN_DELAY_SEC, MAX_DELAY_SEC
from message_template import get_message
from playwright.sync_api import sync_playwright

def random_delay():
    time.sleep(random.uniform(MIN_DELAY_SEC, MAX_DELAY_SEC))

def run():
    if not LINKEDIN_EMAIL or not LINKEDIN_PASSWORD:
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

        print("Logging in...")
        page.goto("https://www.linkedin.com/login", timeout=30000)
        page.fill("#username", LINKEDIN_EMAIL)
        random_delay()
        page.fill("#password", LINKEDIN_PASSWORD)
        random_delay()
        page.click("button[type=submit]")
        time.sleep(5)

        if "checkpoint" in page.url or "challenge" in page.url:
            print("Login blocked! Challenge/2FA page detected. Skipping run.")
            browser.close()
            return

        if "feed" not in page.url and "mynetwork" not in page.url:
            print(f"Login may have failed. Current URL: {page.url}")
            browser.close()
            return

        print("Login successful.")

        page.goto("https://www.linkedin.com/mynetwork/", timeout=30000)
        time.sleep(4)

        accept_buttons = page.query_selector_all("button[aria-label^='Accept']")
        if not accept_buttons:
            accept_buttons = page.query_selector_all("button:has-text('Accept')")

        print(f"Pending requests found: {len(accept_buttons)}")
        to_accept = accept_buttons[:MAX_ACCEPT_PER_RUN]
        accepted_urns = []

        for btn in to_accept:
            try:
                name_el = page.evaluate("""
                    (btn) => {
                        const card = btn.closest('li') || btn.closest('div');
                        if (!card) return '';
                        const spans = card.querySelectorAll('span');
                        for (const s of spans) {
                            if (s.textContent.trim().length > 3) return s.textContent.trim();
                        }
                        return '';
                    }
                """, btn)
                btn.click()
                random_delay()
                total_accepted += 1
                print(f"  Accepted: {name_el or 'unknown'}")

                msg_btn = page.query_selector("button:has-text('Message')")
                if msg_btn:
                    msg_btn.click()
                    time.sleep(2)
                    textarea = page.query_selector("div[role='textbox']")
                    if textarea:
                        textarea.fill(get_message())
                        random_delay()
                        send_btn = page.query_selector("button:has-text('Send')")
                        if send_btn:
                            send_btn.click()
                            total_messaged += 1
                            print(f"  Message sent to: {name_el or 'unknown'}")
                            random_delay()
                    close_btn = page.query_selector("button[aria-label='Close']")
                    if close_btn:
                        close_btn.click()
                        time.sleep(1)

            except Exception as e:
                print(f"  Error on accept: {e}")
                continue

        browser.close()

    print(f"\nDone. Accepted: {total_accepted}, Messaged: {total_messaged}")
