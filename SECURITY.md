# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 2.x     | ✅ Active support   |
| 1.x     | ❌ End of life      |

## Reporting a Vulnerability

If you discover a security vulnerability in HireOS, please report it responsibly:

1. **Do NOT** open a public GitHub issue
2. Email: **dev@saurabhgaur.dev** with subject line `[SECURITY] HireOS Vulnerability`
3. Include: description, reproduction steps, potential impact
4. You will receive acknowledgment within 48 hours

## Security Measures

HireOS implements the following security controls:

- **Per-IP rate limiting** — 10 AI calls/min, pure Python (no Redis)
- **Input sanitization** — null bytes, control chars, max sizes enforced
- **File type allowlist** — PDF, DOCX, TXT only
- **Error masking** — internal stack traces never leaked to clients
- **API key isolation** — keys only in environment variables, never in code
- **Zero data retention** — resumes processed in memory, never stored
- **Owner bypass protection** — SHA-256 hashed secret, never in source

## Production Recommendations

- Enforce HTTPS across all public client connections.
- Rely on proxy/load-balancer rate limits (e.g. Nginx, Cloudflare) in production.

## Secrets Management

- Rotate API keys every 90 days to minimize leakage impact.
- Ensure keys are not committed to source version control.

## Validation Bounds

- File limits (3MB max) and parsing truncations (10k chars max) protect host resources.

## Dependencies

We regularly audit dependencies for known vulnerabilities.
Report dependency issues via the same email channel above.
