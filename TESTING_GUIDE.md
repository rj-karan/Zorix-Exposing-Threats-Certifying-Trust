# Complete Testing Guide - Zorix with Juice-Shop

## ✅ Encoding Issues FULLY FIXED

All Unicode/charmap errors have been fixed:
1. ✅ UTF-8 environment variable set before Python starts
2. ✅ Safe encoding in all error handlers (pipeline + API)
3. ✅ UTF8ResponseMiddleware catches any remaining issues
4. ✅ Batch scripts provided for both .bat and .ps1

---

## 🚀 STEP 1: Start Backend (IMPORTANT - USE NEW SCRIPTS)

### Option A: Windows Batch File (Recommended for CMD users)
```batch
cd C:\zorix\Zorix-Exposing-Threats-Certifying-Trust
start_backend.bat
```

### Option B: PowerShell
```powershell
cd C:\zorix\Zorix-Exposing-Threats-Certifying-Trust
.\start_backend.ps1
```

### Option C: Manual (if above don't work)
```powershell
Set-ExecutionPolicy -ExecutionPolicy Bypass -Scope Process
$env:PYTHONIOENCODING="utf-8"
$env:PYTHONLEGACYWINDOWSSTDIO="0"
cd C:\zorix\Zorix-Exposing-Threats-Certifying-Trust
python -m uvicorn backend.main:app --reload
```

**You should see:**
```
INFO:     Uvicorn running on http://127.0.0.1:8000
INFO:     Database initialized successfully
```

---

## 🚀 STEP 2: Start Frontend (Terminal 2)

```bash
cd C:\zorix\Zorix-Exposing-Threats-Certifying-Trust\frontend
npm run dev
```

**Expected:**
```
Local:   http://localhost:3000/
```

---

## 🚀 STEP 3: Start Ollama (Terminal 3)

```bash
ollama serve
```

**Expected:**
```
Listening on 127.0.0.1:11434
```

If mistral model not installed:
```bash
ollama pull mistral
```

---

## 🧪 STEP 4: Complete Test Flow

### 1. Open Browser
```
http://localhost:3000
```

### 2. Register Account
- **Email:** test@example.com
- **Password:** password123
- Click "Register"
- See: "Registration successful! Please log in."

### 3. Login
- **Email:** test@example.com  
- **Password:** password123
- See: "Logged in successfully!"
- Bottom right shows your email

### 4. Navigate to Analysis Page
- Click "Analysis" tab at the top
- See form: "Analyze Repository"

### 5. Test with Juice-Shop (Real Vulnerable App)

**Enter Repository Details:**
- **Repository URL:** `https://github.com/juice-shop/juice-shop`
- **Vulnerability Type:** SQL_INJECTION
- **Affected File:** `app.js`
- **GitHub Token:** (leave empty - it's public)

**Click "Start Analysis"**

### 6. Wait for Results (2-5 minutes)

Backend will:
1. ✅ Fetch code from GitHub
2. ✅ Send to Ollama for AI analysis
3. ✅ Generate SQL injection exploits
4. ✅ Execute in Docker sandbox (tests if vulnerable)
5. ✅ Calculate CVSS score
6. ✅ Return detailed results

### 7. Check Results

You should see:
- **Severity Badge** → CRITICAL/HIGH/MEDIUM/LOW in color
- **CVSS Score** → Number like 8.5/10.0
- **Root Cause** → Why the vulnerability exists
- **Attack Vector** → How to exploit it
- **PoC** → Proof of concept example
- **Recommended Fix** → How to patch it

### 8. Check Dashboard

Click "Dashboard" tab:
- **Total Analyses** → Should show "1"
- **Completed** → Should show "1"
- **Critical Count** → Based on findings
- **Live Verifications** → Shows your analysis result

---

## 🐛 Troubleshooting

### Error: "charmap" codec can't encode characters
**Solution:** You didn't use the startup script!
- Kill the uvicorn process
- Use `start_backend.bat` or `start_backend.ps1`
- Never use plain `python -m uvicorn` on Windows

### Error: "Failed to fetch repository"
- GitHub API might be rate-limited
- Try smaller repo: `https://github.com/torvalds/linux`
- Or add GitHub token if available

### Error: "AI Service not ready"
- Make sure Terminal 3 has `ollama serve` running
- Check: http://localhost:11434/api/tags
- Verify Mistral model: `ollama list`

### Error: "Cannot connect to backend"
- Make sure Terminal 1 has backend running
- Check: http://localhost:8000/health
- Verify port 8000 is not in use: `netstat -ano | findstr :8000`

### Error: "Docker not found"
- Exploit execution will skip (Docker sandbox)
- Analysis will still work for AI + scoring
- Install Docker if you want sandbox execution

---

## 📊 Expected Final Output

```json
{
  "status": "completed",
  "analysis_id": "550e8400-e29b-41d4-a716-446655440000",
  "severity": "HIGH",
  "score": 8.5,
  "vulnerable": true,
  "exploits_tested": 5,
  "report_url": "/reports/550e8400-e29b-41d4-a716-446655440000/html"
}
```

Dashboard should show:
```
Total Analyses: 1
Completed: 1
Critical Count: 0
Avg Confidence: 95%

Live Verifications:
┌─ juice-shop (GitHub) | SQL_INJECTION | HIGH | 8.5 | 2 days ago ─┐
└────────────────────────────────────────────────────────────────┘
```

---

## ✅ Success Checklist

- [ ] Backend starts without "charmap" error
- [ ] Frontend loads at http://localhost:3000
- [ ] Can register and login
- [ ] Analysis tab works
- [ ] Can submit juice-shop repo
- [ ] See analysis results display
- [ ] Dashboard shows analysis count updated
- [ ] No encoding errors in terminal output

---

## 🎯 Key Fixes Applied

1. **Start Scripts** - UTF-8 encoding set before Python
2. **Safe Encoding** - All errors sanitized before returning
3. **Middleware** - Catches any remaining unicode issues
4. **Logging** - Uses UTF8SafeFormatter for console output
5. **API Routes** - All responses use safe_encode()

You're ready to test! 🚀
