import time, os, json, sys, re, base64
from http.cookies import SimpleCookie
from requests.cookies import RequestsCookieJar, create_cookie
from linkedin_api import Linkedin
from config import LINKEDIN_USERNAME, LINKEDIN_PASSWORD, MAX_ACCEPT_PER_RUN, MIN_DELAY_SEC, MAX_DELAY_SEC
from message_template import get_message

TRACKING_FILE = "E:\\Codes\\linkedin-connect-manager\\tracking.json"
COOKIES_DIR = "E:\\Codes\\linkedin-connect-manager\\.linkedin_cookies"

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
    print(safe, flush=True)

def cookies_from_browser_json(browser_cookies):
    jar = RequestsCookieJar()
    for c in browser_cookies:
        jar.set_cookie(create_cookie(
            name=c["name"],
            value=c["value"],
            domain=c.get("domain", ".linkedin.com"),
            path=c.get("path", "/"),
            secure=c.get("secure", True),
            rest={"HttpOnly": c.get("httpOnly", False)},
        ))
    return jar

def get_api():
    is_ci = os.environ.get("GITHUB_ACTIONS") == "true"
    cookie_b64 = os.environ.get("LINKEDIN_COOKIES", "")
    if cookie_b64:
        try:
            browser_cookies = json.loads(base64.b64decode(cookie_b64).decode())
            jar = cookies_from_browser_json(browser_cookies)
            api = Linkedin(LINKEDIN_USERNAME, LINKEDIN_PASSWORD,
                           authenticate=True, cookies=jar,
                           cookies_dir=COOKIES_DIR)
            me = api.get_user_profile()
            name = me.get('miniProfile', {}).get('firstName', '') or me.get('firstName', {}).get('localized', {}).get('en_US', '')
            sp(f"Logged in via cookies as {name}")
            sp(f"  Profile keys: {list(me.keys())}")
            return api
        except Exception as ex:
            sp(f"Cookie login failed: {ex}")
    api = Linkedin(LINKEDIN_USERNAME, LINKEDIN_PASSWORD,
                   cookies_dir=COOKIES_DIR)
    sp("Logged in via credentials")
    return api

def send_welcome(api, profile_urn, name, headline=""):
    sp(f"    Messaging {name}...")
    try:
        msg = get_message(name, headline)
        error = api.send_message(message_body=msg, recipients=[profile_urn])
        if error:
            sp(f"    Send error: {error}")
            return False
        sp(f"    Sent!")
        return True
    except Exception as ex:
        sp(f"    Message exception: {ex}")
        return False

def run(oneshot=False):
    if not LINKEDIN_USERNAME or not LINKEDIN_PASSWORD:
        print("LinkedIn credentials not configured.")
        return

    total_accepted = 0
    total_messaged = 0
    tracking = load_tracking()
    api = get_api()
    me = api.get_user_profile()
    my_urn = me.get("urn_id", "")

    messaged_clean = {clean_name(m) for m in tracking.get("messaged", [])}

    # === PART 1: Accept incoming requests ===
    sp("Checking pending incoming requests...")
    try:
        invitations = api.get_invitations(limit=50)
    except Exception as ex:
        sp(f"  Error fetching invitations: {ex}")
        invitations = []
    sp(f"Pending incoming requests: {len(invitations)}")

    for inv in invitations[:MAX_ACCEPT_PER_RUN]:
        inviter = inv.get("inviter", {})
        fn = inviter.get("firstName", {}).get("localized", {}).get("en_US", "")
        ln = inviter.get("lastName", {}).get("localized", {}).get("en_US", "")
        full_name = f"{fn} {ln}".strip()
        headline = inviter.get("headline", "")
        if clean_name(full_name) in messaged_clean:
            sp(f"    Skipping {full_name} (already messaged)")
            continue

        sp(f"    Accepting: {full_name} | {headline}")
        entity_urn = inv.get("entity_urn", "")
        shared_secret = inv.get("shared_secret", "")
        if entity_urn and shared_secret:
            try:
                api.reply_invitation(entity_urn, shared_secret, action="accept")
                sp(f"    Accepted!")
                total_accepted += 1
                random_delay()
                inviter_urn = inviter.get("urn_id", "")
                if inviter_urn:
                    success = send_welcome(api, inviter_urn, full_name, headline)
                    if success:
                        tracking.setdefault("messaged", []).append(full_name)
                        total_messaged += 1
                    else:
                        tracking.setdefault("failed_retry", {})[clean_name(full_name)] = time.time()
                random_delay()
            except Exception as ex:
                sp(f"    Error: {ex}")
        else:
            sp(f"    Missing entity_urn or shared_secret")

    # === PART 2: Check connections for new people ===
    sp("Checking connections for new people...")
    try:
        # Get my profile to find correct URN format
        me_profile = api.get_user_profile()
        my_id = me_profile.get("id", me_profile.get("urn_id", ""))
        sp(f"  Profile ID: {my_id}")
        conns = api.get_profile_connections(my_id, limit=100)
        sp(f"  Connection check: got {len(conns)} results")
    except Exception as ex:
        sp(f"  Error fetching connections: {ex}")
        conns = []

    prev = tracking.get("prev_connections", [])
    known = {clean_name(c.get("fullName", c.get("name", ""))) for c in prev}
    new_people = [c for c in conns if clean_name(c.get("fullName", c.get("name", ""))) not in known]
    new_people = [c for c in new_people if clean_name(c.get("fullName", c.get("name", ""))) not in messaged_clean]

    if not prev:
        sp(f"  First run — saved {len(conns)} connections as baseline")
        tracking["prev_connections"] = conns
    elif new_people:
        sp(f"  Found {len(new_people)} new connection(s)!")
        for c in new_people:
            name = c.get("fullName", c.get("name", ""))
            urn = c.get("urn_id", c.get("profile_urn", ""))
            sp(f"    Messaging: {name}")
            if urn:
                success = send_welcome(api, urn, name, "")
                if success:
                    tracking.setdefault("messaged", []).append(name)
                    total_messaged += 1
                else:
                    tracking.setdefault("failed_retry", {})[clean_name(name)] = time.time()
            random_delay()
        tracking["prev_connections"] = conns
    else:
        sp(f"  No new connections")

    # === PART 3: Check sent page alternative ===
    sp("Checking sent invitations for newly accepted...")
    try:
        invitations = api.get_invitations(limit=50)
    except:
        invitations = []
    # People who sent us invites and are no longer pending = accepted
    current_inviter_urns = set()
    for inv in invitations:
        inviter = inv.get("inviter", {})
        uid = (inviter.get("urn_id") or "").lower()
        if uid:
            current_inviter_urns.add(uid)

    prev_sent = tracking.get("prev_sent_invites", [])
    newly_accepted = [p for p in prev_sent
        if p.get("urn", "").lower() not in current_inviter_urns
        and clean_name(p.get("name", "")) not in messaged_clean]
    for p in newly_accepted:
        success = send_welcome(api, p.get("urn", ""), p.get("name", ""), p.get("headline", ""))
        if success:
            tracking.setdefault("messaged", []).append(p["name"])
            total_messaged += 1
        else:
            tracking.setdefault("failed_retry", {})[clean_name(p["name"])] = time.time()
        random_delay()

    tracking["prev_sent_invites"] = [
        {"name": inv.get("inviter",{}).get("firstName",{}).get("localized",{}).get("en_US","") + " " + inv.get("inviter",{}).get("lastName",{}).get("localized",{}).get("en_US",""),
         "urn": inv.get("inviter",{}).get("urn_id",""),
         "headline": inv.get("inviter",{}).get("headline","")}
        for inv in invitations if inv.get("inviter",{}).get("urn_id")
    ]

    save_tracking(tracking)
    sp(f"\nFinal: Accepted: {total_accepted}, Messaged: {total_messaged}")
