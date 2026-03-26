# 🛡️ Zorix - Complete End-to-End Vulnerability Analysis Pipeline

## System Overview

Zorix is a full-stack automated vulnerability validation system that combines AI analysis, exploit testing, and risk scoring to validate security vulnerabilities in GitHub repositories.

### Core Features

✅ **Automated Repository Analysis** - Fetch and analyze GitHub source code  
✅ **AI Root Cause Analysis** - Use local LLM (Ollama) for vulnerability explanation  
✅ **Exploit Generation & Testing** - Create and execute test payloads automatically  
✅ **Docker Sandbox Execution** - Run exploits in isolated containers  
✅ **CVSS Scoring** - Calculate vulnerability severity scores  
✅ **Report Generation** - Create professional HTML, PDF, and JSON reports  
✅ **REST API** - Full API for integration and automation  
✅ **React Dashboard** - Modern web UI for vulnerability management  

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                  React FRONTEND (Port 3001)                 │
│  • Login/Register                                           │
│  • Analysis Form (repo URL, vulnerability type)            │
│  • Results Dashboard (score, severity, exploits)           │
│  • Report Viewer                                            │
└────────────────────────┬────────────────────────────────────┘
                         │ HTTP/REST + WebSocket
┌────────────────────────▼────────────────────────────────────┐
│              FASTAPI BACKEND (Port 8000)                    │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ └─ POST /api/analysis/analyze                        │   │
│  │    └─ Run complete vulnerability pipeline            │   │
│  │ └─ GET /api/analysis/results/{id}                   │   │
│  │    └─ Retrieve analysis results                      │   │
│  │ └─ GET /api/analysis/reports/{id}/{format}          │   │
│  │    └─ Download HTML/PDF/JSON report                 │   │
│  │ └─ GET /api/analysis/exploit-results/{id}           │   │
│  │    └─ Detailed exploit execution logs                │   │
│  └──────────────────────────────────────────────────────┘   │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ PIPELINE ORCHESTRATOR                               │   │
│  │  1. fetch_repository() → GitHub                     │   │
│  │  2. run_root_cause_analysis() → Ollama AI           │   │
│  │  3. generate_exploits() → ExploitGenerator          │   │
│  │  4. execute_exploits() → Docker Sandbox             │   │
│  │  5. run_static_analysis() → Code scanners           │   │
│  │  6. aggregate_results() → Combine findings           │   │
│  │  7. calculate_score() → CVSS scoring                │   │
│  │  8. generate_report() → Report generator             │   │
│  │  9. store_results() → PostgreSQL                     │   │
│  └──────────────────────────────────────────────────────┘   │
└────────────────────────┬────────────────────────────────────┘
         ┌───────────────┼───────────────┐
         │               │               │
    ┌────▼─────┐  ┌─────▼────┐  ┌──────▼──────┐
    │PostgreSQL│  │  Ollama   │  │Docker Engine │
    │Database  │  │Local LLM  │  │  Sandbox     │
    │(Port5432)│  │(Port11434)│  │              │
    └──────────┘  └───────────┘  └──────────────┘
```

---

## Complete Vulnerability Pipeline

### Step 1: Fetch Repository
```
Input: GitHub URL + optional token
↓
Connects to GitHub API
Downloads all source code files
Filters to relevant code (py, js, ts, java, etc.)
Respects file size limits (max 5KB per file, max 5 files)
Output: CodeSnapshot stored in database
```

### Step 2: Root Cause Analysis
```
Input: Code snapshot + vulnerability type
↓
Sends prompt to local Ollama LLM
"Analyze this code for SQL_INJECTION vulnerabilities"
LLM processes code and generates analysis
Output: 
  - Root cause explanation
  - Attack vector description
  - Proof of concept code
  - Recommended fix
```

### Step 3: Generate Exploits
```
Input: Vulnerability type (SQL_INJECTION, XSS, COMMAND_INJECTION, PATH_TRAVERSAL)
↓
ExploitGenerator creates test payloads from templates
SQL_INJECTION: OR-based, UNION-based, Time-based blind, etc.
XSS: Script injection, event handlers, etc.
COMMAND_INJECTION: Shell metacharacters, command chaining, etc.
PATH_TRAVERSAL: Relative paths, double encoding, null bytes, etc.
Output: List of 20 unique exploit payloads per type
```

### Step 4: Execute Exploits in Docker
```
Input: Exploit payload + source code snapshot
↓
Creates temporary secure Docker container
Mounts code snapshot as read-only volume
Executes exploit test script
Captures stdout/stderr/return code
Analyzes output to detect exploitation success
Logs all execution details
Output: 
  - vulnerable: true/false
  - stdout/stderr logs
  - execution time
  - container ID for forensics
```

### Step 5: Static Analysis
```
Input: Code snapshot
↓
Runs code pattern analysis
Detects common vulnerability patterns
Counts critical/high/medium/low findings
Output: ScanResult with finding counts
```

### Step 6: Aggregate Results
```
Input: Exploit results + scan results
↓
Combines execution findings
Determines overall vulnerability confirmation
Calculates confidence score
Output: Aggregated assessment
```

### Step 7: Calculate CVSS Score
```
Input: Vulnerability confirmed + exploitability + impact
↓
Base score = 7.5 - 10.0 if vulnerable
Adjusts based on confidence and impact
Severity levels:
  - CRITICAL (9.0-10.0)
  - HIGH (7.0-8.9)
  - MEDIUM (4.0-6.9)
  - LOW (0.0-3.9)
Output: Full CVSS vector + score
```

### Step 8: Generate Report
```
Input: Analysis data + scores + exploit results
↓
Creates HTML report with styling
Creates JSON report for programmatic access
Optional: Creates PDF if reportlab installed
Reports include:
  - Executive summary
  - Root cause analysis
  - CVSS score & severity
  - Exploit validation results
  - Technical details
  - Recommendations
Output: Report file + database record
```

### Step 9: Store Results
```
Input: All analysis data
↓
Stores in PostgreSQL:
  - AnalysisResult: Root cause, confidence
  - VulnerabilityScore: CVSS, severity
  - ExploitExecution: All exploit details
  - ScanResult: Static analysis findings
  - Report: Reference to generated report
Output: Complete audit trail
```

---

## Database Schema

### Core Tables

**users**
```sql
id (UUID primary key)
email (unique)
password_hash
role (user, admin)
created_at
```

**bug_reports**
```sql
id (UUID primary key)
project_id (foreign key)
title, description
severity, cve_id
affected_file, affected_line
source (manual, automated)
created_at
Relationships: project, code_snapshots, analysis_results
```

**analysis_results**
```sql
id (UUID primary key)
bug_report_id (foreign key)
root_cause (text)
exploit_payload (text)
suggested_patch (text)
confidence_score (0.0-1.0)
created_at
Relationships: exploit_executions, scan_results, vulnerability_score
```

**exploit_executions**
```sql
id (UUID primary key)
analysis_result_id (foreign key)
exploit_type (SQL_INJECTION, XSS, etc.)
exploit_payload
execution_status (pending, running, success, failed)
stdout, stderr
return_code
execution_time_ms
vulnerable (boolean)
docker_container_id
started_at, completed_at
```

**vulnerability_scores**
```sql
id (UUID primary key)
analysis_result_id (unique foreign key)
cvss_score (0.0-10.0)
cvss_vector (AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H)
severity (CRITICAL, HIGH, MEDIUM, LOW)
exploitability (0.0-1.0)
impact_score (0.0-1.0)
confidence (0.0-1.0)
created_at
```

**reports**
```sql
id (UUID primary key)
analysis_result_id (unique foreign key)
report_format (pdf, html, json)
file_path
file_size
generated_at
```

---

## API Endpoints

### Analysis

**POST /api/analysis/analyze**
```json
Request:
{
  "repo_url": "https://github.com/owner/repo",
  "vulnerability_type": "SQL_INJECTION",
  "affected_file": "app.py",
  "affected_line": 42,
  "github_token": "optional-github-token"
}

Response:
{
  "status": "completed",
  "analysis_id": "uuid-of-analysis",
  "score": 8.5,
  "severity": "HIGH",
  "report_url": "/reports/uuid/html",
  "vulnerable": true,
  "exploits_tested": 20
}
```

**GET /api/analysis/results/{analysis_id}**
```json
Response:
{
  "analysis_id": "uuid",
  "root_cause": "Unsanitized user input in SQL query",
  "confidence_score": 0.92,
  "vulnerability_score": {
    "cvss_score": 8.5,
    "severity": "HIGH",
    "cvss_vector": "AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:H/A:H"
  },
  "report_url": "/reports/uuid",
  "created_at": "2024-03-26T10:30:00Z"
}
```

**GET /api/analysis/reports/{analysis_id}/{format}**
- `format`: html, pdf, or json
- Returns: File download

**GET /api/analysis/exploit-results/{analysis_id}**
```json
Response:
{
  "analysis_id": "uuid",
  "total_executions": 20,
  "vulnerable_exploits": 8,
  "executions": [
    {
      "exploit_type": "SQL_INJECTION",
      "vulnerable": true,
      "status": "success",
      "return_code": 0,
      "execution_time_ms": 234
    }
  ]
}
```

**GET /api/analysis/health**
```json
Response:
{
  "status": "healthy",
  "ai_service": "ready",
  "available_models": ["mistral", "llama2"]
}
```

### Authentication

**POST /api/auth/register**
```json
Request:
{
  "email": "user@example.com",
  "password": "secure-password"
}
Response:
{
  "message": "Registration successful"
}
```

**POST /api/auth/login**
```json
Request:
{
  "email": "user@example.com",
  "password": "secure-password"
}
Response:
{
  "access_token": "jwt-token",
  "token_type": "bearer"
}
```

---

## Environment Configuration

### Backend (.env)

```env
# Database
DATABASE_URL=sqlite:///./zorix.db
# Or PostgreSQL:
# DATABASE_URL=postgresql+asyncpg://user:pass@localhost/zorix

# GitHub
GITHUB_TOKEN=ghp_optional_for_private_repos

# Ollama AI
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=mistral
OLLAMA_TIMEOUT=180

# CORS
ALLOWED_ORIGINS=["http://localhost:3000","http://localhost:3001","http://localhost:5173"]

# JWT
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### Frontend (vite.config.js)

```javascript
export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  }
})
```

---

## Docker Sandbox Security

The sandbox Docker execution provides:

✓ **Isolation** - Each exploit runs in its own container  
✓ **Resource Limits** - 512MB memory, 1 CPU per container  
✓ **Network Disabled** - Prevents exploitation spreading  
✓ **Read-only Mounts** - Code snapshot cannot be modified  
✓ **Process Isolation** - Linux namespaces separate processes  
✓ **Automatic Cleanup** - Container removed after execution  

---

## Running the System

### 1. Install Dependencies

```bash
# Backend
cd backend
pip install -r requirements.txt

# Frontend
cd frontend
npm install
npm install react-router-dom
```

### 2. Start Services

**Terminal 1: PostgreSQL** (or skip if using SQLite)
```bash
# Docker
docker run -e POSTGRES_PASSWORD=zorix -p 5432:5432 postgres:15
```

**Terminal 2: Ollama AI**
```bash
# Install Ollama from https://ollama.ai
ollama serve
ollama pull mistral
```

**Terminal 3: Backend**
```bash
cd backend
python -m uvicorn main:app --reload
```

**Terminal 4: Frontend**
```bash
cd frontend
npm run dev
```

### 3. Access System

Open browser: **http://localhost:3001**

```
Login:
  Email: demo@zorix.local
  Password: demo123

Or register a new account
```

---

## Example Usage

### 1. Manual Analysis

```bash
curl -X POST http://localhost:8000/api/analysis/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "repo_url": "https://github.com/sqlalchemy/sqlalchemy",
    "vulnerability_type": "SQL_INJECTION",
    "affected_file": "lib/sqlalchemy/sql.py",
    "github_token": null
  }'
```

### 2. Check Results

```bash
curl http://localhost:8000/api/analysis/results/{analysis_id}
```

### 3. Download Report

```bash
curl http://localhost:8000/api/analysis/reports/{analysis_id}/html \
  -o report.html
```

---

## Key Components

### Services

**pipeline_orchestrator.py**
- Orchestrates full vulnerability validation pipeline
- Coordinates all 9 pipeline steps
- Handles data flow between services

**exploit_execution_service.py**
- Manages exploit execution coordination
- Executes exploits in Docker sandbox
- Logs all execution details

**docker_sandbox.py**
- Docker container management
- Exploit execution environment
- Result analysis and logging

**report_generation_service.py**
- Generates HTML/PDF/JSON reports
- Professional formatting
- Detailed vulnerability documentation

**ai_analysis_service.py** (Ollama)
- Local LLM integration
- Root cause analysis
- Vulnerability explanation

**github_service.py**
- Repository fetching
- Code file filtering
- GitHub API integration

### Models

**exploit_generator.py**
- Payload template management
- Exploit mutation and variation
- Type-specific exploit generation

**mutations.py**
- Payload obfuscation
- WAF bypass techniques
- Encoding variations

---

## Troubleshooting

### API Returns "Backend not reachable"
```bash
# Check if backend is running
curl http://localhost:8000/

# Restart and check logs
python -m uvicorn backend.main:app --reload
```

### "AI Service not ready"
```bash
# Check Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama and pull model
ollama serve &
ollama pull mistral
```

### Docker execution fails
```bash
# Check if Docker daemon is running
docker ps

# On Linux, may need permissions
sudo usermod -aG docker $USER
```

### Database errors
```bash
# Reset SQLite database
rm zorix.db
# Backend will auto-create on startup

# Or use PostgreSQL
export DATABASE_URL="postgresql+asyncpg://user:pass@localhost/zorix"
```

---

## Security Considerations

⚠️ **For Production Deployment:**

1. **Use PostgreSQL** - Not SQLite
2. **Enable HTTPS** - Use valid SSL certificates
3. **Secure GitHub Token** - Use environment variables, never commit
4. **JWT Secret** - Use strong 32+ character secret
5. **CORS** - Restrict to authenticated origins only
6. **Rate Limiting** - Add API rate limits
7. **Audit Logging** - Enable detailed logging
8. **Database Encryption** - Encrypt sensitive data at rest
9. **Docker Security** - Run with seccomp, apparmor, SELinux
10. **Input Validation** - Sanitize all user inputs

---

## Performance Optimization

- **Async Database Operations** - Non-blocking I/O
- **Docker Container Reuse** - Consider container pools
- **Report Caching** - Cache frequently accessed reports
- **Database Indexing** - Index on cve_id, analysis_result_id
- **API Pagination** - Limit large result sets
- **Exploit Parallelization** - Run multiple exploits concurrently

---

## Future Enhancements

- [ ] Kubernetes deployment
- [ ] Multi-tenant architecture
- [ ] Webhook notifications
- [ ] Slack/Teams integration
- [ ] Grafana dashboards
- [ ] Machine learning for false positive reduction
- [ ] Custom payload templates
- [ ] Automated patching recommendations
- [ ] CVE database integration
- [ ] Source code control integration (GitLab, Bitbucket)

---

## Support & Documentation

For detailed API documentation, visit: `http://localhost:8000/docs`

Swagger UI provides interactive API testing and exploration.

---

**Zorix - Exposing Threats, Certifying Trust** 🛡️
