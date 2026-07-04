# LinkedIn Connect Manager

Browser automation that:
1. Logs into LinkedIn
2. Accepts pending connection requests (max 15/run)
3. Sends welcome message to each new connection

## Setup

### 1. Add GitHub Secrets

Go to repo → Settings → Secrets and variables → Actions:

| Secret | Value |
|---|---|
| `LINKEDIN_USERNAME` | Your LinkedIn email or phone number |
| `LINKEDIN_PASSWORD` | Your LinkedIn password |

### 2. Test

Go to Actions → **Auto Accept + Welcome Message** → Run workflow (manual first).

### Schedule

Runs daily at 8:00 AM UTC (1:00 PM PKT).

### Notes

- Max 15 accepts per run (LinkedIn safety limit)
- Random delays between actions (3-7 sec)
- If 2FA/challenge page appears, run skips automatically
- Password is encrypted in GitHub Secrets — never logged or committed
