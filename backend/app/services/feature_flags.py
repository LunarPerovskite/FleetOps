"""Feature Flags System for FleetOps

Gradual rollouts, A/B testing, and feature toggles
"""

from typing import Dict, Any, Optional
from datetime import datetime
import json

class FeatureFlagsService:
    """Manage feature flags for gradual rollouts"""
    
    def __init__(self):
        # In production, store in Redis/Database
        self._flags: Dict[str, Dict[str, Any]] = {
            "new_dashboard": {
                "enabled": True,
                "rollout_percentage": 100,
                "description": "New dashboard layout",
                "created_at": "2026-04-01"
            },
            "advanced_analytics": {
                "enabled": False,
                "rollout_percentage": 0,
                "description": "Advanced analytics charts",
                "created_at": "2026-04-15"
            },
            "voice_commands": {
                "enabled": True,
                "rollout_percentage": 25,
                "description": "Voice command interface",
                "created_at": "2026-04-20"
            },
            "beta_marketplace": {
                "enabled": False,
                "rollout_percentage": 0,
                "description": "Marketplace (beta)",
                "created_at": "2026-04-22"
            }
        }
    
    def is_enabled(self, flag_name: str, user_id: Optional[str] = None) -> bool:
        """Check if feature is enabled for user"""
        flag = self._flags.get(flag_name)
        if not flag:
            return False
        
        if not flag["enabled"]:
            return False
        
        # Full rollout
        if flag["rollout_percentage"] >= 100:
            return True
        
        # Percentage-based rollout
        if user_id and flag["rollout_percentage"] > 0:
            # Deterministic based on user_id hash
            user_hash = hash(f"{flag_name}:{user_id}") % 100
            return user_hash < flag["rollout_percentage"]
        
        return False
    
    def get_all_flags(self, user_id: Optional[str] = None) -> Dict[str, bool]:
        """Get all flags for a user"""
        return {
            name: self.is_enabled(name, user_id)
            for name in self._flags.keys()
        }
    
    def toggle_flag(self, flag_name: str, enabled: bool) -> bool:
        """Enable/disable a flag"""
        if flag_name in self._flags:
            self._flags[flag_name]["enabled"] = enabled
            return True
        return False
    
    def set_rollout(self, flag_name: str, percentage: int) -> bool:
        """Set rollout percentage"""
        if flag_name in self._flags and 0 <= percentage <= 100:
            self._flags[flag_name]["rollout_percentage"] = percentage
            return True
        return False
    
    def create_flag(self, name: str, enabled: bool = False, percentage: int = 0, description: str = "") -> bool:
        """Create a new feature flag"""
        if name in self._flags:
            return False
        
        self._flags[name] = {
            "enabled": enabled,
            "rollout_percentage": percentage,
            "description": description,
            "created_at": datetime.utcnow().isoformat()
        }
        return True

# Initialize service
feature_flags = FeatureFlagsService()
