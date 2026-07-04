import requests, json, time
from config import RATE_LIMIT_SLEEP
from message_template import get_welcome_message

def send_welcome_message(access_token, recipient_urn, name=""):
    url = "https://api.linkedin.com/rest/messages"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": "202405",
        "Content-Type": "application/json",
    }
    body = get_welcome_message(name)

    payload = {
        "recipients": [
            {"recipient_id": recipient_urn}
        ],
        "body": body,
        "subject": "Thanks for connecting!",
        "messageType": "INMAIL",
    }

    resp = requests.post(url, headers=headers, json=payload)
    if resp.status_code in (201, 200):
        print(f"Message sent to {recipient_urn}")
        return True
    elif resp.status_code == 429:
        print(f"Rate limited. Sleeping {RATE_LIMIT_SLEEP * 3}s...")
        time.sleep(RATE_LIMIT_SLEEP * 3)
        resp = requests.post(url, headers=headers, json=payload)
        return resp.status_code in (201, 200)
    else:
        print(f"Failed to send message to {recipient_urn}: {resp.status_code} {resp.text[:200]}")
        return False

def send_messages_to_new(access_token, new_connections):
    success_count = 0
    for conn in new_connections:
        urn = conn.get("urn")
        name = conn.get("name", "")
        if not urn:
            continue
        ok = send_welcome_message(access_token, urn, name)
        if ok:
            success_count += 1
        time.sleep(RATE_LIMIT_SLEEP)
    return success_count
