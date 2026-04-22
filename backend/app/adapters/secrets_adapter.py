"""Secrets Management Adapters for FleetOps

Doppler, HashiCorp Vault, AWS Secrets Manager
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional
import os

class BaseSecretsAdapter(ABC):
    """Abstract secrets adapter"""
    
    PROVIDER_NAME: str = "base"
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
    
    @abstractmethod
    async def get_secret(self, key: str) -> Optional[str]:
        """Get secret value"""
        pass
    
    @abstractmethod
    async def set_secret(self, key: str, value: str) -> bool:
        """Set secret value"""
        pass
    
    @abstractmethod
    async def delete_secret(self, key: str) -> bool:
        """Delete secret"""
        pass
    
    @abstractmethod
    async def list_secrets(self, prefix: str = None) -> list:
        """List secrets"""
        pass

class DopplerAdapter(BaseSecretsAdapter):
    """Doppler secrets adapter"""
    
    PROVIDER_NAME = "doppler"
    
    def __init__(self, token: str = None, project: str = None, 
                 config: str = "dev"):
        super().__init__()
        self.token = token
        self.project = project
        self.config = config
        self.base_url = "https://api.doppler.com/v3"
    
    async def get_secret(self, key: str) -> Optional[str]:
        """Get secret from Doppler"""
        import requests
        
        try:
            response = requests.get(
                f"{self.base_url}/configs/config/secret",
                headers={"Authorization": f"Bearer {self.token}"},
                params={
                    "project": self.project,
                    "config": self.config,
                    "name": key
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("value", {}).get("raw")
            
            return None
        except Exception:
            return None
    
    async def set_secret(self, key: str, value: str) -> bool:
        """Set secret in Doppler"""
        import requests
        
        try:
            response = requests.post(
                f"{self.base_url}/configs/config/secrets",
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Content-Type": "application/json"
                },
                json={
                    "project": self.project,
                    "config": self.config,
                    "secrets": {key: {"raw": value}}
                }
            )
            
            return response.status_code == 200
        except Exception:
            return False
    
    async def delete_secret(self, key: str) -> bool:
        """Delete secret from Doppler"""
        import requests
        
        try:
            response = requests.delete(
                f"{self.base_url}/configs/config/secret",
                headers={"Authorization": f"Bearer {self.token}"},
                params={
                    "project": self.project,
                    "config": self.config,
                    "name": key
                }
            )
            
            return response.status_code == 200
        except Exception:
            return False
    
    async def list_secrets(self, prefix: str = None) -> list:
        """List secrets from Doppler"""
        import requests
        
        try:
            response = requests.get(
                f"{self.base_url}/configs/config/secrets",
                headers={"Authorization": f"Bearer {self.token}"},
                params={
                    "project": self.project,
                    "config": self.config
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                secrets = list(data.get("secrets", {}).keys())
                if prefix:
                    secrets = [s for s in secrets if s.startswith(prefix)]
                return secrets
            
            return []
        except Exception:
            return []

class VaultAdapter(BaseSecretsAdapter):
    """HashiCorp Vault adapter"""
    
    PROVIDER_NAME = "vault"
    
    def __init__(self, url: str = None, token: str = None,
                 mount_point: str = "secret"):
        super().__init__()
        self.url = url
        self.token = token
        self.mount_point = mount_point
    
    async def get_secret(self, key: str) -> Optional[str]:
        """Get secret from Vault"""
        import requests
        
        try:
            response = requests.get(
                f"{self.url}/v1/{self.mount_point}/data/{key}",
                headers={"X-Vault-Token": self.token}
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("data", {}).get("value")
            
            return None
        except Exception:
            return None
    
    async def set_secret(self, key: str, value: str) -> bool:
        """Set secret in Vault"""
        import requests
        
        try:
            response = requests.post(
                f"{self.url}/v1/{self.mount_point}/data/{key}",
                headers={
                    "X-Vault-Token": self.token,
                    "Content-Type": "application/json"
                },
                json={"data": {"value": value}}
            )
            
            return response.status_code == 200
        except Exception:
            return False
    
    async def delete_secret(self, key: str) -> bool:
        """Delete secret from Vault"""
        import requests
        
        try:
            response = requests.delete(
                f"{self.url}/v1/{self.mount_point}/data/{key}",
                headers={"X-Vault-Token": self.token}
            )
            
            return response.status_code == 204
        except Exception:
            return False
    
    async def list_secrets(self, prefix: str = None) -> list:
        """List secrets from Vault"""
        import requests
        
        try:
            response = requests.get(
                f"{self.url}/v1/{self.mount_point}/metadata/{prefix or ''}",
                headers={"X-Vault-Token": self.token}
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("data", {}).get("keys", [])
            
            return []
        except Exception:
            return []

class EnvAdapter(BaseSecretsAdapter):
    """Environment variables adapter (default for dev)"""
    
    PROVIDER_NAME = "env"
    
    async def get_secret(self, key: str) -> Optional[str]:
        """Get from environment"""
        return os.getenv(key)
    
    async def set_secret(self, key: str, value: str) -> bool:
        """Set environment variable"""
        os.environ[key] = value
        return True
    
    async def delete_secret(self, key: str) -> bool:
        """Delete environment variable"""
        if key in os.environ:
            del os.environ[key]
            return True
        return False
    
    async def list_secrets(self, prefix: str = None) -> list:
        """List environment variables"""
        keys = list(os.environ.keys())
        if prefix:
            keys = [k for k in keys if k.startswith(prefix)]
        return keys

# Registry
SECRETS_ADAPTERS = {
    "doppler": DopplerAdapter,
    "vault": VaultAdapter,
    "env": EnvAdapter,
    "aws_secrets": VaultAdapter,  # TODO: Implement AWS Secrets Manager
    "azure_keyvault": VaultAdapter  # TODO: Implement Azure KeyVault
}

def get_secrets_adapter(provider: str, config: Dict = None):
    """Get secrets adapter"""
    adapter_class = SECRETS_ADAPTERS.get(provider)
    if not adapter_class:
        raise ValueError(f"Unknown secrets provider: {provider}")
    
    return adapter_class(config)
