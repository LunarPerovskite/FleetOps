"""Background Model Discovery Scheduler for FleetOps

Runs auto-discovery periodically to keep model registry fresh.
Integrates with the existing scheduled_task_service infrastructure.
"""

import asyncio
import threading
from typing import Optional
from datetime import datetime

from app.core.logging_config import get_logger
from app.core.auto_discovery_service import auto_discovery
from app.core.model_discovery import discovery_service

logger = get_logger("fleetops.model_discovery.scheduler")


class ModelDiscoveryScheduler:
    """Schedules periodic model discovery from all configured providers"""

    def __init__(self, interval_minutes: int = 30):
        self.interval_minutes = interval_minutes
        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()

    def start(self):
        """Start background discovery thread"""
        if self._thread and self._thread.is_alive():
            logger.info("Discovery scheduler already running")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run_loop, daemon=True)
        self._thread.start()
        logger.info(f"Model discovery scheduler started (every {self.interval_minutes} min)")

    def stop(self):
        """Stop background discovery thread"""
        if self._thread:
            self._stop_event.set()
            self._thread.join(timeout=5)
            logger.info("Model discovery scheduler stopped")

    def _run_loop(self):
        """Main loop that triggers discovery"""
        import time

        # Run immediately on startup
        self._discover_all()

        while not self._stop_event.is_set():
            # Wait with periodic checks so stop is responsive
            waited = 0
            while waited < self.interval_minutes * 60:
                if self._stop_event.is_set():
                    return
                time.sleep(1)
                waited += 1

            self._discover_all()

    def _discover_all(self):
        """Trigger async discovery in a new event loop"""
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            results = loop.run_until_complete(auto_discovery.discover_all_configured())

            # Also register discovered models into the registry
            discovery_service.register_all()

            total = sum(len(v) for v in results.values())
            logger.info(f"Background discovery: {total} models refreshed from {len(results)} providers")
        except Exception as e:
            logger.error(f"Background discovery failed: {e}")
        finally:
            loop.close()


# Singleton
discovery_scheduler = ModelDiscoveryScheduler(interval_minutes=30)


def start_discovery_scheduler(interval_minutes: int = 30) -> ModelDiscoveryScheduler:
    """Start the background discovery scheduler"""
    scheduler = ModelDiscoveryScheduler(interval_minutes=interval_minutes)
    scheduler.start()
    return scheduler
