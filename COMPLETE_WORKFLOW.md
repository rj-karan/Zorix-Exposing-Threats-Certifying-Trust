# 🛡️ Zorix System Architecture & Workflow

## 📋 System Overview

**Zorix** is an AI-powered GitHub repository vulnerability analysis platform. It analyzes GitHub repositories for security vulnerabilities using OpenAI-compatible LLMs (Ollama) and provides detailed reports.

---

## 🏗️ Architecture

### Frontend (React + Vite)
- **Location**: `frontend/`
- **Tech Stack**: React 18, Vite 5, Vanilla CSS
- **Port**: 3000
- **Key Files**:
  - `src/App.jsx` - Main UI with 4 views (home, login, register, analyze)
  - `src/api.js` - API client for backend communication
  - `src/App.css` - Complete styling with dark theme
  - `vite.config.js` - Vite config with API proxy to backend

### Backend (FastAPI + SQLAlchemy)
- **Location**: `backend/`
- **Tech Stack**: FastAPI, SQLAlchemy async, Pydantic
- **Port**: 8000
- **Key Modules**:
  - `main.py` - FastAPI app with CORS, routers, lifespan
  - `config.py` - Pydantic settings with environment variables
  - `database.py` - SQLAlchemy async engine and session factory
  - `models.py` - Database models (User, Project, BugReport, etc.)
  - `schemas.py` - Pydantic request/response models
  - `api/routes/auth.py` - Authentication endpoints (register, login)
  - `api/routes/analysis.py` - Analysis endpoints (analyze, health check)
  - `services/` - Business logic layer
    - `user_service.py` - User management
    - `analysis_service.py` - Full analysis pipeline
    - `ai_analysis_service.py` - OllamaService for AI analysis
    - `github_service.py` - GitHub API interactions
  - `core/` - Core utilities
    - `security.py` - Password hashing, JWT tokens
    - `scoring.py` - Vulnerability scoring
    - `prompts.py` - AI prompts

### AI Service (Ollama)
- **Purpose**: Local LLM for vulnerability analysis
- **Default Model**: `mistral` (configurable)
- **Base URL**: `http://localhost:11434`
- **Communication**: HTTP REST API

### Database (SQLite / PostgreSQL)
- **Default**: SQLite (`app.db`)
- **Alternative**: PostgreSQL (configurable)
- **ORM**: SQLAlchemy 2.0 with async support

---

## 🔄 Complete Data Flow

### 1️⃣ User Registration
```
Frontend (Register Form)
  ↓ POST /auth/register
Backend (auth.py → UserService)
  ↓ Hash password with bcrypt
Database (User model)
  ↓ Response
Frontend (Navigate to login)
```

### 2️⃣ User Login
```
Frontend (Login Form)
  ↓ POST /auth/login
Backend (auth.py → UserService)
  ↓ Verify password → Create JWT token
Database (User lookup)
  ↓ Return {access_token, token_type}
Frontend (Save token, navigate to analyze)
```

### 3️⃣ Repository Analysis Pipeline
```
Frontend (Analyze Form)
  ↓ POST /analysis/analyze
  ├─ repo_url: "https://github.com/user/repo"
  └─ github_token: (optional, for private repos)

Backend (analysis.py)
  │
  ├─→ Step 1: Fetch Repository Files
  │   └─ github_service.py → fetch_repo_files()
  │      └─ GitHub API (tree + file contents)
  │      └─ Filter: Only code files, size < 5KB
  │      └─ Result: { filepath: content, ... }
  │
  ├─→ Step 2: Build AI Prompt
  │   └─ prompts.py → build_rca_prompt()
  │      └─ SYSTEM_PROMPT + file_contents
  │      └─ "Analyze this code for vulnerabilities..."
  │
  ├─→ Step 3: Send to AI (Ollama/LLM)
  │   └─ ai_analysis_service.py → OllamaService.analyze_repo()
  │      └─ HTTP POST http://localhost:11434/api/chat
  │      └─ JSON: {model, messages, stream: false, format: json}
  │      └─ Receives: { summary, severity, cwe_id, ... }
  │
  ├─→ Step 4: Parse & Validate Response
  │   └─ _parse_response() → AnalysisResult dataclass
  │      └─ Extract: summary, severity, vulnerability_type
  │      └─ Extract: attack_vector, proof_of_concept
  │      └─ Extract: recommended_fix, cwe_id, cvss_score
  │
  └─→ Step 5: Return Results
      └─ AnalyzeResponse model
      └─ JSON → Frontend

Frontend (Display Results)
  ├─ Summary card
  ├─ Severity badge (CRITICAL/HIGH/MEDIUM/LOW)
  ├─ CVSS Score (0.0-10.0)
  ├─ Root cause explanation
  ├─ Attack vector details
  ├─ Proof of concept code
  ├─ Recommended fixes
  └─ Affected files list
```

---

## 🎯 Key Endpoints

### Authentication
- `POST /auth/register` - Create new account
  ```json
  {
    "email": "user@example.com",
    "password": "secure_password"
  }
  ```
  
- `POST /auth/login` - Get JWT token
  ```json
  {
    "email": "user@example.com",
    "password": "secure_password"
  }
  ```
  Returns:
  ```json
  {
    "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "token_type": "bearer"
  }
  ```

### Analysis
- `POST /analysis/analyze` - Analyze GitHub repo
  ```json
  {
    "repo_url": "https://github.com/user/repo",
    "github_token": "ghp_..." (optional)
  }
  ```
  Returns:
  ```json
  {
    "summary": "SQL injection vulnerability in database query handling...",
    "severity": "HIGH",
    "vulnerability_type": "SQL Injection",
    "affected_files": ["backend/db.py", "backend/models.py"],
    "root_cause": "User input directly concatenated into SQL queries...",
    "attack_vector": "POST /api/search?q=<sql_injection>",
    "proof_of_concept": "' OR '1'='1'...",
    "recommended_fix": "Use parameterized queries...",
    "cwe_id": "CWE-89",
    "cvss_score": 8.5
  }
  ```

- `GET /analysis/ai-health` - Check AI service status
  ```json
  {
    "ollama_reachable": true,
    "current_model": "mistral",
    "available_models": ["mistral", "neural-chat"]
  }
  ```

- `GET /health` - Backend health check
  ```json
  {
    "status": "healthy",
    "database": "connected"
  }
  ```

---

## 🖥️ Frontend Views

### 1. Home View
- Displays app title and description
- Shows AI service status
- Buttons: Login / Register

### 2. Register View
- Email input
- Password input
- Register button
- Link to login

### 3. Login View
- Email input
- Password input
- Login button
- Link to register

### 4. Analyze View (Protected)
- User email display
- Logout button
- GitHub repo URL input
- GitHub token input (optional)
- Analyze button
- Results display (when analysis completes)

---

## ⚙️ Environment Configuration

### Backend (.env)
```
DATABASE_URL=sqlite+aiosqlite:///./zorix.db
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:5173"]
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
OLLAMA_TIMEOUT=180
GITHUB_TOKEN=ghp_xxxxxxxxxxxxx (optional)
```

### Frontend (Vite)
```javascript
// vite.config.js
proxy: {
  '/api': {
    target: 'http://localhost:8000',
    changeOrigin: true,
    rewrite: (path) => path.replace(/^\/api/, '')
  }
}
```

---

## 🚀 Running the System

### 1. Start Backend
```bash
cd Zorix-Exposing-Threats-Certifying-Trust
python -m uvicorn backend.main:app --reload
# Server at: http://localhost:8000
# Docs at: http://localhost:8000/docs
```

### 2. Start Ollama (AI Model)
```bash
# Install Ollama: https://ollama.ai
# Then run:
ollama serve
# In another terminal:
ollama pull mistral
# Check: http://localhost:11434/api/tags
```

### 3. Start Frontend
```bash
cd frontend
npm install
npm run dev
# Server at: http://localhost:3000
```

### 4. Test the Flow
```
1. Open http://localhost:3000
2. Click "Register" → Create account
3. Click "Login" → Sign in
4. Paste GitHub URL (e.g., https://github.com/nodejs/node)
5. Click "Analyze" → Wait for AI results
6. View detailed vulnerability report
```

---

## 🔐 Security Features

1. **Password Hashing**: Bcrypt with salt
2. **JWT Authentication**: 30-minute expiry
3. **CORS Protection**: Whitelist allowed origins
4. **Input Validation**: Pydantic models
5. **SQL Injection Prevention**: Parameterized queries
6. **Private Repos**: Support for GitHub tokens

---

## 📊 Database Models

- **User**: Email, hashed password, created_at
- **Project**: Repository URL, owner, created_by_user
- **BugReport**: Title, description, severity, created_at
- **CodeSnapshot**: File content, context, line numbers
- **AnalysisResult**: Root cause, exploit pattern, patch suggestion, score

---

## ⚠️ Error Handling

- **500 Error**: Backend/AI service failure
- **400 Error**: Invalid request format
- **401 Error**: Authentication failure
- **404 Error**: Repository not found
- **Timeout**: Ollama not responding (check: http://localhost:11434)

Frontend catches all errors and displays user-friendly messages.

---

## 🧪 Testing Endpoints

### Test Health
```bash
curl http://localhost:8000/health
```

### Test AI Service
```bash
curl http://localhost:8000/analysis/ai-health
```

### Test Register
```bash
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"password123"}'
```

### Test Analysis
```bash
curl -X POST http://localhost:8000/analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{"repo_url":"https://github.com/user/repo"}'
```

---

## 📝 Summary

**Zorix** creates a complete vulnerability analysis pipeline:
1. User registers/logs in securely
2. Provides GitHub repository URL
3. Backend fetches repo files from GitHub
4. AI (Ollama) analyzes code for vulnerabilities
5. Results returned with severity, CVSS, fixes
6. Frontend displays beautiful, colored results

All components are now properly connected and ready! 🎉
