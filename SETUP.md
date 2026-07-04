# LinkedIn Connect Manager — Local Setup

GitHub Actions par LinkedIn login block hota hai (different IP).
Solution: **apne PC par Task Scheduler** se daily run.

## Setup

### 1. Install Python packages

Open PowerShell and run:

```powershell
pip install playwright
playwright install chromium
```

### 2. Update `run_daily.ps1`

Notepad mein kholo and apna phone number + password dalo:

```powershell
$env:LINKEDIN_USERNAME = "0300XXXXXXX"
$env:LINKEDIN_PASSWORD = "your_password"
```

### 3. Test manually

```powershell
cd E:\Codes\linkedin-connect-manager
.\run_daily.ps1
```

### 4. Schedule daily via Task Scheduler

1. Open **Task Scheduler** (Windows search)
2. Click **Create Basic Task**
3. Name: `LinkedIn Auto Connect`
4. Trigger: **Daily**, Time: 1:00 PM
5. Action: **Start a program**
   - Program: `powershell.exe`
   - Arguments: `-File "E:\Codes\linkedin-connect-manager\run_daily.ps1" -WindowStyle Hidden`
6. **Finish**

### How it works

- Har din 1 PM par auto-run
- LinkedIn login → accept pending requests (max 15) → welcome message
- Same IP, same location → LinkedIn kuch nahi kahe ga
- No maintenance needed
