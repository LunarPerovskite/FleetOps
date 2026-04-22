"""Audit logging for FleetOps

Immutable, tamper-resistant audit trail for:
- Agent executions
- Credential access
- Human approvals
- Admin actions
- Failed login attempts
"""

import hashlib
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum

from app.core.database import get_db
from app.models.models import User

class AuditEventType(str, Enum):
    """Types of auditable events"""
    # Authentication
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    TOKEN_REFRESH = "token_refresh"
    
    # Agent execution
    AGENT_EXECUTION_STARTED = "agent_execution_started"
    AGENT_EXECUTION_COMPLETED = "agent_execution_completed"
    AGENT_EXECUTION_FAILED = "agent_execution_failed"
    AGENT_EXECUTION_CANCELLED = "agent_execution_cancelled"
    
    # Approvals
    APPROVAL_CREATED = "approval_created"
    APPROVAL_APPROVED = "approval_approved"
    APPROVAL_REJECTED = "approval_rejected"
    APPROVAL_ESCALATED = "approval_escalated"
    
    # Credentials
    CREDENTIALS_ACCESSED = "credentials_accessed"
    CREDENTIALS_UPDATED = "credentials_updated"
    CREDENTIALS_ROTATED = "credentials_rotated"
    
    # Admin
    USER_CREATED = "user_created"
    USER_DELETED = "user_deleted"
    PERMISSION_CHANGED = "permission_changed"
    AGENT_INSTANCE_CREATED = "agent_instance_created"
    AGENT_INSTANCE_DELETED = "agent_instance_deleted"
    
    # Data
    DATA_EXPORTED = "data_exported"
    DATA_DELETED = "data_deleted"
    SETTINGS_CHANGED = "settings_changed"

class AuditSeverity(str, Enum):
    """Severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AuditLogger:
    """Centralized audit logging"""
    
    def __init__(self):
        self.logger = logging.getLogger("fleetops.audit")
        self._chain_hash = "0" * 64  # Genesis hash
    
    async def log(
        self,
        event_type: AuditEventType,
        user_id: Optional[str] = None,
        org_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        details: Dict[str, Any] = None,
        severity: Optional[AuditSeverity] = None
    ) -> Dict[str, Any]:
        """Log an audit event"""
        
        # Calculate severity if not provided
        if not severity:
            severity = self._calculate_severity(event_type)
        
        # Create audit entry
        entry = {
            "id": self._generate_id(),
            "timestamp": datetime.utcnow().isoformat(),
            "event_type": event_type.value,
            "severity": severity.value,
            "user_id": user_id,
            "org_id": org_id,
            "ip_address": ip_address,
            "user_agent": None,  # Extract from request
            "details": self._sanitize_details(details or {}),
            "previous_hash": self._chain_hash,
        }
        
        # Calculate hash for chain integrity
        entry["current_hash"] = self._calculate_hash(entry)
        self._chain_hash = entry["current_hash"]
        
        # Write to database
        await self._write_to_db(entry)
        
        # Alert on high severity
        if severity in [AuditSeverity.HIGH, AuditSeverity.CRITICAL]:
            await self._send_alert(entry)
        
        return entry
    
    def _calculate_severity(self, event_type: AuditEventType) -> AuditSeverity:
        """Determine event severity"""
        critical_events = [
            AuditEventType.LOGIN_FAILURE,
            AuditEventType.CREDENTIALS_ACCESSED,
            AuditEventType.CREDENTIALS_UPDATED,
            AuditEventType.USER_DELETED,
            AuditEventType.PERMISSION_CHANGED,
            AuditEventType.AGENT_INSTANCE_DELETED,
            AuditEventType.DATA_EXPORTED,
        ]
        
        high_events = [
            AuditEventType.AGENT_EXECUTION_STARTED,
            AuditEventType.AGENT_EXECUTION_FAILED,
            AuditEventType.APPROVAL_ESCALATED,
            AuditEventType.SETTINGS_CHANGED,
        ]
        
        if event_type in critical_events:
            return AuditSeverity.CRITICAL
        elif event_type in high_events:
            return AuditSeverity.HIGH
        else:
            return AuditSeverity.MEDIUM
    
    def _sanitize_details(self, details: Dict) -> Dict:
        """Remove sensitive data from details"""
        sanitized = {}
        
        for key, value in details.items():
            # Never log passwords, tokens, or keys
            if any(sensitive in key.lower() for sensitive in 
                    ["password", "token", "key", "secret", "credential"]):
                sanitized[key] = "[REDACTED]"
            else:
                sanitized[key] = value
        
        return sanitized
    
    def _generate_id(self) -> str:
        """Generate unique audit ID"""
        import uuid
        return f"audit_{uuid.uuid4().hex}"
    
    def _calculate_hash(self, entry: Dict) -> str:
        """Calculate hash for chain integrity"""
        data = json.dumps(entry, sort_keys=True)
        return hashlib.sha256(data.encode()).hexdigest()
    
    async def _write_to_db(self, entry: Dict):
        """Write audit entry to database"""
        db = get_db()
        await db.execute("""
            INSERT INTO audit_log (
                id, timestamp, event_type, severity, user_id, org_id,
                ip_address, user_agent, details, previous_hash, current_hash
            ) VALUES (
                :id, :timestamp, :event_type, :severity, :user_id, :org_id,
                :ip_address, :user_agent, :details, :previous_hash, :current_hash
            )
        """, entry)
    
    async def _send_alert(self, entry: Dict):
        """Send security alert"""
        self.logger.warning(
            f"SECURITY ALERT: {entry['event_type']} by user {entry['user_id']} "
            f"from IP {entry['ip_address']}"
        )
        # TODO: Send email/Slack notification
    
    async def verify_chain(self, org_id: str) -> Dict[str, Any]:
        """Verify integrity of audit chain"""
        db = get_db()
        
        entries = await db.fetchall("""
            SELECT * FROM audit_log
            WHERE org_id = :org_id
            ORDER BY timestamp
        """, {"org_id": org_id})
        
        is_valid = True
        tampered_entries = []
        
        for i, entry in enumerate(entries):
            expected_hash = entry["current_hash"]
            
            # Recalculate hash
            data = {k: v for k, v in entry.items() if k != "current_hash"}
            recalculated = self._calculate_hash(data)
            
            if recalculated != expected_hash:
                is_valid = False
                tampered_entries.append({
                    "index": i,
                    "expected": expected_hash,
                    "calculated": recalculated
                })
        
        return {
            "is_valid": is_valid,
            "total_entries": len(entries),
            "tampered_entries": tampered_entries
        }

# Singleton
audit_logger = AuditLogger()
