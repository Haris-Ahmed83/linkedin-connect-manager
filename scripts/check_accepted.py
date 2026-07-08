import sys, json, os, re
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
from playwright.sync_api import sync_playwright
from message_template import get_message

PROFILE_DIR = "E:\\Codes\\Linkdin-Github\\linkedin_profile"
TRACKING_FILE = "E:\\Codes\\linkedin-connect-manager\\tracking.json"

def clean_name(name):
    return re.sub(r'[^\w\s\-\'\.]', '', name).strip()

with open(TRACKING_FILE) as f:
    tracking = json.load(f)
messaged_clean = {clean_name(m) for m in tracking.get("messaged", [])}

p = sync_playwright().start()
ctx = p.chromium.launch_persistent_context(PROFILE_DIR, headless=False, args=["--window-position=-32000,-32000"], viewport={"width": 1280, "height": 800})
page = ctx.pages[0] if ctx.pages else ctx.new_page()

page.goto("https://www.linkedin.com/feed/", timeout=30000)
page.wait_for_timeout(4000)

if "login" in page.url:
    print("Need to login")
    ctx.close()
    p.stop()
    exit()

# Go to connections page
page.goto("https://www.linkedin.com/mynetwork/invitation-manager/sent/", timeout=30000)
page.wait_for_timeout(5000)

current_sent = page.evaluate("""() => {
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

prev_sent = tracking.get("prev_sent", [])
newly_accepted = [p for p in prev_sent if clean_name(p["name"]) not in {clean_name(c["name"]) for c in current_sent}]
newly_accepted = [p for p in newly_accepted if clean_name(p["name"]) not in messaged_clean]

print(f"Newly accepted from sent: {len(newly_accepted)}")
for na in newly_accepted:
    print(f"  {na['name']} - {na['href']}")

if newly_accepted:
    for person in newly_accepted:
        print(f"\nMessaging {person['name']}...")
        page.goto("https://www.linkedin.com/messaging", timeout=30000)
        page.wait_for_timeout(4000)

        new_msg = page.locator("button:has-text('New message')").first
        new_msg.click()
        page.wait_for_timeout(3000)

        recipient = page.locator("input[placeholder*='name']").first
        recipient.fill(person["name"].split()[0])
        page.wait_for_timeout(2000)

        results = page.locator("[id*='mn-dialog'] li:visible, [role='option']:visible").all()
        clicked = False
        for r in results:
            txt = r.text_content() or ""
            if person["name"].split()[0].lower() in txt.lower():
                r.click()
                clicked = True
                page.wait_for_timeout(2000)
                break

        if not clicked and results:
            results[0].click()
            clicked = True
            page.wait_for_timeout(2000)

        if clicked:
            editors = page.locator("div[role='textbox']:visible").all()
            if editors:
                msg = get_message(person["name"], person.get("headline", ""))
                editors[0].type(msg, delay=10)
                page.wait_for_timeout(2000)

                send_btn = page.locator("button:has-text('Send')").first
                if send_btn.is_visible(timeout=2000) and send_btn.is_enabled():
                    send_btn.click()
                    print(f"  Sent to {person['name']}!")
                    tracking.setdefault("messaged", []).append(person["name"])
                else:
                    print(f"  Send button disabled for {person['name']}")

    tracking["prev_sent"] = current_sent
    with open(TRACKING_FILE, "w") as f:
        json.dump(tracking, f, indent=2)
else:
    print("No new acceptances detected from sent list.")
    print("\nWho are the 3 people who accepted? Can you share their names or profile URLs?")

ctx.close()
p.stop()
