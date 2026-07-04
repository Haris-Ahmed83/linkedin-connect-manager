import requests, base64, json
from datetime import datetime, timezone
from config import (
    LINKEDIN_CLIENT_ID, LINKEDIN_CLIENT_SECRET,
    LINKEDIN_ACCESS_TOKEN, LINKEDIN_REFRESH_TOKEN,
    GH_PAT, REPO_OWNER, REPO_NAME, SECRET_NAME,
    TOKEN_REFRESH_BUFFER_DAYS
)

def decode_token(token):
    parts = token.split(".")
    if len(parts) != 3:
        return None
    try:
        padding = 4 - len(parts[1]) % 4
        if padding != 4:
            parts[1] += "=" * padding
        payload = json.loads(base64.urlsafe_b64decode(parts[1]))
        return payload
    except:
        return None

def token_expiring_soon(token):
    payload = decode_token(token)
    if not payload or "exp" not in payload:
        return True
    exp = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
    remaining = (exp - datetime.now(timezone.utc)).days
    return remaining <= TOKEN_REFRESH_BUFFER_DAYS

def refresh_access_token():
    if not LINKEDIN_REFRESH_TOKEN:
        print("No refresh token available. Cannot auto-refresh.")
        return LINKEDIN_ACCESS_TOKEN

    url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "refresh_token",
        "refresh_token": LINKEDIN_REFRESH_TOKEN,
        "client_id": LINKEDIN_CLIENT_ID,
        "client_secret": LINKEDIN_CLIENT_SECRET,
    }
    resp = requests.post(url, data=data)
    if resp.status_code != 200:
        print(f"Token refresh failed: {resp.status_code} {resp.text}")
        return LINKEDIN_ACCESS_TOKEN

    result = resp.json()
    new_token = result.get("access_token")
    if not new_token:
        print("No access_token in refresh response.")
        return LINKEDIN_ACCESS_TOKEN

    print("Token refreshed successfully!")

    if GH_PAT:
        update_github_secret(new_token)
    else:
        print("GH_PAT not set. Token updated in memory but not in GitHub Secrets.")

    return new_token

def update_github_secret(new_token):
    url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/secrets/{SECRET_NAME}"
    headers = {
        "Authorization": f"Bearer {GH_PAT}",
        "Accept": "application/vnd.github.v3+json",
    }

    pub_resp = requests.get(
        f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}/actions/secrets/public-key",
        headers=headers
    )
    if pub_resp.status_code != 200:
        print(f"Failed to get public key: {pub_resp.text}")
        return

    key_data = pub_resp.json()
    key_id = key_data["key_id"]
    public_key = key_data["key"]

    try:
        from nacl import encoding, public
        public_key_bytes = encoding.Base64Encoder.decode(public_key)
        sealed_box = public.SealedBox(public.PublicKey(public_key_bytes))
        encrypted = sealed_box.encrypt(new_token.encode("utf-8"))
        encrypted_value = base64.b64encode(encrypted).decode("utf-8")
    except Exception as e:
        print(f"Encryption failed: {e}")
        return

    put_resp = requests.put(url, headers=headers, json={
        "encrypted_value": encrypted_value,
        "key_id": key_id,
    })
    if put_resp.status_code in (201, 204):
        print("GitHub Secret updated successfully!")
    else:
        print(f"Failed to update GitHub Secret: {put_resp.text}")

def get_valid_token():
    token = LINKEDIN_ACCESS_TOKEN
    if not token:
        print("No access token configured.")
        return None
    if token_expiring_soon(token):
        print("Token expiring soon. Refreshing...")
        token = refresh_access_token()
    return token
