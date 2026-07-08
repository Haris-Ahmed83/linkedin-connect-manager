import json, base64
from playwright.sync_api import sync_playwright

PROFILE_DIR = "E:\\Codes\\Linkdin-Github\\linkedin_profile"

with sync_playwright() as p:
    context = p.chromium.launch_persistent_context(
        PROFILE_DIR, headless=False,
        viewport={"width": 1280, "height": 800}
    )
    page = context.pages[0] if context.pages else context.new_page()
    page.goto("https://www.linkedin.com/feed/", timeout=30000)
    page.wait_for_timeout(3000)

    cookies = context.cookies(urls=["https://www.linkedin.com", "https://.linkedin.com", "https://.www.linkedin.com"])
    encoded = base64.b64encode(json.dumps(cookies).encode()).decode()
    print("\n=== Base64 Cookie String (add to GitHub secret LINKEDIN_COOKIES) ===\n")
    print(encoded)
    print(f"\nTotal cookies: {len(cookies)}")

    context.close()
