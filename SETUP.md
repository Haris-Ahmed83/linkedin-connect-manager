# LinkedIn Connect Manager — Setup

## Step 1: Add Scopes to LinkedIn App

1. Go to https://www.linkedin.com/developers/apps
2. Click **Haris-Poster** app
3. Go to **Auth** tab
4. Under **Scopes**, add these:
   - ✅ `w_messages`
   - ✅ `r_network`
   - ✅ `offline_access`
5. Click **Save**

## Step 2: Generate OAuth Link

Open this URL in your browser (replace CLIENT_ID with `779zgdewb7kogo`):

```
https://www.linkedin.com/oauth/v2/authorization?
response_type=code&
client_id=779zgdewb7kogo&
redirect_uri=https://haris.primevoai.com/callback&
scope=openid%20email%20profile%20w_memory%20w_messages%20r_network%20offline_access&
state=setup123
```

Or click this link (if your browser allows long URLs):
[https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=779zgdewb7kogo&redirect_uri=https://haris.primevoai.com/callback&scope=openid%20email%20profile%20w_memory%20w_messages%20r_network%20offline_access&state=setup123](https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=779zgdewb7kogo&redirect_uri=https://haris.primevoai.com/callback&scope=openid%20email%20profile%20w_memory%20w_messages%20r_network%20offline_access&state=setup123)

## Step 3: Exchange Code for Tokens

After authorizing, you'll be redirected to:
`https://haris.primevoai.com/callback?code=AUTHORIZATION_CODE&state=setup123`

Copy the `code` value from the URL.

Then open PowerShell and run:

```powershell
$body = @{
    grant_type="authorization_code"
    code="YOUR_CODE_HERE"
    client_id="779zgdewb7kogo"
    client_secret="YOUR_CLIENT_SECRET"
    redirect_uri="https://haris.primevoai.com/callback"
}
Invoke-RestMethod -Uri "https://www.linkedin.com/oauth/v2/accessToken" -Method Post -Body $body
```

Response:
```json
{
  "access_token": "AQX...",
  "refresh_token": "AQX...",
  "expires_in": 5184000,
  "refresh_token_expires_in": 31536000
}
```

> **Tip:** `expires_in` = 60 days (access), `refresh_token_expires_in` = 365 days (refresh)

## Step 4: Set GitHub Secrets

Go to https://github.com/Haris-Ahmed83/linkedin-connect-manager/settings/secrets/actions

| Secret | Value |
|---|---|
| `LINKEDIN_ACCESS_TOKEN` | `access_token` from response above (update existing) |
| `LINKEDIN_REFRESH_TOKEN` | `refresh_token` from response above (new) |
| `LINKEDIN_CLIENT_ID` | Already set (`779zgdewb7kogo`) |
| `LINKEDIN_CLIENT_SECRET` | Already set |
| `LINKEDIN_USER_URN` | Already set (`urn:li:person:R6x7Ha7PiU`) |
| `GH_PAT` | GitHub PAT with `repo` scope (create at https://github.com/settings/tokens) |

## Step 5: Test

Go to Actions tab → **Check New Connections** → **Run workflow** (manual)

If successful:
1. Fetches all LinkedIn connections via API
2. Compares with `data/known_connections.json`
3. Sends welcome message to any new connections
4. Updates `known_connections.json`

## How It Works

- Runs every 3 hours via GitHub Actions cron
- Auto-refreshes LinkedIn token when expiry is near (5 days buffer)
- Saves refreshed token back to GitHub Secrets automatically
- Zero maintenance for 1 year (refresh token valid)
