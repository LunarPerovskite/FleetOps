# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x (beta) | ✅ Current |

## Reporting a Vulnerability

We take security seriously. If you discover a security vulnerability, please report it responsibly.

### How to Report

1. **Do NOT** open a public issue
2. Email security@fleetops.io with:
   - Description of the vulnerability
   - Steps to reproduce
   - Potential impact
   - Suggested fix (if any)

### Response Timeline

- **Acknowledgment**: Within 48 hours
- **Initial Assessment**: Within 7 days
- **Fix Released**: Within 30 days (critical), 60 days (high), 90 days (medium)
- **Public Disclosure**: After fix is released and users have had time to update

### What We Promise

- We will acknowledge your report promptly
- We will investigate thoroughly
- We will fix verified vulnerabilities
- We will credit you in the advisory (unless you prefer anonymity)
- We will not take legal action against researchers who follow responsible disclosure

## Security Features

FleetOps includes:

- JWT authentication with configurable expiry
- CSP, XSS, CSRF protection
- Rate limiting on all endpoints
- Input validation and sanitization
- Immutable evidence store with cryptographic signatures
- Role-based access control

## Best Practices

When deploying FleetOps:

1. Use HTTPS in production
2. Set strong JWT secrets
3. Enable rate limiting
4. Keep dependencies updated
5. Review provider security configurations
6. Enable monitoring and alerting
