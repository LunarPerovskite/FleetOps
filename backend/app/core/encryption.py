"""Encryption utilities for FleetOps

Field-level encryption for sensitive data:
- Agent credentials
- API keys
- Personal data

Uses Fernet (symmetric encryption) with PBKDF2 key derivation.
"""

import os
import json
import hashlib
import base64
from typing import Optional, Dict, Any
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

class FieldEncryption:
    """Encrypt/decrypt sensitive database fields"""
    
    def __init__(self):
        self.master_key = os.getenv("FLEETOPS_MASTER_KEY")
        self.salt = os.getenv("FLEETOPS_ENCRYPTION_SALT", "").encode()
        
        # Validate in production
        if os.getenv("ENV", "development").lower() == "production":
            if not self.master_key or len(self.master_key) < 32:
                raise RuntimeError(
                    "FLEETOPS_MASTER_KEY must be set and at least 32 characters in production"
                )
            if not self.salt:
                raise RuntimeError(
                    "FLEETOPS_ENCRYPTION_SALT must be set in production"
                )
        
        # Development fallbacks with warnings
        if not self.master_key:
            import warnings
            warnings.warn(
                "FLEETOPS_MASTER_KEY not set. Using development-only encryption.",
                RuntimeWarning
            )
            self.master_key = os.urandom(32).hex()
        
        if not self.salt:
            import warnings
            warnings.warn(
                "FLEETOPS_ENCRYPTION_SALT not set. Generating random salt.",
                RuntimeWarning
            )
            self.salt = os.urandom(16)
        
        self.fernet = self._create_fernet()
    
    def _create_fernet(self) -> Fernet:
        """Create Fernet instance from master key"""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=self.salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(self.master_key.encode()))
        return Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt plaintext string"""
        if not plaintext:
            return ""
        try:
            return self.fernet.encrypt(plaintext.encode()).decode()
        except Exception as e:
            raise ValueError(f"Encryption failed: {e}")
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt ciphertext string"""
        if not ciphertext:
            return ""
        try:
            return self.fernet.decrypt(ciphertext.encode()).decode()
        except Exception as e:
            raise ValueError(f"Decryption failed: {e}")
    
    def encrypt_dict(self, data: Dict[str, Any]) -> str:
        """Encrypt a dictionary"""
        plaintext = json.dumps(data)
        return self.encrypt(plaintext)
    
    def decrypt_dict(self, ciphertext: str) -> Dict[str, Any]:
        """Decrypt to dictionary"""
        plaintext = self.decrypt(ciphertext)
        return json.loads(plaintext)
    
    def hash_identifier(self, identifier: str) -> str:
        """Create a one-way hash for searching without decryption"""
        return hashlib.sha256(f"{identifier}{self.salt}".encode()).hexdigest()

# Global instance
field_encryption = FieldEncryption()


def get_master_key_status() -> Dict[str, Any]:
    """Check if encryption is properly configured"""
    key = os.getenv("FLEETOPS_MASTER_KEY", "")
    
    return {
        "configured": bool(key) and len(key) >= 32,
        "length": len(key),
        "strength": "strong" if len(key) >= 32 else "weak" if len(key) > 0 else "not-set",
        "salt_configured": os.getenv("FLEETOPS_ENCRYPTION_SALT") is not None
    }
