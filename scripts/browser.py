import time, random
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
        browser = p.chromium.launch(
            headless=False,
            args=["--window-position=-32000,-32000"]
        )
        context = browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        print("Opening LinkedIn login page...")
        page.goto("https://www.linkedin.com/login", timeout=60000)
        time.sleep(4)
        print(f"URL: {page.url}")

        # Find visible email input
        email_inp = None
        for inp in page.locator("input[type='email']").all():
            if inp.is_visible():
                email_inp = inp
                break
        if not email_inp:
            for inp in page.locator("input:not([type='hidden'])").all():
                t = inp.get_attribute("type")
                if t in ("email", "text", "") and inp.is_visible():
                    email_inp = inp
                    break

        pw_inp = None
        for inp in page.locator("input[type='password']").all():
            if inp.is_visible():
                pw_inp = inp
                break

        if email_inp and pw_inp:
            email_inp.fill(LINKEDIN_USERNAME)
            random_delay()
            pw_inp.fill(LINKEDIN_PASSWORD)
            random_delay()
            print("Credentials filled.")
        else:
            print(f"Fields not found. email={email_inp is not None}, pw={pw_inp is not None}")
            browser.close()
            return

        # Submit: try different methods
        submit_btn = page.locator("button[type=submit]")
        if submit_btn.is_visible() and submit_btn.is_enabled():
            submit_btn.click()
            print("Clicked submit button.")
        else:
            page.keyboard.press("Enter")
            print("Pressed Enter.")

        page.wait_for_timeout(3000)
        for _ in range(10):
            if "feed" in page.url:
                break
            page.wait_for_timeout(1000)

        print(f"After login: {page.url}")

        if "checkpoint" in page.url or "challenge" in page.url:
            print("Challenge page detected.")
            browser.close()
            return

        if "feed" not in page.url:
            print(f"Login issue.")
            browser.close()
            return

        print("Login successful!")

        page.goto("https://www.linkedin.com/mynetwork/", timeout=30000)
        time.sleep(4)

        accept_buttons = page.query_selector_all("button:has-text('Accept')")
        if not accept_buttons:
            accept_buttons = page.query_selector_all("[aria-label*='Accept']")

        print(f"Pending requests: {len(accept_buttons)}")
        for btn in accept_buttons[:MAX_ACCEPT_PER_RUN]:
            try:
                person_name = ""
                person_headline = ""
                try:
                    info = page.evaluate("""
                        (btn) => {
                            let el = btn;
                            for (let i = 0; i < 5; i++) {
                                if (el.parentElement) el = el.parentElement;
                            }
                            const text = el.innerText || '';
                            const spans = el.querySelectorAll('span:not(:has(*))');
                            const texts = [];
                            for (const s of spans) {
                                const t = s.textContent.trim();
                                if (t && t.length > 2 && t.length < 60) texts.push(t);
                            }
                            return { name: texts[0] || '', headline: texts[1] || '' };
                        }
                    """, btn)
                    person_name = info.get("name", "")
                    person_headline = info.get("headline", "")
                except:
                    pass

                print(f"  Person: {person_name} | {person_headline}")

                btn.click()
                random_delay()
                total_accepted += 1

                msg_btn = page.query_selector("button:has-text('Message')")
                if msg_btn:
                    msg_btn.click()
                    time.sleep(2)
                    editor = page.query_selector("div[role='textbox'], div[contenteditable='true']")
                    if editor:
                        msg = get_message(person_name, person_headline)
                        editor.fill(msg)
                        random_delay()
                        send_btn = page.query_selector("button:has-text('Send')")
                        if send_btn:
                            send_btn.click()
                            total_messaged += 1
                            print(f"  Messaged {total_messaged}")
                            random_delay()
                    close_btn = page.query_selector("button[aria-label='Close']")
                    if close_btn:
                        close_btn.click()
                        time.sleep(1)
            except Exception as e:
                print(f"Error: {e}")

        browser.close()

    print(f"\nDone. Accepted: {total_accepted}, Messaged: {total_messaged}")
