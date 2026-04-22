"""Provider Registry for FleetOps

Organizations choose their providers. We provide adapters.
"""

from enum import Enum
from typing import Dict, Optional, Any
from dataclasses import dataclass

class AuthProvider(Enum):
    CLERK = "clerk"
    AUTH0 = "auth0"
    OKTA = "okta"
    AZURE_AD = "azure_ad"
    AWS_COGNITO = "cognito"
    SELF_HOSTED = "self_hosted"

class DatabaseProvider(Enum):
    SUPABASE = "supabase"
    NEON = "neon"
    AWS_RDS = "aws_rds"
    POSTGRES = "postgres"  # Self-hosted
    SQLITE = "sqlite"  # Dev only

class HostingProvider(Enum):
    VERCEL = "vercel"
    RAILWAY = "railway"
    RENDER = "render"
    AWS = "aws"
    GCP = "gcp"
    AZURE = "azure"
    SELF_HOSTED = "self_hosted"

class SecretsProvider(Enum):
    DOPPLER = "doppler"
    HASHICORP_VAULT = "vault"
    AWS_SECRETS = "aws_secrets"
    AZURE_KEYVAULT = "azure_keyvault"
    ENV = "env"  # .env files (dev)

class MonitoringProvider(Enum):
    DATADOG = "datadog"
    SENTRY = "sentry"
    CLOUDWATCH = "cloudwatch"
    GRAFANA = "grafana"
    NONE = "none"

class CDNProvider(Enum):
    CLOUDFLARE = "cloudflare"
    AWS_CLOUDFRONT = "aws_cloudfront"
    VERCEL_EDGE = "vercel_edge"
    NONE = "none"

@dataclass
class ProviderConfig:
    """Organization's chosen providers"""
    auth: AuthProvider = AuthProvider.CLERK
    database: DatabaseProvider = DatabaseProvider.SUPABASE
    hosting: HostingProvider = HostingProvider.VERCEL
    secrets: SecretsProvider = SecretsProvider.ENV
    monitoring: MonitoringProvider = MonitoringProvider.SENTRY
    cdn: CDNProvider = CDNProvider.CLOUDFLARE
    
    # Provider-specific settings
    auth_config: Dict[str, Any] = None
    db_config: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.auth_config is None:
            self.auth_config = {}
        if self.db_config is None:
            self.db_config = {}

# Default quick-start configuration (easiest + cheapest)
QUICK_START_CONFIG = ProviderConfig(
    auth=AuthProvider.CLERK,
    database=DatabaseProvider.SUPABASE,
    hosting=HostingProvider.VERCEL,
    secrets=SecretsProvider.DOPPLER,
    monitoring=MonitoringProvider.SENTRY,
    cdn=CDNProvider.CLOUDFLARE,
    auth_config={
        "clerk_publishable_key": "{{CLERK_PUBLISHABLE_KEY}}",
        "clerk_secret_key": "{{CLERK_SECRET_KEY}}",
        "mfa_enabled": True,
        "sso_enabled": False  # Upgrade for SSO
    },
    db_config={
        "connection_pool_size": 20,
        "ssl_mode": "require"
    }
)

# Enterprise configuration
ENTERPRISE_CONFIG = ProviderConfig(
    auth=AuthProvider.OKTA,
    database=DatabaseProvider.AWS_RDS,
    hosting=HostingProvider.AWS,
    secrets=SecretsProvider.HASHICORP_VAULT,
    monitoring=MonitoringProvider.DATADOG,
    cdn=CDNProvider.CLOUDFLARE,
    auth_config={
        "mfa_required": True,
        "sso_required": True,
        "session_timeout": 3600  # 1 hour
    },
    db_config={
        "multi_az": True,
        "encryption_at_rest": True,
        "backup_retention_days": 30
    }
)

# Budget configuration ($0-5/month)
BUDGET_CONFIG = ProviderConfig(
    auth=AuthProvider.CLERK,
    database=DatabaseProvider.SUPABASE,
    hosting=HostingProvider.VERCEL,
    secrets=SecretsProvider.ENV,
    monitoring=MonitoringProvider.NONE,
    cdn=CDNProvider.CLOUDFLARE,
    auth_config={
        "mfa_enabled": False  # Clerk free tier
    }
)

class ProviderRegistry:
    """Registry for provider adapters"""
    
    def __init__(self):
        self.auth_adapters: Dict[str, Any] = {}
        self.db_adapters: Dict[str, Any] = {}
        self.secrets_adapters: Dict[str, Any] = {}
    
    def register_auth_adapter(self, provider: AuthProvider, adapter: Any):
        """Register an auth provider adapter"""
        self.auth_adapters[provider.value] = adapter
    
    def register_db_adapter(self, provider: DatabaseProvider, adapter: Any):
        """Register a database provider adapter"""
        self.db_adapters[provider.value] = adapter
    
    def get_auth_adapter(self, provider: AuthProvider):
        """Get auth adapter for provider"""
        return self.auth_adapters.get(provider.value)
    
    def get_db_adapter(self, provider: DatabaseProvider):
        """Get database adapter for provider"""
        return self.db_adapters.get(provider.value)
    
    def get_provider_info(self) -> Dict:
        """Get all available providers with pricing"""
        return {
            "auth": {
                "clerk": {
                    "name": "Clerk",
                    "pricing": "Free up to 10k MAU, then $0.02/MAU",
                    "features": ["OAuth", "MFA", "Session management", "React SDK"],
                    "setup_time": "5 minutes",
                    "best_for": "Startups, modern apps"
                },
                "auth0": {
                    "name": "Auth0",
                    "pricing": "Free up to 7.5k MAU, then $0.07/MAU",
                    "features": ["SAML", "SSO", "Enterprise", "Mature"],
                    "setup_time": "30 minutes",
                    "best_for": "Enterprises, complex needs"
                },
                "okta": {
                    "name": "Okta",
                    "pricing": "$2/user/month",
                    "features": ["Workforce identity", "Best SSO", "Compliance"],
                    "setup_time": "2 hours",
                    "best_for": "Large enterprises"
                },
                "self_hosted": {
                    "name": "Self-Hosted (FleetOps)",
                    "pricing": "$0 (you manage)",
                    "features": ["Full control", "No vendor lock-in"],
                    "setup_time": "1 hour",
                    "best_for": "Privacy-focused, budget"
                }
            },
            "database": {
                "supabase": {
                    "name": "Supabase",
                    "pricing": "Free tier: 500MB, 2M requests",
                    "features": ["PostgreSQL", "Realtime", "Auth included", "Easy"],
                    "setup_time": "10 minutes",
                    "best_for": "Startups, rapid prototyping"
                },
                "neon": {
                    "name": "Neon",
                    "pricing": "Free tier: 3GB, serverless",
                    "features": ["Serverless", "Branching", "Auto-scale"],
                    "setup_time": "10 minutes",
                    "best_for": "Serverless apps"
                },
                "postgres": {
                    "name": "Self-Hosted PostgreSQL",
                    "pricing": "$0 (you manage)",
                    "features": ["Full control", "No limits"],
                    "setup_time": "1 hour",
                    "best_for": "On-premise, compliance"
                }
            },
            "hosting": {
                "vercel": {
                    "name": "Vercel",
                    "pricing": "Free tier: hobby projects",
                    "features": ["Edge network", "Auto-deploy", "Analytics"],
                    "setup_time": "5 minutes",
                    "best_for": "Frontend, Next.js"
                },
                "railway": {
                    "name": "Railway",
                    "pricing": "$5/month starter",
                    "features": ["Simple", "Auto-scale", "Databases"],
                    "setup_time": "15 minutes",
                    "best_for": "Backend APIs"
                },
                "aws": {
                    "name": "AWS",
                    "pricing": "Pay per use",
                    "features": ["Enterprise", "Global", "Compliance"],
                    "setup_time": "2 hours",
                    "best_for": "Scale, enterprise"
                }
            }
        }

# Global registry
provider_registry = ProviderRegistry()
