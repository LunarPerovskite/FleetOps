"""Google A2A Protocol Models for FleetOps

Full implementation of Google's Agent-to-Agent (A2A) protocol.
Based on: https://github.com/google/a2a  (official spec)

FleetOps acts as the A2A task hub — agents never talk directly to each other.
Every task flows through FleetOps for governance, audit, and routing.

Protocol Endpoints (from spec):
  GET   /.well-known/agent.json         → Agent Card
  POST  /tasks/send                    → Send task (blocking)
  POST  /tasks/sendSubscribe           → Send task (SSE streaming)
  POST  /tasks/get                     → Get task status
  POST  /tasks/cancel                  → Cancel task
  POST  /tasks/subscribe               → Subscribe to task updates (SSE)
  POST  /tasks/pushNotification/set    → Register push notification

Task States:
  submitted ─&#x2014;> working ─&#x2014;> [ input-required ] ─&#x2014;> completed | failed | canceled

Roles: user | agent
Parts: text | file | data
"""

from typing import Optional, List, Dict, Any, Union
from dataclasses import dataclass, field, asdict
from datetime import datetime
import uuid

__all__ = [
    "AgentCard",
    "AgentCapabilities",
    "AgentAuthentication",
    "AgentSkill",
    "TextPart",
    "FilePart",
    "DataPart",
    "Part",
    "Message",
    "Artifact",
    "TaskState",
    "Task",
    "TaskSendParams",
    "TaskQueryParams",
    "TaskIdParams",
    "TaskStatusUpdateEvent",
    "TaskArtifactUpdateEvent",
    "PushNotificationConfig",
    "A2AError",
]


# ═══════════════════════════════════════════
# Enums
# ═══════════════════════════════════════════

class TaskState:
    """Google A2A task lifecycle states"""
    SUBMITTED = "submitted"
    WORKING = "working"
    INPUT_REQUIRED = "input-required"  # Agent needs more input
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELED = "canceled"


# ═══════════════════════════════════════════
# Agent Card (GET /.well-known/agent.json)
# ═══════════════════════════════════════════

@dataclass
class AgentCapabilities:
    """What the A2A endpoint supports"""
    streaming: bool = False       # supports /tasks/sendSubscribe (SSE)
    pushNotifications: bool = False
    stateTransitionHistory: bool = False


@dataclass
class AgentAuthentication:
    """How agents authenticate"""
    schemes: List[str] = field(default_factory=list)  # ["bearer", "apiKey"]
    credentials: Optional[str] = None  # URL for credentials (rare)


@dataclass
class AgentSkill:
    """A capability the agent can perform"""
    id: str
    name: str
    description: str = ""
    tags: List[str] = field(default_factory=list)
    examples: List[str] = field(default_factory=list)
    inputModes: List[str] = field(default_factory=list)   # MIME types
    outputModes: List[str] = field(default_factory=list)  # MIME types


@dataclass
class AgentCard:
    """Agent Card — the "resume" every A2A agent publishes.

    FleetOps publishes a card showing it's the governance hub,
    and other agents can publish theirs if FleetOps proxies for them.
    """
    name: str = "FleetOps"
    description: str = "FleetOps A2A Governance Hub"
    url: str = ""
    provider: Dict[str, str] = field(default_factory=dict)  # {"organization": "FleetOps"}
    version: str = "1.0.0"
    documentationUrl: Optional[str] = None
    capabilities: AgentCapabilities = field(default_factory=AgentCapabilities)
    authentication: AgentAuthentication = field(default_factory=AgentAuthentication)
    defaultInputModes: List[str] = field(default_factory=lambda: ["text"])
    defaultOutputModes: List[str] = field(default_factory=lambda: ["text"])
    skills: List[AgentSkill] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        d["capabilities"] = asdict(self.capabilities)
        d["authentication"] = asdict(self.authentication)
        d["skills"] = [asdict(s) for s in self.skills]
        return d


# ═══════════════════════════════════════════
# Messages and Parts
# ═══════════════════════════════════════════

@dataclass
class TextPart:
    type: str = "text"
    text: str = ""


@dataclass
class FileContent:
    name: str = ""
    mimeType: str = ""
    bytes: Optional[str] = None  # base64-encoded data
    uri: Optional[str] = None   # Alternative: URL reference


@dataclass
class FilePart:
    type: str = "file"
    file: FileContent = field(default_factory=FileContent)


@dataclass
class DataPart:
    type: str = "data"
    data: Dict[str, Any] = field(default_factory=dict)  # arbitrary JSON


Part = Union[TextPart, FilePart, DataPart]


def part_to_dict(p: Part) -> Dict[str, Any]:
    """Serialize any Part"""
    if isinstance(p, TextPart):
        return {"type": "text", "text": p.text}
    if isinstance(p, FilePart):
        return {
            "type": "file",
            "file": {
                "name": p.file.name,
                "mimeType": p.file.mimeType,
                **({"bytes": p.file.bytes} if p.file.bytes else {}),
                **({"uri": p.file.uri} if p.file.uri else {})
            }
        }
    if isinstance(p, DataPart):
        return {"type": "data", "data": p.data}
    return {}


def part_from_dict(d: Dict[str, Any]) -> Optional[Part]:
    """Deserialize a Part"""
    t = d.get("type")
    if t == "text":
        return TextPart(text=d.get("text", ""))
    if t == "file":
        fd = d.get("file", {})
        return FilePart(file=FileContent(
            name=fd.get("name", ""),
            mimeType=fd.get("mimeType", ""),
            bytes=fd.get("bytes"),
            uri=fd.get("uri")
        ))
    if t == "data":
        return DataPart(data=d.get("data", {}))
    return None


@dataclass
class Message:
    """A single message in a task conversation"""
    role: str = "user"  # "user" or "agent"
    parts: List[Part] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "parts": [part_to_dict(p) for p in self.parts],
            "metadata": self.metadata
        }

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "Message":
        m = cls(
            role=d.get("role", "user"),
            metadata=d.get("metadata", {})
        )
        m.parts = [p for p in (part_from_dict(pd) for pd in d.get("parts", [])) if p]
        return m


# ═══════════════════════════════════════════
# Artifacts
# ═══════════════════════════════════════════

@dataclass
class Artifact:
    """Output produced by an agent during a task (files, code, etc.)"""
    name: str = ""            # identifier: "test_file", "report", etc.
    description: str = ""
    parts: List[Part] = field(default_factory=list)
    index: int = 0           # order among artifacts
    append: Optional[bool] = None  # True = concatenate to previous artifact with same name
    lastChunk: Optional[bool] = None  # True = this is the final chunk of an artifact
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ═══════════════════════════════════════════
# Task
# ═══════════════════════════════════════════

@dataclass
class Task:
    """Google A2A Task — the central unit of work"""
    id: str = ""                  # Task UUID
    sessionId: str = ""           # Session UUID (groups related tasks)
    status: str = TaskState.SUBMITTED
    history: List[Message] = field(default_factory=list)
    artifacts: List[Artifact] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)  # org_id, agent_from, agent_to

    # FleetOps extensions (not in Google spec, but needed for governance)
    org_id: str = ""              # FleetOps: which org owns this task
    from_agent_id: str = ""       # FleetOps: which agent submitted
    to_agent_id: Optional[str] = ""  # FleetOps: which agent should handle it
    governance_status: str = ""   # FleetOps: "pending_approval", "auto_approved", "denied"
    approval_id: Optional[str] = None

    @classmethod
    def new(cls, session_id: str = "", metadata: Dict = None) -> "Task":
        return cls(
            id=str(uuid.uuid4()),
            sessionId=session_id or str(uuid.uuid4()),
            metadata=metadata or {}
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "sessionId": self.sessionId,
            "status": self.status,
            "history": [m.to_dict() for m in self.history],
            "artifacts": [a.to_dict() for a in self.artifacts],
            "metadata": self.metadata
        }


# ═══════════════════════════════════════════
# RPC Request/Response Models
# ═══════════════════════════════════════════

@dataclass
class TaskSendParams:
    """POST /tasks/send  and  POST /tasks/sendSubscribe"""
    id: str = ""                # Task ID (optional, auto-generated if empty)
    sessionId: Optional[str] = None
    message: Message = field(default_factory=Message)
    acceptedOutputModes: Optional[List[str]] = None  # e.g. ["text", "file"]
    artifacts: Optional[List[Artifact]] = None  # pre-existing artifacts
    pushNotification: Optional[Dict] = None     # push config
    metadata: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_dict(cls, d: Dict[str, Any]) -> "TaskSendParams":
        params = cls(
            id=d.get("id", ""),
            sessionId=d.get("sessionId"),
            message=Message.from_dict(d.get("message", {})),
            acceptedOutputModes=d.get("acceptedOutputModes"),
            artifacts=[Artifact(**a) for a in d.get("artifacts", [])] if d.get("artifacts") else None,
            metadata=d.get("metadata", {})
        )
        params.pushNotification = d.get("pushNotification")
        return params


@dataclass
class TaskQueryParams:
    """POST /tasks/get"""
    id: str = ""  # Task ID


@dataclass
class TaskIdParams:
    """POST /tasks/cancel"""
    id: str = ""  # Task ID


# ── SSE Events ──────────────────────────────────────────────────────

@dataclass
class TaskStatusUpdateEvent:
    """SSE event for task status changes"""
    id: str = ""
    status: str = ""
    final: bool = False  # True if this is the terminal update
    message: Optional[Message] = None  # Optional update message

    def to_sse(self) -> str:
        """Serialize as Server-Sent Event"""
        import json
        data = {"id": self.id, "status": self.status, "final": self.final}
        if self.message:
            data["message"] = self.message.to_dict()
        return f"event: status\ndata: {json.dumps(data)}\n\n"


@dataclass
class TaskArtifactUpdateEvent:
    """SSE event for artifact streaming"""
    id: str = ""
    artifact: Artifact = field(default_factory=Artifact)
    final: bool = False  # True if stream complete

    def to_sse(self) -> str:
        import json
        return f"event: artifact\ndata: {json.dumps({'id': self.id, 'artifact': self.artifact.to_dict(), 'final': self.final})}\n\n"


# ── Push Notifications ────────────────────────────────────────────────

@dataclass
class PushNotificationConfig:
    """Agent sets where FleetOps should POST task updates"""
    url: str = ""
    token: Optional[str] = None


# ── Errors ──────────────────────────────────────────────────────────

class A2AError(Exception):
    """Structured A2A error per spec (JSON-RPC 2.0 style)"""

    CODE_AGENT_NOT_FOUND = -32000
    CODE_TASK_NOT_FOUND = -32001
    CODE_TASK_NOT_CANCELABLE = -32002
    CODE_PUSH_NOTIFICATION_NOT_SUPPORTED = -32003
    CODE_PUSH_NOTIFICATION_AUTH_INVALID = -32004
    CODE_UNSUPPORTED_OPERATION = -32005
    CODE_TOO_MANY_REQUESTS = -32006
    CODE_INTERNAL_ERROR = -32007

    def __init__(self, code: int, message: str, data: Dict = None):
        self.code = code
        self.message = message
        self.data = data or {}
        super().__init__(f"A2AError {code}: {message}")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "code": self.code,
            "message": self.message,
            "data": self.data
        }
