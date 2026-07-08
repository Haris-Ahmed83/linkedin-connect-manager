import os, json, base64
from requests.cookies import RequestsCookieJar, create_cookie
from linkedin_api import Linkedin
from playwright.sync_api import sync_playwright

PROFILE_DIR = "E:\\Codes\\Linkdin-Github\\linkedin_profile"

# Get cookies from browser profile
with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        PROFILE_DIR, headless=False,
        viewport={"width": 1280, "height": 800}
    )
    page = context.pages[0] if context.pages else context.new_page()
    page.goto("https://www.linkedin.com/feed/", timeout=30000)
    page.wait_for_timeout(3000)
    browser_cookies = context.cookies(urls=["https://www.linkedin.com", "https://.linkedin.com", "https://.www.linkedin.com"])
    context.close()

# Convert to RequestsCookieJar
jar = RequestsCookieJar()
for c in browser_cookies:
    jar.set_cookie(create_cookie(name=c['name'], value=c['value'],
        domain=c.get('domain', '.linkedin.com'), path=c.get('path', '/'),
        secure=c.get('secure', True)))

# Try linkedin-api with these cookies
api = Linkedin(os.environ.get('LINKEDIN_USERNAME', ''), os.environ.get('LINKEDIN_PASSWORD', ''),
               authenticate=True, cookies=jar,
               cookies_dir='E:\\Codes\\linkedin-connect-manager\\.linkedin_cookies')
me = api.get_user_profile()
first = me.get('firstName', {}).get('localized', {}).get('en_US', '')
last = me.get('lastName', {}).get('localized', {}).get('en_US', '')
urn = me.get('urn_id', '')
print(f'SUCCESS: {first} {last} (urn: {urn})')

invites = api.get_invitations(limit=3)
print(f'Invitations: {len(invites)}')
for inv in invites:
    inviter = inv.get('inviter', {})
    fn = inviter.get('firstName', {}).get('localized', {}).get('en_US', '')
    ln = inviter.get('lastName', {}).get('localized', {}).get('en_US', '')
    print(f'  - {fn} {ln} | {inv.get("entity_urn", "")}')
