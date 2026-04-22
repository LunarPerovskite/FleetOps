# FleetOps Security

## Status: 🔒 Enterprise-Grade Security Framework

### Security Packages (Production-Grade)
| Package | Version | Purpose |
|---------|---------|---------|
| **cryptography** | 42.0.0 | Fernet, AES-256, RSA, X509, TLS |
| **passlib** | 1.7.4 | bcrypt, argon2 password hashing |
| **argon2-cffi** | 23.1.0 | Argon2id (OWASP recommended) |
| **pyjwt** | 2.8.0 | JWT signing/verification |
| **python-jose** | 3.3.0 | JWS, JWE, JWK (OIDC ready) |
| **authlib** | 1.3.0 | OAuth2 / OIDC flows |
| **pyopenssl** | 24.1.0 | SSL/TLS certificate handling |
| **certifi** | 2024.2.2 | Trusted CA bundle |
| **slowapi** | 0.1.9 | Redis-backed rate limiting |
| **bandit** | 1.7.8 | Security linting |
| **safety** | 3.2.0 | Dependency vulnerability scanning |
| **structlog** | 24.1.0 | Structured audit logging |

### Implemented
- ✅ Field-level encryption (cryptography.Fernet + PBKDF2)
- ✅ Audit logging (immutable chain hashing)
- ✅ Rate limiting (slowapi + Redis)
- ✅ Security headers (all major headers)
- ✅ Input sanitization (SQLi + XSS patterns)
- ✅ Output sanitization (credential redaction)
- ✅ Password hashing (argon2id - OWASP 2023 recommended)
- ✅ JWT handling (pyjwt + python-jose)
- ✅ Security middleware (FastAPI)
- ✅ Row-level security (PostgreSQL RLS)
- ✅ Data retention policies
- ✅ Secret manager abstraction (Vault/AWS/Azure ready)
- ✅ OAuth2 / OIDC ready (authlib)
- ✅ Security scanning (bandit + safety)
- ✅ Certificate handling (pyopenssl)

### Architecture
```
User (JWT + OAuth2) <-> Rate Limiting (slowapi) <-> Input Sanitization <-> 
FleetOps <-> Audit Log (immutable) <-> 
Encrypted DB (RLS + argon2) <-> 
Agent Communication (mTLS + cryptography)
```

## Key Features

### 1. Credential Encryption
All agent credentials encrypted at rest:
```python
# AES-256 via Fernet
encrypted = field_encryption.encrypt(api_key)
decrypted = field_encryption.decrypt(encrypted)
```

### 2. Immutable Audit Trail
```
Entry 1: hash=abc123, prev=000000
Entry 2: hash=def456, prev=abc123
Entry 3: hash=ghi789, prev=def456
...
(Tampering breaks the chain)
```

### 3. No Agent-to-Agent Communication
```
❌ AgentA -> AgentB (UNSAFE - not supported)
✅ AgentA -> FleetOps -> Human -> AgentB (SAFE)
```

### 4. Output Sanitization
Agent outputs automatically scrubbed:
- API keys (sk-...)
- Passwords
- Tokens
- Private keys
- Email addresses

## Configuration

### Required
```bash
FLEETOPS_MASTER_KEY=your-32-char-key-here-please
JWT_SECRET=another-32-char-secret-here
```

### Rate Limits
- Auth endpoints: 10 req/min
- API endpoints: 100 req/min  
- Public: 30 req/min

## Compliance
- GDPR/CCPA: Data export + right to deletion
- SOC 2: Audit trail + access controls
- HIPAA: Field encryption + audit logging (with proper configuration)

## Security Checklist
- [x] Field-level encryption
- [x] Audit logging
- [x] Rate limiting
- [x] Input/output sanitization
- [x] Security headers
- [x] CORS configuration
- [ ] 2FA implementation (ready, needs UI)
- [ ] mTLS (infrastructure-dependent)
- [ ] Secret manager integration (ready, needs config)

---

*See docs/SECURITY_DEEP_DIVE.md for full implementation details*
