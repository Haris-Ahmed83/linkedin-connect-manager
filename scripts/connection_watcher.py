import requests, json, os
from config import CONNECTIONS_FILE

def fetch_connections(access_token):
    url = "https://api.linkedin.com/rest/connections"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Restli-Protocol-Version": "2.0.0",
        "LinkedIn-Version": "202405",
    }
    params = {"q": "viewer", "start": 0, "count": 1000}

    all_connections = []
    while True:
        resp = requests.get(url, headers=headers, params=params)
        if resp.status_code != 200:
            print(f"Failed to fetch connections: {resp.status_code} {resp.text[:200]}")
            return None
        data = resp.json()
        elements = data.get("elements", [])
        for el in elements:
            urn = el.get("urn")
            name = el.get("firstName", "") + " " + el.get("lastName", "")
            all_connections.append({"urn": urn, "name": name.strip()})
        start = data.get("paging", {}).get("start", params["start"])
        count = data.get("paging", {}).get("count", len(elements))
        total = data.get("paging", {}).get("total", len(elements))
        params["start"] = start + count
        if params["start"] >= total:
            break

    return all_connections

def load_known():
    if os.path.exists(CONNECTIONS_FILE):
        with open(CONNECTIONS_FILE) as f:
            return json.load(f)
    return []

def save_known(connections):
    os.makedirs(os.path.dirname(CONNECTIONS_FILE), exist_ok=True)
    with open(CONNECTIONS_FILE, "w") as f:
        json.dump(connections, f, indent=2)

def detect_new_connections(access_token):
    current = fetch_connections(access_token)
    if current is None:
        return None, []

    known = load_known()
    known_urns = {c["urn"] for c in known}
    new_connections = [c for c in current if c["urn"] not in known_urns]

    return current, new_connections

def update_known(connections):
    save_known(connections)
