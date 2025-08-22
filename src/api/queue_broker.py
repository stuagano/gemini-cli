"""
Queue Broker for managing agent task execution
Handles prioritization, concurrency, and result management
"""

from typing import Dict, Any, Optional, List, Callable, Awaitable
import asyncio
import heapq
import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import json

logger = logging.getLogger(__name__)

class Priority(Enum):
    """Task priority levels"""
    CRITICAL = 0
    HIGH = 1
    NORMAL = 2
    LOW = 3
    
    def __lt__(self, other):
        return self.value < other.value

class TaskStatus(Enum):
    """Task execution status"""
    QUEUED = "queued"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMEOUT = "timeout"

@dataclass
class QueuedTask:
    """Represents a queued task"""
    task_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    priority: Priority = Priority.NORMAL
    agent_type: str = ""
    action: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)
    context: Dict[str, Any] = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: TaskStatus = TaskStatus.QUEUED
    result: Optional[Any] = None
    error: Optional[str] = None
    retries: int = 0
    max_retries: int = 3
    timeout: int = 30  # seconds
    callback: Optional[Callable[[Any], Awaitable[None]]] = None
    
    def __lt__(self, other):
        """Priority queue comparison"""
        if self.priority != other.priority:
            return self.priority < other.priority
        return self.created_at < other.created_at
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            "task_id": self.task_id,
            "priority": self.priority.name,
            "agent_type": self.agent_type,
            "action": self.action,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "retries": self.retries,
            "error": self.error
        }

class TaskQueue:
    """Priority queue for tasks"""
    
    def __init__(self):
        self.queue: List[QueuedTask] = []
        self.task_map: Dict[str, QueuedTask] = {}
        self._lock = asyncio.Lock()
    
    async def put(self, task: QueuedTask):
        """Add task to queue"""
        async with self._lock:
            heapq.heappush(self.queue, task)
            self.task_map[task.task_id] = task
    
    async def get(self) -> Optional[QueuedTask]:
        """Get highest priority task"""
        async with self._lock:
            while self.queue:
                task = heapq.heappop(self.queue)
                # Skip cancelled tasks
                if task.status != TaskStatus.CANCELLED:
                    return task
            return None
    
    async def remove(self, task_id: str) -> bool:
        """Remove a task from queue"""
        async with self._lock:
            if task_id in self.task_map:
                task = self.task_map[task_id]
                task.status = TaskStatus.CANCELLED
                del self.task_map[task_id]
                return True
            return False
    
    def size(self) -> int:
        """Get queue size"""
        return len([t for t in self.queue if t.status == TaskStatus.QUEUED])
    
    def get_tasks(self, agent_type: Optional[str] = None) -> List[QueuedTask]:
        """Get all tasks, optionally filtered by agent"""
        tasks = list(self.task_map.values())
        if agent_type:
            tasks = [t for t in tasks if t.agent_type == agent_type]
        return sorted(tasks, key=lambda t: (t.priority.value, t.created_at))

class QueueBroker:
    """Manages task queues and execution"""
    
    def __init__(self, max_concurrent: int = 10, max_per_agent: int = 3):
        self.max_concurrent = max_concurrent
        self.max_per_agent = max_per_agent
        
        # Queues per agent type
        self.queues: Dict[str, TaskQueue] = {}
        
        # Active tasks
        self.active_tasks: Dict[str, asyncio.Task] = {}
        self.agent_task_count: Dict[str, int] = {}
        
        # Results storage
        self.results: Dict[str, Any] = {}
        self.result_ttl = timedelta(minutes=30)
        
        # Statistics
        self.stats = {
            "total_enqueued": 0,
            "total_completed": 0,
            "total_failed": 0,
            "total_timeout": 0,
            "total_cancelled": 0
        }
        
        # Task executor
        self.executor: Optional[Callable] = None
        
        # Background tasks
        self.processor_task: Optional[asyncio.Task] = None
        self.cleanup_task: Optional[asyncio.Task] = None
    
    async def start(self, executor: Callable[[QueuedTask], Awaitable[Any]]):
        """Start the queue broker"""
        self.executor = executor
        
        # Start background tasks
        self.processor_task = asyncio.create_task(self._process_queues())
        self.cleanup_task = asyncio.create_task(self._cleanup_results())
        
        logger.info("Queue broker started")
    
    async def stop(self):
        """Stop the queue broker"""
        # Cancel active tasks
        for task_id, task in self.active_tasks.items():
            task.cancel()
        
        # Cancel background tasks
        if self.processor_task:
            self.processor_task.cancel()
        if self.cleanup_task:
            self.cleanup_task.cancel()
        
        logger.info("Queue broker stopped")
    
    async def enqueue(
        self,
        agent_type: str,
        action: str,
        payload: Dict[str, Any],
        context: Dict[str, Any] = None,
        priority: Priority = Priority.NORMAL,
        timeout: int = 30,
        callback: Optional[Callable] = None
    ) -> str:
        """Enqueue a task for execution"""
        # Create queue for agent if needed
        if agent_type not in self.queues:
            self.queues[agent_type] = TaskQueue()
            self.agent_task_count[agent_type] = 0
        
        # Create task
        task = QueuedTask(
            priority=priority,
            agent_type=agent_type,
            action=action,
            payload=payload,
            context=context or {},
            timeout=timeout,
            callback=callback
        )
        
        # Add to queue
        await self.queues[agent_type].put(task)
        self.stats["total_enqueued"] += 1
        
        logger.debug(f"Enqueued task {task.task_id} for {agent_type}")
        
        return task.task_id
    
    async def get_result(self, task_id: str, timeout: int = 30) -> Optional[Any]:
        """Get result for a task, waiting if necessary"""
        start_time = asyncio.get_event_loop().time()
        
        while True:
            # Check if result is available
            if task_id in self.results:
                result = self.results[task_id]
                # Remove from results if it's final
                if isinstance(result, dict) and result.get("status") in ["completed", "failed", "timeout", "cancelled"]:
                    del self.results[task_id]
                return result
            
            # Check timeout
            if asyncio.get_event_loop().time() - start_time > timeout:
                raise TimeoutError(f"Timeout waiting for result of task {task_id}")
            
            # Wait a bit before checking again
            await asyncio.sleep(0.1)
    
    async def cancel_task(self, task_id: str) -> bool:
        """Cancel a task"""
        # Cancel if running
        if task_id in self.active_tasks:
            self.active_tasks[task_id].cancel()
            return True
        
        # Remove from queue if queued
        for queue in self.queues.values():
            if await queue.remove(task_id):
                self.stats["total_cancelled"] += 1
                self.results[task_id] = {
                    "status": "cancelled",
                    "task_id": task_id
                }
                return True
        
        return False
    
    async def get_status(self, task_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a task"""
        # Check active tasks
        if task_id in self.active_tasks:
            return {"status": "running", "task_id": task_id}
        
        # Check results
        if task_id in self.results:
            return self.results[task_id]
        
        # Check queues
        for agent_type, queue in self.queues.items():
            if task_id in queue.task_map:
                task = queue.task_map[task_id]
                return task.to_dict()
        
        return None
    
    async def get_queue_stats(self) -> Dict[str, Any]:
        """Get queue statistics"""
        queue_sizes = {
            agent_type: queue.size()
            for agent_type, queue in self.queues.items()
        }
        
        return {
            **self.stats,
            "active_tasks": len(self.active_tasks),
            "queued_tasks": sum(queue_sizes.values()),
            "queue_sizes": queue_sizes,
            "agent_task_count": self.agent_task_count.copy()
        }
    
    async def _process_queues(self):
        """Background task to process queues"""
        while True:
            try:
                # Check if we can start more tasks
                if len(self.active_tasks) >= self.max_concurrent:
                    await asyncio.sleep(0.1)
                    continue
                
                # Find next task to execute
                next_task = await self._get_next_task()
                if not next_task:
                    await asyncio.sleep(0.1)
                    continue
                
                # Execute task
                asyncio.create_task(self._execute_task(next_task))
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in queue processor: {e}")
                await asyncio.sleep(1)
    
    async def _get_next_task(self) -> Optional[QueuedTask]:
        """Get next task to execute based on priority and limits"""
        best_task = None
        best_agent = None
        
        for agent_type, queue in self.queues.items():
            # Check agent limit
            if self.agent_task_count.get(agent_type, 0) >= self.max_per_agent:
                continue
            
            # Peek at next task
            if queue.queue:
                task = queue.queue[0]  # Peek without removing
                if not best_task or task < best_task:
                    best_task = task
                    best_agent = agent_type
        
        # Get the best task
        if best_agent:
            return await self.queues[best_agent].get()
        
        return None
    
    async def _execute_task(self, task: QueuedTask):
        """Execute a single task"""
        task_id = task.task_id
        agent_type = task.agent_type
        
        # Update task status
        task.status = TaskStatus.RUNNING
        task.started_at = datetime.now()
        
        # Track active task
        self.agent_task_count[agent_type] = self.agent_task_count.get(agent_type, 0) + 1
        
        try:
            # Create execution task with timeout
            exec_task = asyncio.create_task(self.executor(task))
            self.active_tasks[task_id] = exec_task
            
            # Wait with timeout
            result = await asyncio.wait_for(exec_task, timeout=task.timeout)
            
            # Update task status
            task.status = TaskStatus.COMPLETED
            task.completed_at = datetime.now()
            task.result = result
            
            # Store result
            self.results[task_id] = {
                "status": "completed",
                "task_id": task_id,
                "result": result,
                "execution_time": (task.completed_at - task.started_at).total_seconds()
            }
            
            self.stats["total_completed"] += 1
            
            # Execute callback if provided
            if task.callback:
                await task.callback(result)
            
            logger.debug(f"Task {task_id} completed successfully")
            
        except asyncio.TimeoutError:
            task.status = TaskStatus.TIMEOUT
            task.error = f"Task timed out after {task.timeout} seconds"
            
            self.results[task_id] = {
                "status": "timeout",
                "task_id": task_id,
                "error": task.error
            }
            
            self.stats["total_timeout"] += 1
            logger.warning(f"Task {task_id} timed out")
            
            # Retry if possible
            if task.retries < task.max_retries:
                task.retries += 1
                task.status = TaskStatus.QUEUED
                await self.queues[agent_type].put(task)
                logger.info(f"Retrying task {task_id} (attempt {task.retries})")
        
        except asyncio.CancelledError:
            task.status = TaskStatus.CANCELLED
            self.stats["total_cancelled"] += 1
            raise
        
        except Exception as e:
            task.status = TaskStatus.FAILED
            task.error = str(e)
            
            self.results[task_id] = {
                "status": "failed",
                "task_id": task_id,
                "error": task.error
            }
            
            self.stats["total_failed"] += 1
            logger.error(f"Task {task_id} failed: {e}")
            
            # Retry if possible
            if task.retries < task.max_retries:
                task.retries += 1
                task.status = TaskStatus.QUEUED
                await self.queues[agent_type].put(task)
                logger.info(f"Retrying task {task_id} (attempt {task.retries})")
        
        finally:
            # Clean up
            self.agent_task_count[agent_type] -= 1
            if task_id in self.active_tasks:
                del self.active_tasks[task_id]
    
    async def _cleanup_results(self):
        """Periodically clean up old results"""
        while True:
            try:
                await asyncio.sleep(60)  # Check every minute
                
                now = datetime.now()
                expired = []
                
                for task_id, result in self.results.items():
                    if isinstance(result, dict):
                        # Check if result is old
                        if "timestamp" in result:
                            timestamp = datetime.fromisoformat(result["timestamp"])
                            if now - timestamp > self.result_ttl:
                                expired.append(task_id)
                
                for task_id in expired:
                    del self.results[task_id]
                
                if expired:
                    logger.debug(f"Cleaned up {len(expired)} expired results")
            
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in result cleanup: {e}")

# Global queue broker instance
queue_broker = QueueBroker()