# Zorix Backend - AI-Powered Vulnerability Analysis Platform

## Overview

Production-ready FastAPI backend for analyzing code vulnerabilities. The system fetches real code from GitHub repositories and uses AI reasoning to perform root cause analysis, exploit generation, and patch suggestions.

## Architecture

```
backend/
├── main.py                 # FastAPI app entry point + lifespan management
├── config.py              # Configuration management (environment variables)
├── database.py            # SQLAlchemy async setup + database session
├── models.py              # Database models (User, Project, BugReport, etc.)
├── schemas.py             # Pydantic request/response schemas
│
├── core/                  # Core business logic
│   ├── security.py        # JWT + password hashing (bcrypt)
│   ├── github_service.py  # GitHub API interaction + code fetching
│   ├── ai_analysis.py     # AI reasoning engine (mock + extensible)
│   └── scoring.py         # Severity scoring (CVSS-like)
│
├── services/              # Application services
│   ├── user_service.py    # User operations
│   ├── report_service.py  # Project & bug report operations
│   └── analysis_service.py # Full analysis pipeline orchestration
│
└── api/
    ├── deps.py            # Dependency injection (authentication)
    └── routes/
        ├── auth.py        # Register, login
        └── analysis.py    # Reports, analysis results, projects
```

## Key Features

### 1. Authentication (JWT + Bcrypt)
- User registration with email validation
- Secure login returning JWT tokens
- Password hashing with bcrypt
- Dependency-based authentication on protected routes

### 2. Bug Report API
```
POST /reports
  Input: project_id, title, description, affected_file, affected_line, severity, cve_id
  Pipeline:
    1. Fetch live code from GitHub repository
    2. Extract affected file and context (±10 lines)
    3. Create code snapshot
    4. Run AI analysis on extracted code
    5. Compute severity score
    6. Store analysis results
```

### 3. GitHub Integration
- Fetches code directly from repository URL
- Extracts affected file with configurable context lines
- Supports authentication (optional GitHub token)
- Error handling for missing files/repos

### 4. AI Analysis Service
- Input: bug description + real code from GitHub + security knowledge
- Output: structured JSON with root_cause, exploit_payload, suggested_patch, confidence_score
- Extensible for LLM integration (OpenAI, Claude, Ollama, etc.)
- Includes mock reasoning for demo/testing

### 5. Analysis Results API
```
GET /analysis/{report_id}
  Returns: root_cause, exploit_payload, suggested_patch, confidence_score
```

## Database Schema

### User
- id (UUID)
- email (unique)
- password_hash
- role
- created_at

### Project
- id (UUID)
- user_id (FK)
- name
- repository_url
- created_at

### BugReport
- id (UUID)
- project_id (FK)
- title, description
- severity, cve_id
- affected_file, affected_line
- source (manual/auto)
- created_at

### CodeSnapshot
- id (UUID)
- bug_report_id (FK)
- repo_url
- commit_hash
- snapshot_data (JSON)
- created_at

### AnalysisResult
- id (UUID)
- bug_report_id (FK)
- root_cause, exploit_payload, suggested_patch
- confidence_score
- created_at

## Running the Backend

### Local Development

```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.dev .env

# Run migrations (if needed)
alembic upgrade head

# Start server
uvicorn backend.main:app --reload --port 8000
```

### Docker (with docker-compose)

```bash
# From repository root
docker-compose up --build

# Backend runs on http://localhost:8000
# PostgreSQL on localhost:5432
```

## API Endpoints

### Authentication
```
POST /auth/register
  Body: { "email": "user@example.com", "password": "secure_password" }
  Returns: User object + created_at
  
POST /auth/login
  Body: { "email": "user@example.com", "password": "secure_password" }
  Returns: { "access_token": "...", "token_type": "bearer", "user": {...} }
```

### Projects
```
POST /projects
  Auth: Required (Bearer token)
  Body: { "name": "MyProject", "repository_url": "https://github.com/user/repo" }
  Returns: Project object

GET /projects
  Auth: Required
  Returns: List of user's projects

GET /projects/{project_id}
  Auth: Required
  Returns: Project object
```

### Bug Reports & Analysis (Core Pipeline)
```
POST /reports
  Auth: Required
  Body: {
    "project_id": "uuid",
    "title": "SQL Injection in login",
    "description": "Unsanitized user input in database query",
    "affected_file": "app/auth.py",
    "affected_line": 42,
    "severity": "high",
    "cve_id": null
  }
  Returns: BugReport object
  Action: Automatically runs full analysis pipeline

GET /reports
  Auth: Required
  Query: ?project_id=uuid
  Returns: List of bug reports for project

GET /reports/{report_id}
  Auth: Required
  Returns: BugReport object

GET /analysis/{report_id}
  Auth: Required
  Returns: AnalysisResult object with root cause, exploit, patch, score
```

## Example Workflow

```bash
# 1. Register
curl -X POST http://localhost:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email": "analyst@zorix.io", "password": "SecurePass123"}'

# 2. Login
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "analyst@zorix.io", "password": "SecurePass123"}'
# Returns: {"access_token": "eyJ0eXAiOiJKV1Q...", "token_type": "bearer", ...}

# 3. Create project (use token from login)
curl -X POST http://localhost:8000/projects \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1Q..." \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Django Ecommerce",
    "repository_url": "https://github.com/django/django"
  }'
# Returns: {"id": "abc-123", "name": "Django Ecommerce", ...}

# 4. Create bug report + trigger analysis
curl -X POST http://localhost:8000/reports \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1Q..." \
  -H "Content-Type: application/json" \
  -d '{
    "project_id": "abc-123",
    "title": "SQL Injection in ORM",
    "description": "Insufficient parameterization in database queries",
    "affected_file": "django/db/models.py",
    "affected_line": 256,
    "severity": "critical",
    "cve_id": "CVE-2024-12345"
  }'
# Pipeline executes automatically:
# - Fetches django/db/models.py from GitHub
# - Extracts code context around line 256
# - Creates snapshot
# - Runs AI analysis
# - Computes score
# Returns: BugReport object

# 5. Get analysis results
curl -X GET http://localhost:8000/analysis/abc-123 \
  -H "Authorization: Bearer eyJ0eXAiOiJKV1Q..."
# Returns: {
#   "root_cause": "...",
#   "exploit_payload": "...",
#   "suggested_patch": "...",
#   "confidence_score": 8.75
# }
```

## Configuration

### Environment Variables (.env)

```
# Database
POSTGRES_HOST=localhost
POSTGRES_PORT=5432
POSTGRES_DB=zorix
POSTGRES_USER=zorix_user
POSTGRES_PASSWORD=zorix_password

# Security
SECRET_KEY=your-secret-key-here
ACCESS_TOKEN_EXPIRE_MINUTES=30

# GitHub (optional)
GITHUB_TOKEN=ghp_your_github_token

# Application
DEBUG=False
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8000
```

## Tech Stack

- **Framework**: FastAPI 0.104.1
- **Server**: Uvicorn 0.24.0
- **Database**: PostgreSQL + SQLAlchemy 2.0 (async)
- **ORM**: SQLAlchemy with async support
- **Authentication**: JWT (PyJWT) + Bcrypt
- **Validation**: Pydantic 2.5
- **GitHub Integration**: httpx (async HTTP client)
- **Migrations**: Alembic

## Development Notes

### Adding New Features

1. **New Database Model**: Add to `backend/models.py`
2. **API Schema**: Add to `backend/schemas.py`
3. **Business Logic**: Add service to `backend/services/`
4. **Routes**: Add to `backend/api/routes/`
5. **Core Logic**: Add to `backend/core/` if cross-cutting

### Extending AI Analysis

The `AIAnalysisService` in `core/ai_analysis.py` is a mock implementation. To use real AI:

```python
# Replace _mock_ai_reasoning() with:
async def _call_llm(self, prompt: str) -> dict:
    # OpenAI example:
    import openai
    response = await openai.ChatCompletion.acreate(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
    )
    return json.loads(response.choices[0].message.content)
```

### GitHub Token Setup

For higher rate limits:

```bash
# Create GitHub personal access token with 'repo' scope
# Add to .env:
GITHUB_TOKEN=ghp_your_token_here
```

## Error Handling

- 400: Bad request (validation errors)
- 401: Unauthorized (invalid/missing token)
- 403: Forbidden (access denied)
- 404: Not found (resource doesn't exist)
- 500: Server error (logged)

## Production Checklist

- [ ] Change SECRET_KEY in .env
- [ ] Set DEBUG=False
- [ ] Configure ALLOWED_ORIGINS correctly
- [ ] Add GitHub token if needed
- [ ] Set up proper logging
- [ ] Configure database backups
- [ ] Use HTTPS in production
- [ ] Set strong database password
- [ ] Review and test all endpoints
- [ ] Set up monitoring/alerting

## Docker Integration

The backend integrates seamlessly with the existing docker-compose setup:

```yaml
backend:
  build:
    context: .
    dockerfile: docker/backend/Dockerfile
  environment:
    - POSTGRES_HOST=postgres  # Service name from docker-compose
    - POSTGRES_DB=${POSTGRES_DB}
    - POSTGRES_USER=${POSTGRES_USER}
    - POSTGRES_PASSWORD=${POSTGRES_PASSWORD}
  depends_on:
    postgres:
      condition: service_healthy
  ports:
    - "8000:8000"
```

The entrypoint script automatically:
1. Waits for database readiness
2. Runs migrations (alembic upgrade head)
3. Starts FastAPI server on 0.0.0.0:8000

## Support

For issues or questions:
1. Check the GitHub repository
2. Review logs: `docker-compose logs -f backend`
3. Test endpoints with provided curl examples
