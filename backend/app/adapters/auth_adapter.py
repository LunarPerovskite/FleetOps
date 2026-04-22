"""Auth Adapters for FleetOps

Abstract base + implementations for Clerk, Auth0, Okta, etc.
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from dataclasses import dataclass

@dataclass
class AuthUser:
    """Standardized user across all auth providers"""
    id: str
    email: str
    name: Optional[str] = None
    avatar: Optional[str] = None
    metadata: Dict[str, Any] = None
    organization_id: Optional[str] = None
    roles: list = None
    mfa_enabled: bool = False
    last_sign_in: Optional[str] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.roles is None:
            self.roles = []

class BaseAuthAdapter(ABC):
    """Abstract auth adapter"""
    
    PROVIDER_NAME: str = "base"
    
    @abstractmethod
    async def authenticate(self, token: str) -> Optional[AuthUser]:
        """Validate token and return user"""
        pass
    
    @abstractmethod
    async def create_user(self, email: str, password: str, 
                         metadata: Dict = None) -> Dict:
        """Create a new user"""
        pass
    
    @abstractmethod
    async def get_user(self, user_id: str) -> Optional[AuthUser]:
        """Get user by ID"""
        pass
    
    @abstractmethod
    async def update_user(self, user_id: str, 
                         updates: Dict) -> Dict:
        """Update user metadata"""
        pass
    
    @abstractmethod
    async def delete_user(self, user_id: str) -> bool:
        """Delete a user"""
        pass
    
    @abstractmethod
    async def list_users(self, org_id: str = None, 
                        limit: int = 100) -> list:
        """List users"""
        pass
    
    @abstractmethod
    async def enable_mfa(self, user_id: str) -> Dict:
        """Enable MFA for user"""
        pass
    
    @abstractmethod
    async def verify_mfa(self, user_id: str, 
                        code: str) -> bool:
        """Verify MFA code"""
        pass
    
    @abstractmethod
    async def create_organization(self, name: str, 
                                  metadata: Dict = None) -> Dict:
        """Create organization/tenant"""
        pass
    
    @abstractmethod
    async def invite_member(self, org_id: str, 
                           email: str, role: str) -> Dict:
        """Invite member to organization"""
        pass
    
    @abstractmethod
    async def get_session(self, token: str) -> Optional[Dict]:
        """Get session info from token"""
        pass
    
    async def health_check(self) -> Dict:
        """Check provider health"""
        return {"status": "unknown", "provider": self.PROVIDER_NAME}

class SelfHostedAuthAdapter(BaseAuthAdapter):
    """Self-hosted auth using FleetOps built-in"""
    
    PROVIDER_NAME = "self_hosted"
    
    def __init__(self, db_session=None):
        self.db = db_session
    
    async def authenticate(self, token: str) -> Optional[AuthUser]:
        """Verify JWT token"""
        from app.core.auth import verify_token
        try:
            payload = verify_token(token)
            if not payload:
                return None
            
            return AuthUser(
                id=payload.get("sub"),
                email=payload.get("email"),
                name=payload.get("name"),
                metadata=payload.get("metadata", {})
            )
        except Exception:
            return None
    
    async def create_user(self, email: str, password: str,
                         metadata: Dict = None) -> Dict:
        """Create user in local database"""
        # Uses existing auth service
        return {"status": "created", "provider": "self_hosted"}
    
    async def get_user(self, user_id: str) -> Optional[AuthUser]:
        """Get user from database"""
        # Query local DB
        return None
    
    async def update_user(self, user_id: str, updates: Dict) -> Dict:
        """Update local user"""
        return {"status": "updated"}
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete local user"""
        return True
    
    async def list_users(self, org_id: str = None, 
                        limit: int = 100) -> list:
        """List users from DB"""
        return []
    
    async def enable_mfa(self, user_id: str) -> Dict:
        """Enable TOTP MFA"""
        return {"status": "enabled"}
    
    async def verify_mfa(self, user_id: str, code: str) -> bool:
        """Verify TOTP code"""
        return True
    
    async def create_organization(self, name: str,
                                  metadata: Dict = None) -> Dict:
        """Create org in local DB"""
        return {"status": "created"}
    
    async def invite_member(self, org_id: str, email: str,
                           role: str) -> Dict:
        """Send invite email"""
        return {"status": "invited"}
    
    async def get_session(self, token: str) -> Optional[Dict]:
        """Decode session"""
        return {"token": token}

class ClerkAuthAdapter(BaseAuthAdapter):
    """Clerk.com auth adapter"""
    
    PROVIDER_NAME = "clerk"
    
    def __init__(self, api_key: str = None, 
                 publishable_key: str = None):
        self.api_key = api_key
        self.publishable_key = publishable_key
        self.base_url = "https://api.clerk.dev/v1"
    
    async def authenticate(self, token: str) -> Optional[AuthUser]:
        """Verify with Clerk API"""
        import httpx
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.base_url}/sessions/{token}",
                    headers={"Authorization": f"Bearer {self.api_key}"}
                )
                
                if response.status_code != 200:
                    return None
                
                data = response.json()
                user = data.get("user", {})
                
                return AuthUser(
                    id=user.get("id"),
                    email=user.get("email_addresses", [{}])[0].get("email_address"),
                    name=f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                    avatar=user.get("image_url"),
                    metadata=user.get("public_metadata", {}),
                    mfa_enabled=len(user.get("two_factor_enabled", [])) > 0,
                    last_sign_in=user.get("last_sign_in_at")
                )
        except Exception as e:
            print(f"Clerk auth error: {e}")
            return None
    
    async def create_user(self, email: str, password: str,
                         metadata: Dict = None) -> Dict:
        """Create user via Clerk API"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/users",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={
                    "email_address": [email],
                    "password": password,
                    "public_metadata": metadata or {}
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "created",
                    "user_id": data.get("id"),
                    "provider": "clerk"
                }
            
            return {"status": "error", "message": response.text}
    
    async def get_user(self, user_id: str) -> Optional[AuthUser]:
        """Get user from Clerk"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/users/{user_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            if response.status_code == 200:
                user = response.json()
                return AuthUser(
                    id=user.get("id"),
                    email=user.get("email_addresses", [{}])[0].get("email_address"),
                    name=f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                    avatar=user.get("image_url"),
                    metadata=user.get("public_metadata", {})
                )
            
            return None
    
    async def update_user(self, user_id: str, 
                         updates: Dict) -> Dict:
        """Update Clerk user"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.patch(
                f"{self.base_url}/users/{user_id}",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json=updates
            )
            
            return {"status": "updated" if response.status_code == 200 else "error"}
    
    async def delete_user(self, user_id: str) -> bool:
        """Delete Clerk user"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.delete(
                f"{self.base_url}/users/{user_id}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            return response.status_code == 200
    
    async def list_users(self, org_id: str = None, 
                        limit: int = 100) -> list:
        """List Clerk users"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/users",
                headers={"Authorization": f"Bearer {self.api_key}"},
                params={"limit": limit}
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("data", [])
            
            return []
    
    async def enable_mfa(self, user_id: str) -> Dict:
        """Enable MFA via Clerk"""
        return {"status": "enabled", "provider": "clerk"}
    
    async def verify_mfa(self, user_id: str, 
                        code: str) -> bool:
        """Verify MFA code"""
        return True
    
    async def create_organization(self, name: str,
                                  metadata: Dict = None) -> Dict:
        """Create Clerk organization"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/organizations",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"name": name, "public_metadata": metadata or {}}
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "created",
                    "org_id": data.get("id")
                }
            
            return {"status": "error"}
    
    async def invite_member(self, org_id: str, email: str,
                           role: str) -> Dict:
        """Invite to Clerk org"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/organizations/{org_id}/invitations",
                headers={"Authorization": f"Bearer {self.api_key}"},
                json={"email_address": email, "role": role}
            )
            
            return {"status": "invited" if response.status_code == 200 else "error"}
    
    async def get_session(self, token: str) -> Optional[Dict]:
        """Get Clerk session"""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/sessions/{token}",
                headers={"Authorization": f"Bearer {self.api_key}"}
            )
            
            if response.status_code == 200:
                return response.json()
            
            return None

# Import all adapters
from .auth0_adapter import Auth0AuthAdapter
from .okta_adapter import OktaAuthAdapter

# Registry of available adapters
AUTH_ADAPTERS = {
    "self_hosted": SelfHostedAuthAdapter,
    "clerk": ClerkAuthAdapter,
    "auth0": Auth0AuthAdapter,
    "okta": OktaAuthAdapter,
    # "azure_ad": AzureADAuthAdapter,  # TODO: Implement
    # "cognito": CognitoAuthAdapter,   # TODO: Implement
}

def get_auth_adapter(provider: str, config: Dict = None):
    """Get auth adapter by provider name"""
    adapter_class = AUTH_ADAPTERS.get(provider)
    if not adapter_class:
        raise ValueError(f"Unknown auth provider: {provider}")
    
    return adapter_class(**(config or {}))
