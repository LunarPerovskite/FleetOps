# FleetOps Security Deep Dive

## Overview

FleetOps handles sensitive data: agent credentials, API keys, task outputs, and organizational data. This document covers the comprehensive security architecture.

---

## 🔐 1. Credential Storage & Encryption

### Current State (Needs Improvement)

Currently, credentials are stored in:
- `.env` files (plaintext)
- Database (JSON columns, not encrypted)
- Agent instance `credentials` column (JSON, not encrypted)

### Required Implementation

#### Field-Level Encryption

```python
# backend/app/core/encryption.py
"""Encryption utilities for sensitive data"""

import os
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
import base64

class FieldEncryption:
    """Encrypt/decrypt sensitive database fields"""
    
    def __init__(self):
        self.master_key = os.getenv("FLEETOPS_MASTER_KEY")
        if not self.master_key:
            raise ValueError("FLEETOPS_MASTER_KEY required")
        
        self.fernet = self._create_fernet()
    
    def _create_fernet(self) -> Fernet:
        """Create Fernet instance from master key"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=os.getenv("FLEETOPS_ENCRYPTION_SALT", "fleetops-salt").encode(),
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        return Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext"""
        if not plaintext:
            return ""
        return self.fernet.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt ciphertext"""
        if not ciphertext:
            return ""
        return self.fernet.decrypt(ciphertext.encode()).decode()

# Global instance
field_encryption = FieldEncryption()
```

#### Encrypted Model Fields

```python
# backend/app/models/agent_models.py
from sqlalchemy import Column, String, LargeBinary
from app.core.encryption import field_encryption

class AgentInstance(Base):
    # ... existing fields ...
    
    # Store encrypted credentials
    _credentials_encrypted = Column("credentials", LargeBinary, nullable=True)
    
    @property
    def credentials(self) -> Optional[Dict]:
        """Auto-decrypt on access"""
        if self._credentials_encrypted:
            decrypted = field_encryption.decrypt(
                self._credentials_encrypted.decode()
            )
            return json.loads(decrypted)
        return None
    
    @credentials.setter
    def credentials(self, value: Optional[Dict]):
        """Auto-encrypt on set"""
        if value:
            plaintext = json.dumps(value)
            self._credentials_encrypted = field_encryption.encrypt(
                plaintext
            ).encode()
        else:
            self._credentials_encrypted = None
```

#### Environment Variable Encryption

```python
# backend/app/core/config.py
class Settings(BaseSettings):
    # Encryption
    FLEETOPS_MASTER_KEY: str  # Required - 32+ chars
    FLEETOPS_ENCRYPTION_SALT: str = "fleetops-salt-change-me"
    
    # Agent credentials - stored encrypted in DB, never in .env
    # These are for system-level config only
    OPENCLAW_API_KEY: Optional[str] = None
    HERMES_API_KEY: Optional[str] = None
    GITHUB_TOKEN: Optional[str] = None
```

---

## 🌐 2. Agent Communication Security

### mTLS (Mutual TLS)

```python
# backend/app/adapters/base.py
import ssl
import httpx

class SecureHTTPClient:
    """HTTP client with mTLS support"""
    
    def __init__(self, base_url: str, cert_path: str = None, key_path: str = None):
        self.base_url = base_url
        
        # mTLS configuration
        if cert_path and key_path:
            self.ssl_context = ssl.create_default_context()
            self.ssl_context.load_cert_chain(cert_path, key_path)
            self.ssl_context.verify_mode = ssl.CERT_REQUIRED
        else:
            self.ssl_context = ssl.create_default_context()
    
    def create_client(self) -> httpx.AsyncClient:
        return httpx.AsyncClient(
            base_url=self.base_url,
            verify=self.ssl_context,
            http2=True,  # Enable HTTP/2 for efficiency
        )
```

### API Key Rotation

```python
# backend/app/services/api_key_service.py
from datetime import datetime, timedelta
import secrets

class APIKeyService:
    """Manage API keys with rotation"""
    
    async def create_key(self, org_id: str, name: str, 
                        expires_in_days: int = 90) -> Dict:
        """Create new API key with expiration"""
        key = f"fp_{secrets.token_urlsafe(32)}"
        
        # Store hashed version
        key_hash = hashlib.sha256(key.encode()).hexdigest()
        
        await db.execute("""
            INSERT INTO api_keys (org_id, name, key_hash, 
                                created_at, expires_at)
            VALUES ($1, $2, $3, $4, $5)
        """, org_id, name, key_hash, datetime.utcnow(),
            datetime.utcnow() + timedelta(days=expires_in_days))
        
        return {
            "key": key,  # Show ONCE to user
            "name": name,
            "expires_at": datetime.utcnow() + timedelta(days=expires_in_days)
        }
    
    async def rotate_key(self, key_id: str) -> Dict:
        """Rotate existing key"""
        # Create new key
        new_key = f"fp_{secrets.token_urlsafe(32)}"
        
        # Update database
        await db.execute("""
            UPDATE api_keys 
            SET key_hash = $1, 
                previous_key_hash = key_hash,
                rotated_at = $2,
                grace_period_until = $3
            WHERE id = $4
        """, hashlib.sha256(new_key.encode()).hexdigest(),
            datetime.utcnow(),
            datetime.utcnow() + timedelta(hours=24),  # 24h grace period
            key_id)
        
        return {"key": new_key}
```

---

## 🏛️ 3. Data Isolation (Multi-Tenant Security)

### Row-Level Security (RLS)

```sql
-- PostgreSQL Row-Level Security
-- Enable RLS on all tables
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;
ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;

-- Policy: Users can only see their org's data
CREATE POLICY org_isolation ON tasks
    USING (org_id = current_setting('app.current_org_id')::UUID);

-- Set org ID per request
SET app.current_org_id = 'user-org-id';
```

### Organization Scoping in Code

```python
# backend/app/core/auth.py
async def get_current_user_org(request: Request) -> str:
    """Extract org ID from JWT and set in DB context"""
    token = extract_token(request)
    payload = jwt.decode(token, SECRET_KEY)
    org_id = payload["org_id"]
    
    # Set for RLS
    await db.execute("SET app.current_org_id = :org_id", {"org_id": org_id})
    
    return org_id
```

### Database Per Tenant (Optional)

```yaml
# For highest isolation
# Each organization gets own database
tenants:
  org_1:
    database: fleetops_org_1
  org_2:
    database: fleetops_org_2
```

---

## 📝 4. Audit Logging

### Comprehensive Audit Trail

```python
# backend/app/core/audit.py
import logging
from datetime import datetime

class AuditLogger:
    """Log all security-relevant events"""
    
    def __init__(self):
        self.logger = logging.getLogger("fleetops.audit")
    
    async def log(self, event_type: str, details: Dict, 
                  user_id: str, org_id: str, ip_address: str):
        """Log security event"""
        
        audit_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type,
            "user_id": user_id,
            "org_id": org_id,
            "ip_address": ip_address,
            "details": details,
            "severity": self._calculate_severity(event_type)
        }
        
        # Write to tamper-proof log store
        await self._write_to_audit_db(audit_entry)
        
        # Alert on high severity
        if audit_entry["severity"] == "high":
            await self._send_security_alert(audit_entry)
    
    def _calculate_severity(self, event_type: str) -> str:
        """Calculate event severity"""
        high_severity = [
            "agent_credentials_accessed",
            "failed_login_attempt",
            "unauthorized_access",
            "agent_executed_without_approval",
            "data_exported",
            "admin_action"
        ]
        
        return "high" if event_type in high_severity else "medium"

# Usage
audit_logger = AuditLogger()

# In agent execution:
audit_logger.log(
    event_type="agent_execution_started",
    details={"agent_type": "openclaw", "task_id": task_id},
    user_id=current_user.id,
    org_id=current_user.org_id,
    ip_address=request.client.host
)
```

### Immutable Audit Storage

```python
# Store in append-only table with cryptographic hashing
class ImmutableAuditLog(Base):
    __tablename__ = "immutable_audit_log"
    
    id = Column(String, primary_key=True)
    timestamp = Column(DateTime, default=datetime.utcnow)
    event_type = Column(String)
    user_id = Column(String)
    org_id = Column(String)
    details = Column(JSON)
    previous_hash = Column(String)  # Chain hashing
    current_hash = Column(String)  # SHA-256 of all fields
```

---

## 🔑 5. Secret Management

### Integration with Secret Managers

```python
# backend/app/core/secrets.py
import os
from typing import Optional

class SecretManager:
    """Abstract secret management"""
    
    def __init__(self):
        self.backend = os.getenv("SECRET_BACKEND", "env")  # env, vault, aws, azure
    
    async def get_secret(self, key: str) -> Optional[str]:
        """Get secret from configured backend"""
        if self.backend == "vault":
            return await self._get_from_hashicorp_vault(key)
        elif self.backend == "aws":
            return await self._get_from_aws_secrets_manager(key)
        elif self.backend == "azure":
            return await self._get_from_azure_keyvault(key)
        else:
            return os.getenv(key)
    
    async def _get_from_hashicorp_vault(self, key: str) -> str:
        """Retrieve from HashiCorp Vault"""
        import hvac
        client = hvac.Client(url=os.getenv("VAULT_ADDR"))
        client.token = os.getenv("VAULT_TOKEN")
        
        secret = client.secrets.kv.v2.read_secret_version(
            path=f"fleetops/{key}"
        )
        return secret["data"]["data"]["value"]
    
    async def _get_from_aws_secrets_manager(self, key: str) -> str:
        """Retrieve from AWS Secrets Manager"""
        import boto3
        client = boto3.client('secretsmanager')
        
        response = client.get_secret_value(SecretId=f"fleetops/{key}")
        return response["SecretString"]

secret_manager = SecretManager()
```

### Never Store in Code

```python
# ❌ BAD - Never do this
API_KEY = "sk-abc123xyz"

# ✅ GOOD - Always use secret manager
API_KEY = await secret_manager.get_secret("OPENAI_API_KEY")
```

---

## 🛡️ 6. Network Security

### Firewall Rules

```bash
# UFW / iptables rules for FleetOps
# Only allow necessary ports

# FleetOps web (HTTPS only)
ufw allow 443/tcp

# Internal agent communication (VPN/VPC only)
ufw allow from 10.0.0.0/8 to any port 8080  # OpenClaw
ufw allow from 10.0.0.0/8 to any port 8001  # CrewAI
ufw allow from 10.0.0.0/8 to any port 11434 # Ollama

# Block external access to agents
ufw deny 8080/tcp  # Block external OpenClaw
ufw deny 8001/tcp  # Block external CrewAI
```

### VPN Requirements for Remote Agents

```yaml
# docker-compose.yml with VPN
services:
  fleetops:
    networks:
      - fleetops-internal
      - vpn-network  # For remote agents
  
  openclaw:
    networks:
      - fleetops-internal
    # Only accessible via VPN
```

---

## 🧹 7. Data Retention & Privacy

### Automatic Data Purging

```python
# backend/app/services/data_retention.py
from datetime import datetime, timedelta

class DataRetentionService:
    """Manage data lifecycle for privacy"""
    
    async def purge_old_data(self, org_id: str):
        """Purge data according to retention policy"""
        
        # Get retention settings
        retention_days = await self.get_org_retention_policy(org_id)
        cutoff = datetime.utcnow() - timedelta(days=retention_days)
        
        # Anonymize old execution logs
        await db.execute("""
            UPDATE agent_execution_logs
            SET 
                output = '[REDACTED - retention policy]',
                error = NULL,
                execution_log = NULL
            WHERE org_id = :org_id AND started_at < :cutoff
        """, {"org_id": org_id, "cutoff": cutoff})
        
        # Delete old events
        await db.execute("""
            DELETE FROM events
            WHERE org_id = :org_id AND created_at < :cutoff
        """, {"org_id": org_id, "cutoff": cutoff})
    
    async def export_user_data(self, user_id: str) -> Dict:
        """GDPR/CCPA: Export all user data"""
        # ... gather all data ...
        return user_data
    
    async def delete_user_data(self, user_id: str):
        """GDPR: Right to be forgotten"""
        # ... delete all user data ...
        pass
```

---

## 🔒 8. Agent Communication Security

### No Direct Agent-to-Agent Communication

```
❌ Agents talking directly:  AgentA -> AgentB (UNSAFE)
✅ Through FleetOps:        AgentA -> FleetOps -> Human -> AgentB (SAFE)
```

### Agent Output Sanitization

```python
# backend/app/services/sanitization.py
import re

class OutputSanitizer:
    """Sanitize agent outputs before storage/display"""
    
    PATTERNS = {
        "api_key": r"sk-[a-zA-Z0-9]{48}",
        "password": r"password[:\s]*[^\s]+",
        "token": r"token[:\s]*[^\s]+",
        "private_key": r"-----BEGIN .* PRIVATE KEY-----",
        "email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}",
    }
    
    def sanitize(self, text: str) -> str:
        """Remove sensitive data from agent output"""
        for pattern_name, pattern in self.PATTERNS.items():
            text = re.sub(pattern, f"[REDACTED_{pattern_name.upper()}]", text)
        return text

sanitizer = OutputSanitizer()
```

---

## 🚨 9. Security Checklist

### Before Production

- [ ] Enable field-level encryption for credentials
- [ ] Configure mTLS for agent communication
- [ ] Enable Row-Level Security (RLS) in PostgreSQL
- [ ] Set up immutable audit logging
- [ ] Configure secret manager (Vault/AWS/Azure)
- [ ] Enable API key rotation
- [ ] Set up firewall rules
- [ ] Configure VPN for remote agents
- [ ] Implement data retention policies
- [ ] Add output sanitization
- [ ] Enable rate limiting
- [ ] Configure CORS properly
- [ ] Set up security alerts
- [ ] Implement backup encryption
- [ ] Enable 2FA for admin access

---

## 📋 10. Security Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                        USER LAYER                           │
│  - JWT Authentication                                       │
│  - Role-based access control (RBAC)                        │
│  - 2FA for admins                                          │
└─────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                       FLEETOPS LAYER                        │
│  - API rate limiting                                        │
│  - Input validation                                         │
│  - Request sanitization                                     │
│  - CORS configuration                                       │
└─────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                      ORCHESTRATION LAYER                    │
│  - Agent output sanitization                                │
│  - Human approval gates                                     │
│  - Audit logging (immutable)                                │
│  - No direct agent-to-agent comms                           │
└─────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                       DATABASE LAYER                        │
│  - Row-level security (RLS)                               │
│  - Field-level encryption (credentials)                     │
│  - Encrypted backups                                        │
│  - Data retention policies                                  │
└─────────────────────────────────────────────────────────────┘
                           │
┌─────────────────────────────────────────────────────────────┐
│                      AGENT LAYER                            │
│  - mTLS communication                                       │
│  - API key rotation                                         │
│  - Secret manager integration                               │
│  - VPN for remote agents                                    │
└─────────────────────────────────────────────────────────────┘
```

---

*Security is not a feature, it's a foundation.*
