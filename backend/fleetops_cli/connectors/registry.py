"""Connector Registry for FleetOps

Central registry for managing all CLI connectors.
"""

import os
import json
from typing import Dict, List, Optional, Type
from .base import BaseConnector, ConnectorManifest
from .generic import GenericCLIConnector, PREBUILT_MANIFESTS, list_prebuilt_connectors


class ConnectorRegistry:
    """Registry for all FleetOps connectors"""
    
    def __init__(self):
        self._connectors: Dict[str, BaseConnector] = {}
        self._manifests_dir = os.path.expanduser("~/.fleetops/connectors")
        os.makedirs(self._manifests_dir, exist_ok=True)
        
        # Auto-load pre-built connectors
        self._load_prebuilt()
    
    def _load_prebuilt(self) -> None:
        """Load all pre-built connectors"""
        from .codex import CodexConnector
        from .copilot import CopilotConnector
        from .opencode import OpenCodeConnector
        from .heroku import HerokuConnector
        from .openclaw import OpenClawConnector
        
        prebuilt = {
            "codex": CodexConnector,
            "copilot": CopilotConnector,
            "opencode": OpenCodeConnector,
            "heroku": HerokuConnector,
            "openclaw": OpenClawConnector,
        }
        
        for name, connector_class in prebuilt.items():
            try:
                connector = connector_class()
                self._connectors[name] = connector
            except Exception as e:
                print(f"[FleetOps] Failed to load {name} connector: {e}")
    
    def register(self, name: str, connector: BaseConnector) -> None:
        """Register a custom connector"""
        self._connectors[name] = connector
        print(f"[FleetOps] Registered connector: {name}")
    
    def get(self, name: str) -> Optional[BaseConnector]:
        """Get a connector by name"""
        return self._connectors.get(name)
    
    def list(self) -> List[str]:
        """List all registered connectors"""
        return list(self._connectors.keys())
    
    def create_from_manifest(self, manifest_path: str) -> Optional[BaseConnector]:
        """Create connector from JSON manifest file"""
        try:
            connector = GenericCLIConnector.from_manifest(manifest_path)
            self.register(connector.name, connector)
            return connector
        except Exception as e:
            print(f"[FleetOps] Failed to create connector from {manifest_path}: {e}")
            return None
    
    def create_from_prebuilt(self, name: str) -> Optional[BaseConnector]:
        """Create connector from pre-built manifest"""
        manifest_data = PREBUILT_MANIFESTS.get(name)
        if not manifest_data:
            print(f"[FleetOps] No pre-built connector found: {name}")
            print(f"[FleetOps] Available: {', '.join(list_prebuilt_connectors())}")
            return None
        
        try:
            connector = GenericCLIConnector.from_dict(manifest_data)
            self.register(connector.name, connector)
            return connector
        except Exception as e:
            print(f"[FleetOps] Failed to create pre-built connector {name}: {e}")
            return None
    
    def wrap_all(self) -> None:
        """Wrap all registered CLIs"""
        for name, connector in self._connectors.items():
            print(f"[FleetOps] Wrapping {name}...")
            connector.wrap_cli()
    
    def unwrap_all(self) -> None:
        """Unwrap all registered CLIs"""
        for name, connector in self._connectors.items():
            print(f"[FleetOps] Unwrapping {name}...")
            connector.unwrap_cli()
    
    def save_manifest(self, name: str, path: Optional[str] = None) -> None:
        """Save connector manifest to file"""
        connector = self._connectors.get(name)
        if not connector or not connector.manifest:
            print(f"[FleetOps] Connector {name} not found or has no manifest")
            return
        
        if path is None:
            path = os.path.join(self._manifests_dir, f"{name}.json")
        
        connector.manifest.save_manifest(path)
        print(f"[FleetOps] Manifest saved to: {path}")
    
    def load_user_manifests(self) -> None:
        """Load all user-created manifests from directory"""
        if not os.path.exists(self._manifests_dir):
            return
        
        for filename in os.listdir(self._manifests_dir):
            if filename.endswith(".json"):
                path = os.path.join(self._manifests_dir, filename)
                self.create_from_manifest(path)


# Singleton registry
_registry: Optional[ConnectorRegistry] = None


def get_registry() -> ConnectorRegistry:
    """Get or create the global connector registry"""
    global _registry
    if _registry is None:
        _registry = ConnectorRegistry()
    return _registry
