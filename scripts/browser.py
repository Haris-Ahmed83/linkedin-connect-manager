import time, random, os, json, sys, re
from config import LINKEDIN_USERNAME, LINKEDIN_PASSWORD, MAX_ACCEPT_PER_RUN, MIN_DELAY_SEC, MAX_DELAY_SEC
from message_template import get_message
from playwright.sync_api import sync_playwright, TimeoutError as PwTimeout

PROFILE_DIR = "E:\\Codes\\Linkdin-Github\\linkedin_profile"
TRACKING_FILE = "E:\\Codes\\linkedin-connect-manager\\tracking.json"

def random_delay():
    time.sleep(random.uniform(MIN_DELAY_SEC, MAX_DELAY_SEC))

def clean_name(name):
    return re.sub(r'[^\w\s\-\'\.]', '', name).strip()

def load_tracking():
    if os.path.exists(TRACKING_FILE):
        with open(TRACKING_FILE, "r") as f:
            return json.load(f)
    return {"messaged": []}

def save_tracking(data):
    with open(TRACKING_FILE, "w") as f:
        json.dump(data, f, indent=2)

def sp(text):
    safe = text.encode(sys.stdout.encoding, errors='replace').decode(sys.stdout.encoding)
    print(safe)

def get_all_connections(page):
    """Scrape LinkedIn search for all 1st degree connections."""
    try:
        page.goto("https://www.linkedin.com/search/results/people/?network=%5B%22F%22%5D", timeout=30000)
        page.wait_for_timeout(6000)
        for _ in range(5):
            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            page.wait_for_timeout(1500)
        connections = page.evaluate("""() => {
            const items = [];
            const seen = new Set();
            const allLinks = document.querySelectorAll('a[href*="/in/"]');
            for (const a of allLinks) {
                if (a.offsetParent === null) continue;
                const href = a.href || '';
                if (!href || seen.has(href)) continue;
                seen.add(href);
                const text = (a.textContent || '').trim();
                // Split by newline, take first non-empty line as name
                const lines = text.split('\\n').filter(l => l.trim());
                let name = '';
                for (const line of lines) {
                    const t = line.trim();
                    if (t && t.length > 3 && t.length < 35 && !/\\d/.test(t) && !t.includes('•') && !/^(Message|Connect|Follow|Pending)/i.test(t)) {
                        name = t;
                        break;
                    }
                }
                if (!name) continue;
                // Skip locations and generic text
                if (/^(Lahore|Karachi|Islamabad|Multan|Punjab|Location|Lead|Remote|On-site)/i.test(name)) continue;
                items.push({name: name, href: href.startsWith('http') ? href : 'https://www.linkedin.com' + href});
            }
            return items;
        }""")
        return connections
    except Exception as e:
        sp(f"    get_all_connections error: {e}")
        return []

def click_safe(page, selector, timeout=5000):
    """Click an element only if it's visible and enabled."""
    try:
        el = page.locator(selector).first
        if el.is_visible(timeout=timeout):
            el.click()
            return True
    except:
        pass
    return False

def send_welcome(page, name, profile_url, headline="", sender_name="Muhammad Haris"):
    """
    Send welcome message via LinkedIn messaging page.
    Uses the 'New message' modal which reliably enables the Send button for connections.
    """
    sp(f"    Messaging {name}...")

    # Navigate to messaging page
    try:
        page.goto("https://www.linkedin.com/messaging", timeout=30000)
        page.wait_for_timeout(3000)
    except:
        sp(f"    Failed to load messaging page")
        return False

    # Click 'New message' button
    if not click_safe(page, "button:has-text('New message')", timeout=4000):
        # Maybe already in a conversation — try finding editor
        editors = page.locator("div[role='textbox']:visible").all()
        if editors:
            msg = get_message(name, headline)
            editors[0].type(msg, delay=10)
            page.wait_for_timeout(2000)
            if click_safe(page, "button:has-text('Send')", timeout=2000) and page.locator("button:has-text('Send')").first.is_enabled():
                sp(f"    Sent!")
                return True
        sp(f"    No New message button available")
        return False

    page.wait_for_timeout(2000)

    # Find the recipient input
    recipient = page.locator("input[placeholder*='name']").first
    if not recipient.is_visible(timeout=5000):
        sp(f"    Recipient input not found")
        return False

    # Type the person's first name to search
    first_name = name.split()[0] if name.split() else name
    recipient.fill(first_name)
    page.wait_for_timeout(2500)

    # Wait for dropdown to appear and select matching person
    try:
        page.wait_for_selector("[id*='mn-dialog'] li:visible, [role='option']:visible", timeout=5000)
    except:
        pass

    results = page.locator("[id*='mn-dialog'] li:visible, [role='option']:visible").all()
    selected = False
    for r in results:
        txt = (r.text_content() or "").lower()
        if first_name.lower() in txt:
            # Click the inner clickable element (avoid li click issues)
            inner = r.locator("a, span, div").first
            if inner.is_visible(timeout=1000):
                inner.click()
            else:
                r.click()
            selected = True
            page.wait_for_timeout(2000)
            break

    if not selected and results:
        inner = results[0].locator("a, span, div").first
        if inner.is_visible(timeout=1000):
            inner.click()
        else:
            results[0].click()
        selected = True
        page.wait_for_timeout(2000)

    if not selected:
        sp(f"    No matching contact found in dropdown")
        return False

    # Wait and press Enter to confirm selection
    page.wait_for_timeout(1500)
    page.keyboard.press("Enter")
    page.wait_for_timeout(2000)

    # Find the editor using multiple selectors
    editor = None
    for sel in ["div[role='textbox']:visible", "[contenteditable='true']:visible",
                "div[aria-label*='message']:visible", ".msg-form__contenteditable:visible"]:

        if editor is None or not editor.is_visible(timeout=1000):
            try:
                e = page.locator(sel).first
                if e.is_visible(timeout=3000):
                    editor = e
                    break
            except:
                pass

    if not editor or not editor.is_visible(timeout=2000):
        sp(f"    Editor not found")
        try:
            page.screenshot(path=os.path.join(os.path.dirname(PROFILE_DIR), "debug_editor_fail.png"))
        except:
            pass
        return False

    # Close any typeahead overlay that might block interaction
    page.keyboard.press("Escape")
    page.wait_for_timeout(500)

    # Focus and type the message character by character (triggers React state)
    msg = get_message(name, headline)
    editor.focus()
    page.wait_for_timeout(300)
    editor.type(msg, delay=8)
    page.wait_for_timeout(2000)

    # Check if Send button is enabled
    send_btn = page.locator("button:has-text('Send')").first
    if send_btn.is_visible(timeout=3000):
        if send_btn.is_enabled():
            send_btn.click()
            sp(f"    Sent!")
            return True
        else:
            sp(f"    Send button disabled (not a connection yet)")
            return False
    else:
        sp(f"    Send button not visible")
        return False

def get_profile_url_from_accept_btn(page, btn):
    """Extract profile URL from an accept button's parent card."""
    try:
        return page.evaluate("""(btn) => {
            let el = btn;
            for (let i = 0; i < 8; i++) { if (el.parentElement) el = el.parentElement; }
            const links = el.querySelectorAll('a[href*="/in/"]');
            for (const a of links) { const h = a.getAttribute('href') || ''; if (h) return h.startsWith('http') ? h : 'https://www.linkedin.com' + h; }
            return '';
        }""", btn)
    except:
        return ""

def extract_person_info(page, btn):
    """Extract name and headline from an accept button."""
    try:
        return page.evaluate("""(btn) => {
            let el = btn;
            for (let i = 0; i < 5; i++) { if (el.parentElement) el = el.parentElement; }
            const spans = el.querySelectorAll('span:not(:has(*))');
            const texts = [];
            for (const s of spans) { const t = (s.textContent || '').trim(); if (t && t.length > 2 && t.length < 60) texts.push(t); }
            return { name: texts[0] || '', headline: texts[1] || '' };
        }""", btn)
    except:
        return {"name": "", "headline": ""}

def get_sent_page_people(page):
    """Get list of people from the sent invitations page."""
    return page.evaluate("""() => {
        const items = [];
        const allLinks = document.querySelectorAll('a[href*="/in/"]');
        for (const a of allLinks) {
            if (a.offsetParent === null) continue;
            const href = a.getAttribute('href') || '';
            if (!href) continue;
            const parent = a.closest('li') || a.parentElement;
            const parentText = parent ? (parent.innerText || '') : '';
            const lines = parentText.split('\\n').filter(l => l.trim());
            const name = lines[0] || '';
            if (name && name.length > 1 && name.length < 40) {
                const fullHref = href.startsWith('http') ? href : 'https://www.linkedin.com' + href;
                items.push({name: name, href: fullHref, headline: lines[1] || ''});
            }
        }
        return items;
    }""")

def accept_and_message_incoming(page, tracking, btn):
    """Accept an incoming request and send welcome message."""
    try:
        info = extract_person_info(page, btn)
        name = info.get("name", "")
        headline = info.get("headline", "")
        sp(f"    Accepting: {name} | {headline}")

        btn.click()
        random_delay()

        url = get_profile_url_from_accept_btn(page, btn)
        if url:
            success = send_welcome(page, name, url, headline)
            if success:
                tracking.setdefault("messaged", []).append(name)
                return 1
        else:
            sp(f"    No profile URL found for {name}")
        return 0
    except Exception as e:
        sp(f"    Error accepting: {e}")
        return 0

def check_and_message_sent_page(page, tracking, now_ts=None):
    """Check sent page for newly accepted + message un-messaged people.
    If now_ts is provided, respects failed_retry cooldown (24h).
    """
    sp("Checking sent invitations for newly accepted connections...")
    page.goto("https://www.linkedin.com/mynetwork/invitation-manager/sent/", timeout=30000)
    page.wait_for_timeout(5000)

    current_sent = get_sent_page_people(page)
    prev_sent = tracking.get("prev_sent", [])
    messaged_clean = {clean_name(m) for m in tracking.get("messaged", [])}

    # People who were in prev_sent but LEFT the sent page = newly accepted
    newly_accepted = [p for p in prev_sent
        if clean_name(p["name"]) not in {clean_name(c["name"]) for c in current_sent}
        and clean_name(p["name"]) not in messaged_clean]

    all_to_msg = list(newly_accepted)

    # Filter out people on failed_retry cooldown (24h)
    if now_ts:
        failed = tracking.get("failed_retry", {})
        all_to_msg = [p for p in all_to_msg
            if clean_name(p["name"]) not in failed or
            now_ts - failed.get(clean_name(p["name"]), 0) > 86400]

    sp(f"  Current sent: {len(current_sent)}, Prev sent: {len(prev_sent)}, "
       f"Accepted: {len(newly_accepted)}, To message: {len(all_to_msg)}")

    total = 0
    for person in all_to_msg:
        success = send_welcome(page, person["name"], person["href"], person.get("headline", ""))
        if success:
            tracking.setdefault("messaged", []).append(person["name"])
            total += 1
        else:
            tracking.setdefault("failed_retry", {})[clean_name(person["name"])] = time.time()
        random_delay()

    tracking["prev_sent"] = current_sent
    return total

def check_and_message_connections(page, tracking, now_ts=None):
    """Check connections list for new people and message them."""
    sp("Checking all connections for new people...")
    try:
        current = get_all_connections(page)
        prev = tracking.get("prev_connections", [])

        if not prev:
            sp(f"  First run — saved {len(current)} connections as baseline")
            tracking["prev_connections"] = current
            return 0

        known = {clean_name(c["name"]) for c in prev}
        new_people = [c for c in current if clean_name(c["name"]) not in known]
        messaged_clean = {clean_name(m) for m in tracking.get("messaged", [])}
        new_people = [c for c in new_people if clean_name(c["name"]) not in messaged_clean]

        # Filter failed_retry cooldown (24h)
        if now_ts:
            failed = tracking.get("failed_retry", {})
            new_people = [c for c in new_people
                if clean_name(c["name"]) not in failed or
                now_ts - failed.get(clean_name(c["name"]), 0) > 86400]

        if not new_people:
            tracking["prev_connections"] = current
            return 0

        sp(f"  Found {len(new_people)} new connection(s)!")
        total = 0
        for c in new_people:
            success = send_welcome(page, c["name"], c["href"], "")
            if success:
                tracking.setdefault("messaged", []).append(c["name"])
                total += 1
            else:
                tracking.setdefault("failed_retry", {})[clean_name(c["name"])] = time.time()
            random_delay()

        tracking["prev_connections"] = current
        return total
    except Exception as e:
        sp(f"  Connections check error: {e}")
        return 0

def login_if_needed(page):
    """Check if logged in, otherwise log in."""
    page.goto("https://www.linkedin.com/feed/", timeout=30000, wait_until="domcontentloaded")
    page.wait_for_timeout(4000)

    if "login" in page.url:
        sp("Need to log in...")
        page.goto("https://www.linkedin.com/login", timeout=60000)
        page.wait_for_timeout(5000)

        # Try multiple selectors (LinkedIn changes these)
        email_inp = page.locator("#username, input[name='session_key'], input[type='text'], input[type='email']").first
        pw_inp = page.locator("#password, input[name='session_password'], input[type='password']").first

        if email_inp.is_visible(timeout=5000) and pw_inp.is_visible(timeout=5000):
            email_inp.fill(LINKEDIN_USERNAME)
            random_delay()
            pw_inp.fill(LINKEDIN_PASSWORD)
            random_delay()
            page.keyboard.press("Enter")
            page.wait_for_timeout(8000)
        else:
            sp("Login fields not found - saving screenshot")
            try:
                page.screenshot(path="login_debug.png", full_page=True)
            except:
                pass
            return False

    if "checkpoint" in page.url or "challenge" in page.url:
        sp("Challenge page detected. Waiting...")
        for _ in range(36):
            page.wait_for_timeout(5000)
            if "feed" in page.url:
                sp("Challenge resolved.")
                break

    if "feed" not in page.url:
        sp(f"Login issue: {page.url}")
        return False

    sp("Login successful!")
    return True

def run(oneshot=False):
    if not LINKEDIN_USERNAME or not LINKEDIN_PASSWORD:
        print("LinkedIn credentials not configured.")
        return

    total_accepted = 0
    total_messaged = 0
    tracking = load_tracking()

    # Kill orphaned Playwright Chrome processes that may lock the profile
    try:
        import subprocess
        result = subprocess.run(
            ['wmic', 'process', 'where', 'name="chrome.exe"', 'get', 'ProcessId,CommandLine', '/format:csv'],
            capture_output=True, text=True, timeout=10
        )
        for line in result.stdout.split('\n'):
            if 'linkedin_profile' in line and 'ms-playwright' in line:
                parts = line.strip().split(',')
                for p in parts:
                    if p.strip().isdigit():
                        os.system(f"taskkill /F /PID {p.strip()} >nul 2>&1")
    except:
        pass

    is_ci = os.environ.get("GITHUB_ACTIONS") == "true"
    with sync_playwright() as p:
        context = p.chromium.launch_persistent_context(
            PROFILE_DIR if not is_ci else "",
            headless=is_ci,
            args=[] if is_ci else ["--window-position=-32000,-32000"],
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = context.pages[0] if context.pages else context.new_page()

        if not login_if_needed(page):
            context.close()
            return

        # === PART 1: Accept incoming requests (with 5 min delay) ===
        sp("Checking pending incoming requests...")
        page.goto("https://www.linkedin.com/mynetwork/", timeout=30000)
        page.wait_for_timeout(5000)

        incoming = page.locator("button:has-text('Accept')").all()
        if not incoming:
            incoming = page.locator("[aria-label*='Accept']").all()

        sp(f"Pending incoming requests: {len(incoming)}")

        if incoming:
            sp("Waiting 5 minutes before accepting (to look natural)...")
            time.sleep(300)
            page.goto("https://www.linkedin.com/mynetwork/", timeout=30000)
            page.wait_for_timeout(5000)
            incoming = page.locator("button:has-text('Accept')").all()
            if not incoming:
                incoming = page.locator("[aria-label*='Accept']").all()

        for btn in incoming[:MAX_ACCEPT_PER_RUN]:
            result = accept_and_message_incoming(page, tracking, btn)
            total_accepted += 1 if result == 1 else 0
            total_messaged += result
            random_delay()

        # === PART 2: Check sent page + connections ===
        ts = time.time()
        total_messaged += check_and_message_sent_page(page, tracking, now_ts=ts)
        total_messaged += check_and_message_connections(page, tracking, now_ts=ts)
        save_tracking(tracking)

        # === PART 3: Continuous monitoring (skip in oneshot mode) ===
        if not oneshot:
            sp("\nEntering continuous monitoring mode (Ctrl+C to stop)...")
            incoming_found_at = None
            try:
                while True:
                    time.sleep(60)
                    now = time.time()

                    # Check sent page + connections (with failed_retry filter)
                    total_messaged += check_and_message_sent_page(page, tracking, now_ts=now)
                    total_messaged += check_and_message_connections(page, tracking, now_ts=now)

                    # Check incoming requests
                    page.goto("https://www.linkedin.com/mynetwork/", timeout=30000)
                    page.wait_for_timeout(5000)
                    incoming = page.locator("button:has-text('Accept')").all()
                    if not incoming:
                        incoming = page.locator("[aria-label*='Accept']").all()

                    if incoming:
                        if incoming_found_at is None:
                            incoming_found_at = now
                            sp(f"  Found {len(incoming)} incoming. Will accept in 5 min...")
                        elif now - incoming_found_at >= 300:
                            sp(f"  5 min passed. Accepting {len(incoming)}...")
                            for btn in incoming[:MAX_ACCEPT_PER_RUN]:
                                result = accept_and_message_incoming(page, tracking, btn)
                                total_accepted += 1 if result == 1 else 0
                                total_messaged += result
                                random_delay()
                            incoming_found_at = None
                    else:
                        incoming_found_at = None

                    save_tracking(tracking)

            except KeyboardInterrupt:
                sp("\nMonitoring stopped by user.")
            finally:
                context.close()
        else:
            sp("  Oneshot mode — skipping continuous monitoring")
            context.close()

    sp(f"\nFinal: Accepted: {total_accepted}, Messaged: {total_messaged}")
