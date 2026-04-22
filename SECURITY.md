# FleetOps Security

## Status: 🔒 Security Framework Implemented

### Implemented
- ✅ Field-level encryption for credentials (Fernet + PBKDF2)
- ✅ Audit logging (immutable chain hashing)
- ✅ Rate limiting (per-endpoint)
- ✅ Security headers (all major headers)
- ✅ Input sanitization (SQLi + XSS detection)
- ✅ Output sanitization (credential redaction)
- ✅ Security middleware (FastAPI)
- ✅ Row-level security (PostgreSQL RLS)
- ✅ Data retention policies
- ✅ Secret manager abstraction (Vault/AWS/Azure ready)
- ✅ Comprehensive security documentation

### Architecture
```
User (JWT + 2FA) <-> Rate Limiting <-> Input Sanitization <-> 
FleetOps <-> Audit Log (Immutable) <-> 
Encrypted DB (RLS) <-> 
Agent Communication (mTLS)
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
