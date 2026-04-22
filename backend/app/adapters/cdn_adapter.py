"""CDN Adapters for FleetOps

Cloudflare, AWS CloudFront, Vercel Edge
"""

from abc import ABC, abstractmethod
from typing import Dict, Optional

class BaseCDNAdapter(ABC):
    """Abstract CDN adapter"""
    
    PROVIDER_NAME: str = "base"
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
    
    @abstractmethod
    async def purge_cache(self, path: str = None) -> bool:
        """Purge CDN cache"""
        pass
    
    @abstractmethod
    async def get_stats(self) -> Dict:
        """Get CDN stats"""
        pass

class CloudflareAdapter(BaseCDNAdapter):
    """Cloudflare CDN adapter"""
    
    PROVIDER_NAME = "cloudflare"
    
    def __init__(self, api_token: str = None, zone_id: str = None):
        super().__init__()
        self.api_token = api_token
        self.zone_id = zone_id
        self.base_url = "https://api.cloudflare.com/client/v4"
    
    async def purge_cache(self, path: str = None) -> bool:
        """Purge Cloudflare cache"""
        import requests
        
        try:
            data = {"purge_everything": True} if not path else {"files": [path]}
            
            response = requests.post(
                f"{self.base_url}/zones/{self.zone_id}/purge_cache",
                headers={
                    "Authorization": f"Bearer {self.api_token}",
                    "Content-Type": "application/json"
                },
                json=data
            )
            
            return response.status_code == 200
        except Exception:
            return False
    
    async def get_stats(self) -> Dict:
        """Get Cloudflare analytics"""
        import requests
        
        try:
            response = requests.get(
                f"{self.base_url}/zones/{self.zone_id}/analytics/dashboard",
                headers={"Authorization": f"Bearer {self.api_token}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                return {
                    "status": "success",
                    "requests": data.get("result", {}).get("timeseries", [{}])[0].get("requests", {}),
                    "bandwidth": data.get("result", {}).get("timeseries", [{}])[0].get("bandwidth", {})
                }
            
            return {"status": "error"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

class VercelEdgeAdapter(BaseCDNAdapter):
    """Vercel Edge Network adapter"""
    
    PROVIDER_NAME = "vercel_edge"
    
    def __init__(self, token: str = None, team_id: str = None):
        super().__init__()
        self.token = token
        self.team_id = team_id
        self.base_url = "https://api.vercel.com/v13"
    
    async def purge_cache(self, path: str = None) -> bool:
        """Purge Vercel cache"""
        import requests
        
        try:
            response = requests.post(
                f"{self.base_url}/deployments",
                headers={"Authorization": f"Bearer {self.token}"},
                json={"target": "production"}
            )
            
            # Vercel doesn't have direct cache purge, redeploy
            return response.status_code == 200
        except Exception:
            return False
    
    async def get_stats(self) -> Dict:
        """Get Vercel analytics"""
        import requests
        
        try:
            response = requests.get(
                f"{self.base_url}/teams/{self.team_id}/projects",
                headers={"Authorization": f"Bearer {self.token}"}
            )
            
            return {"status": "success" if response.status_code == 200 else "error"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

# Registry
CDN_ADAPTERS = {
    "cloudflare": CloudflareAdapter,
    "vercel_edge": VercelEdgeAdapter,
    "aws_cloudfront": CloudflareAdapter,  # TODO: Implement
    "none": CloudflareAdapter  # No-op
}

def get_cdn_adapter(provider: str, config: Dict = None):
    """Get CDN adapter"""
    adapter_class = CDN_ADAPTERS.get(provider)
    if not adapter_class:
        raise ValueError(f"Unknown CDN provider: {provider}")
    
    return adapter_class(**(config or {}))
