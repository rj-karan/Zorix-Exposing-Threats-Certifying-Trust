CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

DO $$
BEGIN
  RAISE NOTICE 'Zorix database initialized successfully';
END $$;
```

---

### `.env.example`
```
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=zorix_db
POSTGRES_USER=zorix_user
POSTGRES_PASSWORD=your_password_here

SECRET_KEY=your_secret_key_here
DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000

GITHUB_TOKEN=your_github_token_here
NVD_API_KEY=your_nvd_key_here
CLAUDE_API_KEY=your_claude_key_here
```

---

### `.env.dev`
```
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=zorix_db
POSTGRES_USER=zorix_user
POSTGRES_PASSWORD=devpassword123

SECRET_KEY=dev_secret_key_not_for_production
DEBUG=True
ALLOWED_ORIGINS=http://localhost:3000

GITHUB_TOKEN=
NVD_API_KEY=
CLAUDE_API_KEY=
```

---

### `.env.prod`
```
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_DB=zorix_db
POSTGRES_USER=zorix_user
POSTGRES_PASSWORD=CHANGE_THIS_STRONG_PASSWORD

SECRET_KEY=CHANGE_THIS_TO_LONG_RANDOM_STRING
DEBUG=False
ALLOWED_ORIGINS=https://yourdomain.com

GITHUB_TOKEN=
NVD_API_KEY=
CLAUDE_API_KEY=
```

---

### `.gitignore`
```
.env
.env.dev
.env.prod
*.env
__pycache__/
*.pyc
node_modules/
dist/
build/
docker/postgres/data/
Thumbs.db
.DS_Store
.vscode/
*.log
```

---

### `.gitattributes`
```
*.sh        text eol=lf
*.yml       text eol=lf
*.yaml      text eol=lf
*.sql       text eol=lf
*.conf      text eol=lf
Dockerfile  text eol=lf
*.env*      text eol=lf