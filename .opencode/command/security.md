---
description: Audit code for security vulnerabilities.
---

# Security Audit Prompt

You are tasked with performing a comprehensive security audit on the following code or system.

## Input

{{input}}

## Security Audit Framework

Assess each area below. Assign severity using the following scale:

| Severity | Definition | Response Time |
|----------|------------|---------------|
| CRITICAL | Active exploitation possible, data breach risk | Immediate |
| HIGH     | Significant vulnerability, limited exploitation | < 24 hours |
| MEDIUM   | Moderate risk, requires specific conditions | < 1 week |
| LOW      | Minor issue, defense-in-depth improvement | < 1 month |
| INFO     | Informational, best practice recommendation | Backlog |

## OWASP Top 10 (2021)

### A01: Broken Access Control

- Can users access resources they should not have access to?
- Are authorization checks performed on every request (not just UI hiding)?
- Is there IDOR (Insecure Direct Object Reference) allowing access to other users data?
- Are role-based or attribute-based access controls properly enforced server-side?
- Are API endpoints protected against privilege escalation?
- Is there proper separation between authenticated and unauthenticated routes?

### A02: Cryptographic Failures

- Are passwords hashed with a strong, slow algorithm (bcrypt, argon2, scrypt)?
- Are all communications over TLS (HTTPS, WSS) with valid certificates?
- Are TLS versions 1.2+ enforced (no SSL, no TLS 1.0/1.1)?
- Are secrets, API keys, and tokens stored securely (vault, HSM, environment variables)?
- Is sensitive data encrypted at rest (AES-256)?
- Are cryptographic keys managed securely (rotation, access control, key ceremony)?

### A03: Injection

- **SQL/NoSQL Injection**: Are all database queries parameterized or using an ORM safely?
- **Command Injection**: Are system commands built from user input sanitized?
- **Cross-Site Scripting (XSS)**: Is user input properly escaped before rendering in HTML?
  - Reflected XSS: input in URL parameters
  - Stored XSS: input stored in database
  - DOM-based XSS: client-side injection
- **Template Injection**: Are server-side templates free from user-controlled expressions?
- **LDAP, XML, SSRF**: Are other injection vectors covered?

### A04: Insecure Design

- Are security requirements considered in the design phase?
- Is there a threat model for the application?
- Are rate limits and throttling implemented?
- Are security controls applied consistently across the application?
- Is there proper error handling that does not leak sensitive information?
- Are default configurations secure?

### A05: Security Misconfiguration

- Are default credentials changed?
- Is unnecessary functionality disabled (debug endpoints, admin consoles)?
- Are security headers configured (CSP, HSTS, X-Frame-Options, X-Content-Type-Options)?
- Is CORS properly restricted to trusted origins?
- Are cloud resources properly configured (S3 buckets, IAM roles, security groups)?
- Are directory listings disabled on web servers?

### A06: Vulnerable and Outdated Components

- Are all dependencies up to date with no known CVEs?
- Is there a Software Bill of Materials (SBOM)?
- Are automated dependency scanning tools in place (Dependabot, Snyk, OWASP Dependency-Check)?
- Is the language runtime and framework at a supported version?
- Are unused dependencies removed?

### A07: Identification and Authentication Failures

- Is multi-factor authentication available and encouraged?
- Are session tokens properly generated (cryptographically random), stored (httpOnly, secure), and expired?
- Is there account lockout after failed login attempts?
- Are password policies reasonable and enforced?
- Is credential stuffing mitigated (rate limiting, CAPTCHA)?
- Are JWT tokens signed with a strong secret and properly validated?

### A08: Software and Data Integrity Failures

- Are CI/CD pipelines secured against supply chain attacks?
- Are artifacts signed and verified before deployment?
- Are dependencies pinned to specific versions or hashes?
- Is code signing used for releases?
- Are third-party scripts and libraries integrity-checked (SRI for web)?

### A09: Security Logging and Monitoring Failures

- Are security-relevant events logged (logins, access control failures, input validation errors)?
- Are logs protected from tampering and unauthorized access?
- Is there centralized logging with alerting?
- Are suspicious activities detected and alerted?
- Is there an incident response plan?

### A10: Server-Side Request Forgery (SSRF)

- Are user-supplied URLs validated against an allowlist?
- Is internal network access restricted from application servers?
- Are outbound network requests subject to firewall rules?
- Is the URL scheme restricted (no file://, etc.)?

## Additional Security Checks

### Secrets Management

- Are there any hardcoded secrets, passwords, or tokens in the codebase?
- Are .env files, credentials, and certificate files in .gitignore?
- Is the secrets scanning tool configured in CI/CD?
- Are secrets rotated on a regular schedule?

### Input Validation

- Are all inputs validated for type, length, format, and range?
- Is input validation performed server-side (not just client-side)?
- Are file uploads restricted by type, size, and content inspection?
- Are uploads stored outside the web root?

### Output Encoding

- Is output contextually encoded based on where it is rendered (HTML, JavaScript, CSS, URL)?
- Are Content-Type headers set correctly?
- Is JSON/API output free from sensitive data leakage?

### Authentication & Session Management

- Are password reset tokens time-limited and single-use?
- Are API keys, OAuth tokens, and session tokens revocable?
- Is there an allowlist for redirect URLs after authentication?
- Are concurrent session limits enforced?

## Reporting Format

### Vulnerability Report

```
### [SEVERITY] Vulnerability Title

- **CVE/CWE**: CWE-89 (SQL Injection)
- **Location**: file:line
- **Description**: What is vulnerable and why
- **Impact**: What an attacker can achieve (data access, RCE, privilege escalation)
- **Exploitability**: Easy / Moderate / Difficult
- **Proof of Concept**: Steps to reproduce or code example
- **Remediation**: Specific fix or mitigation steps
- **Code fix**:

\`\`\`language
// vulnerable code
// fixed code
\`\`\`
```

### Summary Table

| # | Severity | Vulnerability | Location | Status |
|---|----------|---------------|----------|--------|
| 1 | CRITICAL | SQL Injection | users.php:45 | Open |
| 2 | HIGH | XSS | search.php:12 | Fixed |

### Recommendations

- Prioritized remediation plan
- Security training needs
- Process improvements for secure development lifecycle
- Tooling recommendations (SAST, DAST, SCA)
