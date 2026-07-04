# LinkedIn Connect Manager — Setup

## Step 1: Add Scopes to LinkedIn App

Go to https://www.linkedin.com/developers/apps → **Haris-Poster** → **Auth** tab

Add these scopes:
- ✅ `w_messages` — Send welcome messages
- ✅ `r_network` — Read connections list
- ✅ `offline_access` — Get refresh token (1 year valid)

Click **Save**.

## Step 2: Generate OAuth URL

Build this URL:

```
https://www.linkedin.com/oauth/v2/authorization
  ?response_type=code
  &client_id=779zgdewb7kogo
  &redirect_uri=https://www.linkedin.com/developers/tools/oauth/redirect
  &scope=openid%20email%20profile%20w_memory%20w_messages%20r_network%20offline_access
  &state=setup123
```

Or use this one-click link:
[Click here to authorize](https://www.linkedin.com/oauth/v2/authorization?response_type=code&client_id=779zgdewb7kogo&redirect_uri=https://www.linkedin.com/developers/tools/oauth/redirect&scope=openid%20email%20profile%20w_memory%20w_messages%20r_network%20offline_access&state=setup123)

## Step 3: Exchange Code for Tokens

After authorizing, LinkedIn redirects to a URL like:
```
https://www.linkedin.com/developers/tools/oauth/redirect?code=AQX...&state=setup123
```

Go to https://www.linkedin.com/developers/tools/oauth/redirect and copy the `code` value from the URL.

Then run this command locally (replace CODE with yours):

```bash
curl -X POST https://www.linkedin.com/oauth/v2/accessToken \
  -d "grant_type=authorization_code" \
  -d "code=YOUR_CODE_HERE" \
  -d "client_id=779zgdewb7kogo" \
  -d "client_secret=YOUR_CLIENT_SECRET" \
  -d "redirect_uri=https://www.linkedin.com/developers/tools/oauth/redirect"
```

Or use PowerShell:
```powershell
$body = @{
    grant_type="authorization_code"
    code="YOUR_CODE_HERE"
    client_id="779zgdewb7kogo"
    client_secret="YOUR_CLIENT_SECRET"
    redirect_uri="https://www.linkedin.com/developers/tools/oauth/redirect"
}
Invoke-RestMethod -Uri "https://www.linkedin.com/oauth/v2/accessToken" -Method Post -Body $body
```

Response will include:
```json
{
  "access_token": "AQX...",
  "refresh_token": "AQX...",
  "expires_in": 5184000,
  "refresh_token_expires_in": 31536000
}
```

## Step 4: Set GitHub Secrets

Go to repo Settings → Secrets and variables → Actions → Add:

| Secret | Value |
|---|---|
| `LINKEDIN_ACCESS_TOKEN` | From response above |
| `LINKEDIN_REFRESH_TOKEN` | From response above (🆕) |
| `LINKEDIN_CLIENT_ID` | Already set |
| `LINKEDIN_CLIENT_SECRET` | Already set |
| `LINKEDIN_USER_URN` | Already set (`urn:li:person:R6x7Ha7PiU`) |
| `GH_PAT` | GitHub Personal Access Token with `repo` scope |

## Step 5: Test

Go to Actions tab → **Check New Connections** → Run workflow manually.

If successful, it will:
1. Fetch all your LinkedIn connections via API
2. Compare with `data/known_connections.json`
3. Send welcome message to any new connections
4. Update `known_connections.json`

## How It Works

- Runs every 3 hours via GitHub Actions cron
- Auto-refreshes LinkedIn token when expiry is near (5 days buffer)
- Saves refreshed token back to GitHub Secrets automatically
- Zero maintenance for 1 year (refresh token valid)
