# LinkedIn Connect Manager

Browser automation that:
1. Logs into LinkedIn
2. Accepts pending connection requests (max 15/run)
3. Sends welcome message to each new connection

## Setup

### 1. Install Playwright

```powershell
pip install playwright
playwright install chromium
```

### 2. Configure Credentials

Edit `run_daily.ps1` — apna phone number aur password dalo.

### 3. Test Manually

Right-click `run_daily.ps1` → **Run with PowerShell**

### 4. Auto-Schedule (already done)

Task Scheduler set hai — har din **1:00 PM PKT** par auto-run.

## How it works

- LinkedIn login with your credentials
- Go to My Network page
- Accept pending requests (max 15 per run)
- Send welcome message to each
- Same IP, same location → LinkedIn won't block

## Manual Trigger

```powershell
schtasks /Run /TN "LinkedIn Auto Connect"
```
