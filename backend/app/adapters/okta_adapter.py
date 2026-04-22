"""Okta Auth Adapter for FleetOps"""

from typing import Dict, Optional
from auth_adapter import BaseAuthAdapter, AuthUser

class OktaAuthAdapter(BaseAuthAdapter):
    """Okta.com auth adapter for enterprises"""
    
    PROVIDER_NAME = "okta"
    
    def __init__(self, domain: str = None, api_token: str = None):
        self.domain = domain
        self.api_token = api_token
        self.base_url = f"https://{domain}/api/v1" if domain else None
    
    async def authenticate(self, token: str) -> Optional[AuthUser]:
        """Verify token with Okta"""
        import requests
        
        try:
            response = requests.get(
                f"{self.base_url}/users/me",
                headers={"Authorization": f"SSWS {token}"}
            )
            
            if response.status_code != 200:
                return None
            
            user = response.json()
            
            return AuthUser(
                id=user.get("id"),
                email=user.get("profile", {}).get("email"),
                name=f"{user.get('profile', {}).get('firstName', '')} {user.get('profile', {}).get('lastName', '')}".strip(),
                metadata=user.get("profile", {}),
                mfa_enabled=user.get("_links", {}).get("factorTypes") is not None
            )
        except Exception as e:
            print(f"Okta auth error: {e}")
            return None
    
    async def create_user(self, email: str, password: str,
                         metadata: Dict = None) -> Dict:
        """Create Okta user"""
        import requests
        
        try:
            response = requests.post(
                f"{self.base_url}/users",
                headers={
                    "Authorization": f"SSWS {self.api_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "profile": {
                        "firstName": metadata.get("first_name", "User"),
                        "lastName": metadata.get("last_name", ""),
                        "email": email,
                        "login": email
                    },
                    "credentials": {
                        "password": {"value": password}
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "created",
                    "user_id": data.get("id"),
                    "provider": "okta"
                }
            
            return {"status": "error", "message": response.text}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def get_user(self, user_id: str) -> Optional[AuthUser]:
        """Get Okta user"""
        import requests
        
        try:
            response = requests.get(
                f"{self.base_url}/users/{user_id}",
                headers={"Authorization": f"SSWS {self.api_token}"}
            )
            
            if response.status_code == 200:
                user = response.json()
                return AuthUser(
                    id=user.get("id"),
                    email=user.get("profile", {}).get("email"),
                    name=f"{user.get('profile', {}).get('firstName', '')} {user.get('profile', {}).get('lastName', '')}".strip(),
                    metadata=user.get("profile", {})
                )
            
            return None
        except Exception:
            return None
    
    async def update_user(self, user_id: str, 
                         updates: Dict) -> Dict:
        """Update Okta user"""
        import requests
        
        try:
            response = requests.post(
                f"{self.base_url}/users/{user_id}",
                headers={
                    "Authorization": f"SSWS {self.api_token}",
                    "Content-Type": "application/json"
                },
                json={"profile": updates}
            )
            
            return {"status": "updated" if response.status_code == 200 else "error"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
    
    async def delete_user(self, user_id: str) -> bool:
        """Deactivate Okta user"""
        import requests
        
        try:
            response = requests.delete(
                f"{self.base_url}/users/{user_id}",
                headers={"Authorization": f"SSWS {self.api_token}"}
            )
            
            return response.status_code == 200
        except Exception:
            return False
    
    async def list_users(self, org_id: str = None, 
                        limit: int = 100) -> list:
        """List Okta users"""
        import requests
        
        try:
            response = requests.get(
                f"{self.base_url}/users",
                headers={"Authorization": f"SSWS {self.api_token}"},
                params={"limit": limit}
            )
            
            if response.status_code == 200:
                return response.json()
            
            return []
        except Exception:
            return []
    
    async def enable_mfa(self, user_id: str) -> Dict:
        """Enroll MFA factor for Okta user"""
        import requests
        
        try:
            response = requests.post(
                f"{self.base_url}/users/{user_id}/factors",
                headers={
                    "Authorization": f"SSWS {self.api_token}",
                    "Content-Type": "application/json"
                },
                json={"factorType": "token:software:totp", "provider": "GOOGLE"}
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "enrolled",
                    "qr_code": data.get("_embedded", {}).get("activation", {}).get("_links", {}).get("qrcode", {}).get("href")
                }
            
            return {"status": "error"}
        except Exception:
            return {"status": "error"}
    
    async def verify_mfa(self, user_id: str, 
                        code: str) -> bool:
        """Verify MFA factor"""
        import requests
        
        try:
            # Get user's factors
            response = requests.get(
                f"{self.base_url}/users/{user_id}/factors",
                headers={"Authorization": f"SSWS {self.api_token}"}
            )
            
            if response.status_code == 200:
                factors = response.json()
                for factor in factors:
                    if factor.get("factorType") == "token:software:totp":
                        # Verify
                        verify_response = requests.post(
                            f"{self.base_url}/users/{user_id}/factors/{factor['id']}/verify",
                            headers={
                                "Authorization": f"SSWS {self.api_token}",
                                "Content-Type": "application/json"
                            },
                            json={"passCode": code}
                        )
                        return verify_response.status_code == 200
            
            return False
        except Exception:
            return False
    
    async def create_organization(self, name: str,
                                  metadata: Dict = None) -> Dict:
        """Create Okta group (used as org)"""
        import requests
        
        try:
            response = requests.post(
                f"{self.base_url}/groups",
                headers={
                    "Authorization": f"SSWS {self.api_token}",
                    "Content-Type": "application/json"
                },
                json={
                    "profile": {
                        "name": name,
                        "description": metadata.get("description", "")
                    }
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                return {"status": "created", "org_id": data.get("id")}
            
            return {"status": "error"}
        except Exception:
            return {"status": "error"}
    
    async def invite_member(self, org_id: str, email: str,
                           role: str) -> Dict:
        """Add user to Okta group"""
        import requests
        
        try:
            # Find user by email
            user_response = requests.get(
                f"{self.base_url}/users/{email}",
                headers={"Authorization": f"SSWS {self.api_token}"}
            )
            
            if user_response.status_code == 200:
                user_id = user_response.json().get("id")
                
                response = requests.put(
                    f"{self.base_url}/groups/{org_id}/users/{user_id}",
                    headers={"Authorization": f"SSWS {self.api_token}"}
                )
                
                return {"status": "added" if response.status_code == 204 else "error"}
            
            return {"status": "user_not_found"}
        except Exception:
            return {"status": "error"}
    
    async def get_session(self, token: str) -> Optional[Dict]:
        """Get Okta session"""
        import requests
        
        try:
            response = requests.get(
                f"{self.base_url}/sessions/{token}",
                headers={"Authorization": f"SSWS {self.api_token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            
            return None
        except Exception:
            return None
