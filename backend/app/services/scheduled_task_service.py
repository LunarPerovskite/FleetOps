"""Scheduled Task Service for FleetOps

Features:
- Cron-like scheduling
- Recurring tasks
- One-off scheduled tasks
- Timezone support
- Task templates
"""

import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Callable
from enum import Enum
import schedule
import threading

class ScheduleFrequency(Enum):
    ONCE = "once"
    MINUTELY = "minutely"
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"

class ScheduledTask:
    """A scheduled task configuration"""
    def __init__(self, task_id: str, name: str, agent_id: str,
                 template: Dict, schedule_config: Dict):
        self.task_id = task_id
        self.name = name
        self.agent_id = agent_id
        self.template = template
        self.schedule = schedule_config
        self.active = True
        self.last_run: Optional[datetime] = None
        self.next_run: Optional[datetime] = None
        self.run_count = 0
        self.created_at = datetime.utcnow()

class ScheduledTaskService:
    """Task scheduling and automation"""
    
    def __init__(self):
        self.scheduled_tasks: Dict[str, ScheduledTask] = {}
        self.task_handlers: Dict[str, Callable] = {}
        self.running = False
        self.scheduler_thread = None
    
    def register_handler(self, task_type: str, handler: Callable):
        """Register a handler for a task type"""
        self.task_handlers[task_type] = handler
    
    def create_scheduled_task(self, name: str, agent_id: str,
                             template: Dict, schedule_config: Dict) -> Dict:
        """Create a new scheduled task"""
        task_id = f"sched_{agent_id}_{datetime.utcnow().timestamp()}"
        
        task = ScheduledTask(task_id, name, agent_id, template, schedule_config)
        self.scheduled_tasks[task_id] = task
        
        # Schedule it
        self._schedule_task(task)
        
        return {
            "task_id": task_id,
            "name": name,
            "status": "scheduled",
            "next_run": task.next_run.isoformat() if task.next_run else None
        }
    
    def _schedule_task(self, task: ScheduledTask):
        """Schedule a task using schedule library"""
        frequency = task.schedule.get("frequency", "daily")
        at_time = task.schedule.get("at_time", "09:00")
        
        if frequency == "minutely":
            interval = task.schedule.get("interval", 5)
            schedule.every(interval).minutes.do(self._run_task, task.task_id)
        elif frequency == "hourly":
            schedule.every().hour.at(at_time).do(self._run_task, task.task_id)
        elif frequency == "daily":
            schedule.every().day.at(at_time).do(self._run_task, task.task_id)
        elif frequency == "weekly":
            day = task.schedule.get("day", "monday")
            getattr(schedule.every(), day).at(at_time).do(self._run_task, task.task_id)
        elif frequency == "monthly":
            day = task.schedule.get("day", 1)
            # schedule library doesn't support monthly directly
            schedule.every(30).days.at(at_time).do(self._run_task, task.task_id)
        elif frequency == "once":
            run_at = datetime.fromisoformat(task.schedule.get("run_at"))
            delay = (run_at - datetime.utcnow()).total_seconds()
            if delay > 0:
                threading.Timer(delay, self._run_task, args=[task.task_id]).start()
        
        # Calculate next run
        task.next_run = self._get_next_run(frequency, at_time)
    
    def _get_next_run(self, frequency: str, at_time: str) -> Optional[datetime]:
        """Calculate next run time"""
        now = datetime.utcnow()
        
        if frequency == "daily":
            next_run = datetime.strptime(at_time, "%H:%M").replace(
                year=now.year, month=now.month, day=now.day
            )
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run
        
        return None
    
    def _run_task(self, task_id: str):
        """Execute a scheduled task"""
        if task_id not in self.scheduled_tasks:
            return
        
        task = self.scheduled_tasks[task_id]
        
        if not task.active:
            return
        
        print(f"Running scheduled task: {task.name}")
        
        # Execute handler
        handler = self.task_handlers.get(task.template.get("type"))
        if handler:
            try:
                asyncio.create_task(handler(task))
                task.run_count += 1
                task.last_run = datetime.utcnow()
            except Exception as e:
                print(f"Error running task {task_id}: {e}")
        
        # Update next run
        if task.schedule.get("frequency") != "once":
            task.next_run = self._get_next_run(
                task.schedule.get("frequency", "daily"),
                task.schedule.get("at_time", "09:00")
            )
    
    def start_scheduler(self):
        """Start the scheduler in a background thread"""
        self.running = True
        
        def run_schedule():
            while self.running:
                schedule.run_pending()
                asyncio.sleep(1)
        
        self.scheduler_thread = threading.Thread(target=run_schedule, daemon=True)
        self.scheduler_thread.start()
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5)
    
    def get_scheduled_tasks(self, agent_id: Optional[str] = None) -> List[Dict]:
        """Get all scheduled tasks"""
        tasks = []
        for task in self.scheduled_tasks.values():
            if agent_id and task.agent_id != agent_id:
                continue
            
            tasks.append({
                "task_id": task.task_id,
                "name": task.name,
                "agent_id": task.agent_id,
                "active": task.active,
                "last_run": task.last_run.isoformat() if task.last_run else None,
                "next_run": task.next_run.isoformat() if task.next_run else None,
                "run_count": task.run_count,
                "schedule": task.schedule
            })
        
        return tasks
    
    def deactivate_task(self, task_id: str) -> bool:
        """Deactivate a scheduled task"""
        if task_id in self.scheduled_tasks:
            self.scheduled_tasks[task_id].active = False
            return True
        return False
    
    def activate_task(self, task_id: str) -> bool:
        """Activate a scheduled task"""
        if task_id in self.scheduled_tasks:
            self.scheduled_tasks[task_id].active = True
            return True
        return False
