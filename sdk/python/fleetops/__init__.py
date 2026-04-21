"""FleetOps SDK for Python

The official SDK for integrating AI agents with FleetOps governance platform.
"""

from .client import FleetOpsClient
from .agent import Agent
from .task import Task
from .events import EventReporter

__version__ = "0.1.0"
__all__ = ["FleetOpsClient", "Agent", "Task", "EventReporter"]
