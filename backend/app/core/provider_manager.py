"""Provider Manager - Unified interface for all adapters

Organizations configure once, use everywhere
"""

from typing import Dict, Optional, Any
from datetime import datetime

from app.core.provider_registry import ProviderConfig, provider_registry
from app.adapters.auth_adapter import get_auth_adapter, AuthUser
from app.adapters.db_adapter import get_db_adapter
from app.adapters.monitoring_adapter import get_monitoring_adapter
from app.adapters.secrets_adapter import get_secrets_adapter

class ProviderManager:
    """Manages all provider adapters for an organization"""
    
    def __init__(self, org_id: str, config: ProviderConfig = None):
        self.org_id = org_id
        self.config = config or ProviderConfig()
        
        # Lazy-loaded adapters
        self._auth = None
        self._db = None
        self._monitoring = None
        self._secrets = None
    
    @property
    def auth(self):
        """Get auth adapter"""
        if not self._auth:
            self._auth = get_auth_adapter(
                self.config.auth.value,
                self.config.auth_config
            )
        return self._auth
    
    @property
    def db(self):
        """Get database adapter"""
        if not self._db:
            self._db = get_db_adapter(
                self.config.database.value,
                self.config.db_config.get("connection_string"),
                self.config.db_config
            )
        return self._db
    
    @property
    def monitoring(self):
        """Get monitoring adapter"""
        if not self._monitoring:
            self._monitoring = get_monitoring_adapter(
                self.config.monitoring.value,
                self.config.monitoring_config
            )
        return self._monitoring
    
    @property
    def secrets(self):
        """Get secrets adapter"""
        if not self._secrets:
            self._secrets = get_secrets_adapter(
                self.config.secrets.value,
                self.config.secrets_config
            )
        return self._secrets
    
    async def authenticate(self, token: str) -> Optional[AuthUser]:
        """Authenticate user via configured provider"""
        return await self.auth.authenticate(token)
    
    async def health_check(self) -> Dict:
        """Check health of all providers"""
        return {
            "org_id": self.org_id,
            "timestamp": datetime.utcnow().isoformat(),
            "providers": {
                "auth": {
                    "provider": self.config.auth.value,
                    "status": "unknown"  # Would call adapter health_check
                },
                "database": {
                    "provider": self.config.database.value,
                    "status": "unknown"
                },
                "monitoring": {
                    "provider": self.config.monitoring.value,
                    "status": "unknown"
                },
                "secrets": {
                    "provider": self.config.secrets.value,
                    "status": "unknown"
                }
            }
        }
    
    def get_provider_info(self) -> Dict:
        """Get information about configured providers"""
        return {
            "org_id": self.org_id,
            "auth": {
                "provider": self.config.auth.value,
                "config": {k: "***" if "secret" in k.lower() or "key" in k.lower() else v 
                          for k, v in self.config.auth_config.items()}
            },
            "database": {
                "provider": self.config.database.value,
                "config": {k: "***" if "password" in k.lower() else v
                          for k, v in self.config.db_config.items()}
            },
            "monitoring": {
                "provider": self.config.monitoring.value
            },
            "secrets": {
                "provider": self.config.secrets.value
            }
        }

# Global provider managers by org
_provider_managers: Dict[str, ProviderManager] = {}

def get_provider_manager(org_id: str, config: ProviderConfig = None) -> ProviderManager:
    """Get or create provider manager for org"""
    if org_id not in _provider_managers:
        _provider_managers[org_id] = ProviderManager(org_id, config)
    return _provider_managers[org_id]
