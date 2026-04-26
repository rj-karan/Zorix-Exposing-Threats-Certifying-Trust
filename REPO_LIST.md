# 🧪 Vulnerable Repository Test List
## For Zorix — AI Security Validation Platform

> These are **intentionally vulnerable** open‑source applications designed for security testing and education. Use them only in isolated environments.

---

## 🔴 SQL Injection

| # | Repository | Language | Description |
|---|-----------|----------|-------------|
| 1 | [OWASP/NodeGoat](https://github.com/OWASP/NodeGoat) | Node.js | OWASP intentionally vulnerable Node.js app with SQL/NoSQL injection |
| 2 | [appsecco/dvna](https://github.com/appsecco/dvna) | Node.js | Damn Vulnerable NodeJS Application — multiple SQLi vectors |
| 3 | [digininja/DVWA](https://github.com/digininja/DVWA) | PHP | Damn Vulnerable Web Application — classic SQLi playground |
| 4 | [stamparm/DSVW](https://github.com/stamparm/DSVW) | Python | Damn Small Vulnerable Web — minimal SQLi‑focused app |
| 5 | [nicholasmckinney/BAD-BLOG](https://github.com/nicholasmckinney/BAD-BLOG) | Python | Vulnerable Flask blog with raw SQL queries |

---

## 🟠 Cross‑Site Scripting (XSS)

| # | Repository | Language | Description |
|---|-----------|----------|-------------|
| 1 | [nicholasmckinney/BAD-BLOG](https://github.com/nicholasmckinney/BAD-BLOG) | Python | Reflected & stored XSS in Flask templates |
| 2 | [OWASP/NodeGoat](https://github.com/OWASP/NodeGoat) | Node.js | Multiple XSS vectors via unescaped user input |
| 3 | [digininja/DVWA](https://github.com/digininja/DVWA) | PHP | Dedicated reflected, stored, and DOM XSS modules |
| 4 | [payloadbox/xss-payload-list](https://github.com/payloadbox/xss-payload-list) | Payloads | Comprehensive XSS payload reference list |
| 5 | [WebGoat/WebGoat](https://github.com/WebGoat/WebGoat) | Java | OWASP WebGoat — XSS lessons with difficulty levels |

---

## 🟡 Command Injection (OS Command Injection)

| # | Repository | Language | Description |
|---|-----------|----------|-------------|
| 1 | [OWASP/NodeGoat](https://github.com/OWASP/NodeGoat) | Node.js | OS command injection via child_process |
| 2 | [digininja/DVWA](https://github.com/digininja/DVWA) | PHP | Dedicated command injection module (ping wrapper) |
| 3 | [stamparm/DSVW](https://github.com/stamparm/DSVW) | Python | Command injection via os.popen / subprocess |
| 4 | [appsecco/dvna](https://github.com/appsecco/dvna) | Node.js | exec() command injection in Node.js |
| 5 | [snyk-labs/nodejs-goof](https://github.com/snyk-labs/nodejs-goof) | Node.js | Vulnerable to-do app with command injection via eval |

---

## 🟢 Path Traversal (Directory Traversal / LFI)

| # | Repository | Language | Description |
|---|-----------|----------|-------------|
| 1 | [digininja/DVWA](https://github.com/digininja/DVWA) | PHP | File inclusion module — LFI/RFI with path traversal |
| 2 | [stamparm/DSVW](https://github.com/stamparm/DSVW) | Python | Path traversal via unsanitized file read |
| 3 | [appsecco/dvna](https://github.com/appsecco/dvna) | Node.js | Directory traversal in file download handler |
| 4 | [OWASP/NodeGoat](https://github.com/OWASP/NodeGoat) | Node.js | Path traversal via file upload/download |
| 5 | [WebGoat/WebGoat](https://github.com/WebGoat/WebGoat) | Java | Path traversal lesson with multiple bypass methods |

---

## 🔵 Cross‑Site Request Forgery (CSRF)

| # | Repository | Language | Description |
|---|-----------|----------|-------------|
| 1 | [digininja/DVWA](https://github.com/digininja/DVWA) | PHP | CSRF module — password change without token validation |
| 2 | [OWASP/NodeGoat](https://github.com/OWASP/NodeGoat) | Node.js | Missing CSRF token on state‑changing endpoints |
| 3 | [WebGoat/WebGoat](https://github.com/WebGoat/WebGoat) | Java | CSRF lessons with token bypass techniques |
| 4 | [appsecco/dvna](https://github.com/appsecco/dvna) | Node.js | No CSRF protection on sensitive routes |
| 5 | [bkimminich/juice-shop](https://github.com/juice-shop/juice-shop) | Node.js | OWASP Juice Shop — CSRF among 100+ vulnerability challenges |

---

## 🟣 XXE (XML External Entity Injection)

| # | Repository | Language | Description |
|---|-----------|----------|-------------|
| 1 | [WebGoat/WebGoat](https://github.com/WebGoat/WebGoat) | Java | XXE lesson — reads /etc/passwd via XML parser |
| 2 | [c0ny1/xxe-lab](https://github.com/c0ny1/xxe-lab) | PHP/Java/Python | Dedicated XXE testing lab in multiple languages |
| 3 | [jbarone/xxeserv](https://github.com/jbarone/xxeserv) | Go | XXE OOB (out-of-band) exfiltration test server |
| 4 | [BuffaloWill/oxml_xxe](https://github.com/BuffaloWill/oxml_xxe) | Ruby | XXE via OXML document formats (docx, xlsx, etc.) |
| 5 | [payloadbox/xxe-injection-payload-list](https://github.com/payloadbox/xxe-injection-payload-list) | Payloads | Comprehensive XXE payload reference list |

---

## 🏆 All‑in‑One (Multiple Vulnerability Types)

These single repos contain **all six** vulnerability categories above:

| # | Repository | Language | Vuln Coverage |
|---|-----------|----------|---------------|
| 1 | [digininja/DVWA](https://github.com/digininja/DVWA) | PHP | SQLi, XSS, CMDi, Path Traversal, CSRF, File Upload |
| 2 | [OWASP/NodeGoat](https://github.com/OWASP/NodeGoat) | Node.js | SQLi, XSS, CMDi, Path Traversal, CSRF |
| 3 | [WebGoat/WebGoat](https://github.com/WebGoat/WebGoat) | Java | SQLi, XSS, CMDi, Path Traversal, CSRF, XXE |
| 4 | [juice-shop/juice-shop](https://github.com/juice-shop/juice-shop) | Node.js | 100+ challenges across all OWASP Top 10 |
| 5 | [appsecco/dvna](https://github.com/appsecco/dvna) | Node.js | SQLi, XSS, CMDi, Path Traversal, CSRF |

---

## ⚡ Quick Test Commands

Paste any of these URLs into the Zorix **Analysis** page:

```
https://github.com/OWASP/NodeGoat
https://github.com/stamparm/DSVW
https://github.com/appsecco/dvna
https://github.com/snyk-labs/nodejs-goof
https://github.com/digininja/DVWA
https://github.com/WebGoat/WebGoat
```

> ⚠️ **Warning**: These repos contain intentionally vulnerable code. Never deploy them in production environments.
