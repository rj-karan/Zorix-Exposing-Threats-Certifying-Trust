# 🚀 Zorix Quick Start Guide

## ✅ System Status

All components are now properly connected:
- ✅ **Frontend**: React + Vite with full UI (home, login, register, analyze)
- ✅ **Backend**: FastAPI with auth & analysis endpoints
- ✅ **API Client**: `api.js` with all necessary methods
- ✅ **Database**: SQLAlchemy with async support
- ✅ **AI Service**: OllamaService configured
- ✅ **Styling**: Complete dark theme with animations

---

## 🎬 How It Works (Step-by-Step)

### What Happens When You Register:
```
You enter email + password in browser
           ↓
Frontend sends POST /auth/register
           ↓
Backend (UserService) hashes password with bcrypt
           ↓
Stores user in SQLite database
           ↓
Returns success message
           ↓
You're redirected to login
```

### What Happens When You Log In:
```
You enter email + password in browser
           ↓
Frontend sends POST /auth/login
           ↓
Backend verifies password
           ↓
Creates JWT token (30-min expiry)
           ↓
Frontend saves token, shows "Logged in!" message
           ↓
You can now analyze repositories
```

### What Happens When You Analyze a Repo:
```
You paste: https://github.com/user/repo
You click "Analyze"
           ↓
═══ STEP 1: FETCH FILES ═══
Backend calls GitHub API
Downloads all code files from repo
Filters: Only .py, .js, .ts, .java, etc.
Filters: Max 5KB per file, max 5 files total
Result: { "path/file.py": "code content...", ... }
           ↓
═══ STEP 2: BUILD PROMPT ═══
Creates prompt: "Analyze this code for vulnerabilities"
Includes all file contents
Sends to Ollama (local AI)
           ↓
═══ STEP 3: AI ANALYSIS ═══
Ollama processes the code
Runs inference on mistral model
Takes 30-120 seconds depending on code size
Returns: JSON with analysis results
           ↓
═══ STEP 4: FORMAT RESULTS ═══
Extracts:
  - Summary: "Found SQL injection in database queries"
  - Severity: "HIGH"
  - CVSS Score: 8.5
  - Root cause: "User input directly used in SQL"
  - Attack vector: "POST /search?q=<injection>"
  - Proof of concept: "' OR '1'='1'"
  - Recommended fix: "Use parameterized queries"
           ↓
═══ STEP 5: DISPLAY ═══
Frontend shows beautiful color-coded results:
  🔴 CRITICAL / 🟠 HIGH / 🟡 MEDIUM / 🟢 LOW
  CVSS Score as big yellow number
  Expandable details about each finding
           ↓
You can see EXACTLY what to fix!
```

---

## 💻 Start All Services

### Terminal 1: Start Backend
```bash
cd C:\zorix\Zorix-Exposing-Threats-Certifying-Trust
python -m uvicorn backend.main:app --reload

# You should see:
# ✅ INFO:     Uvicorn running on http://127.0.0.1:8000
# ✅ Database initialized successfully
```

### Terminal 2: Start Ollama (Required for AI)
```bash
# Make sure Ollama is installed first!
ollama serve

# You should see:
# ✅ Listening on 127.0.0.1:11434

# In ANOTHER terminal, pull the model:
ollama pull mistral
```

### Terminal 3: Start Frontend
```bash
cd C:\zorix\Zorix-Exposing-Threats-Certifying-Trust\frontend
npm install
npm run dev

# You should see:
# ✅ Local:   http://localhost:3000
```

---

## 🧪 Test the Complete Flow

### 1. Open in Browser
```
http://localhost:3000
```

### 2. You'll see:
- 🛡️ Zorix title
- Subtitle: "Exposing Threats, Certifying Trust"
- Status: "✅ AI service ready" (if Ollama is running)
- Two buttons: "Register" and "Login"

### 3. Click "Register"
- Enter email: `test@example.com`
- Enter password: `password123`
- Click "Register"
- You'll see: "✅ Registration successful! Please log in."

### 4. Click "Login"
- Enter same email & password
- Click "Login"
- You'll see: "✅ Logged in successfully!"
- Page shows: "Analyze Repository" form

### 5. Test Analysis
- Paste GitHub URL: `https://github.com/nodejs/node`
- GitHub token: (leave empty unless private repo)
- Click "Analyze Repository"
- Wait 30-120 seconds...
- You'll see beautiful results with:
  - ✅ Summary of vulnerabilities
  - ✅ Severity level (with color)
  - ✅ CVSS Score
  - ✅ Root cause explanation
  - ✅ Attack vector details
  - ✅ Proof of concept
  - ✅ Recommended fixes

---

## 🔗 Connection Points

### Frontend → Backend
- `http://localhost:3000` (Vite)
- Proxied to → `http://localhost:8000/api` (FastAPI)

### Backend → Database
- SQLite: `./zorix.db` (auto-created)
- Or PostgreSQL if configured

### Backend → GitHub
- `https://api.github.com/` (public)
- Uses GitHub token if provided (private repos)

### Backend → AI (Ollama)
- `http://localhost:11434` (must be running!)
- Model: `mistral` (configurable)
- Returns: JSON with vulnerability analysis

---

## ❌ Troubleshooting

### "❌ Backend not reachable"
- Make sure Terminal 1 is running: `python -m uvicorn backend.main:app --reload`
- Check port 8000: `http://localhost:8000`

### "⚠️ AI Service not ready"
- Make sure Terminal 2 is running: `ollama serve`
- Did you run: `ollama pull mistral`?
- Check: `http://localhost:11434/api/tags`

### "Analysis failed: No module named X"
- Run: `pip install -r backend/requirements.txt`

### "CORS error"
- Check `ALLOWED_ORIGINS` in `.env`
- Should be: `["http://localhost:3000","http://localhost:5173"]`

### "Database error"
- Delete `zorix.db` and restart backend
- It will auto-create a new one

---

## 📚 File Structure (What We Have)

```
Zorix-Exposing-Threats-Certifying-Trust/
├── frontend/                      # React + Vite
│   ├── src/
│   │   ├── App.jsx               # ✅ MAIN UI (4 views)
│   │   ├── api.js                # ✅ API CLIENT
│   │   ├── App.css               # ✅ STYLING
│   │   └── main.jsx              # Entry point
│   ├── package.json
│   ├── vite.config.js            # ✅ API PROXY
│   └── index.html
│
├── backend/                       # FastAPI
│   ├── main.py                   # ✅ APP SETUP (CORS, routers)
│   ├── config.py                 # ✅ SETTINGS
│   ├── models.py                 # ✅ DATABASE MODELS
│   ├── database.py               # ✅ SQLALCHEMY SETUP
│   ├── requirements.txt           # ✅ DEPENDENCIES
│   ├── api/
│   │   └── routes/
│   │       ├── auth.py           # ✅ REGISTER/LOGIN
│   │       └── analysis.py       # ✅ ANALYZE ENDPOINT
│   ├── services/
│   │   ├── user_service.py       # ✅ User management
│   │   ├── ai_analysis_service.py # ✅ OLLAMA INTEGRATION
│   │   └── github_service.py     # ✅ GITHUB API
│   └── core/
│       ├── security.py           # ✅ Password/JWT
│       └── prompts.py            # ✅ AI PROMPTS
│
├── .env                          # ✅ CONFIGURATION
├── COMPLETE_WORKFLOW.md          # 📖 THIS FILE
└── ... (other files)
```

---

## 🎯 Key Features Enabled

✅ **User Authentication**
- Register accounts
- Secure password hashing (bcrypt)
- JWT tokens (30-min expiry)

✅ **GitHub Integration**
- Fetch any public repository
- Support for private repos (with token)
- Automatic code file filtering

✅ **AI Vulnerability Analysis**
- Powered by Ollama + mistral model
- Understands code context
- Returns severity, CVSS, fixes

✅ **Beautiful UI**
- Dark theme with gradients
- Real-time status updates
- Color-coded severity levels
- Responsive design (works on mobile)

✅ **Complete Backend**
- Async database operations
- Proper error handling
- CORS security
- Input validation

---

## 🎉 You're All Set!

The entire Zorix system is now:
- ✅ Properly connected (frontend ↔ backend)
- ✅ Ready to test (all components working)
- ✅ Well-documented (see COMPLETE_WORKFLOW.md)
- ✅ Production-ready (with proper security)

Start the 3 terminals and visit `http://localhost:3000` to begin! 🚀
