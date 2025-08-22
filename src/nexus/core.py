"""
Core Nexus - Central Orchestrator for BMAD + Gemini Enterprise Architect
Manages agent spawning, communication, resource management, and metrics
"""

import asyncio
import json
import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
import multiprocessing as mp
from concurrent.futures import ProcessPoolExecutor, ThreadPoolExecutor
from pathlib import Path


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class AgentState(Enum):
    """Agent lifecycle states"""
    IDLE = "idle"
    INITIALIZING = "initializing"
    RUNNING = "running"
    WAITING = "waiting"
    COMPLETED = "completed"
    FAILED = "failed"


class ResourceType(Enum):
    """Types of resources agents can request"""
    FILE = "file"
    API = "api"
    DATABASE = "database"
    KNOWLEDGE = "knowledge"
    AGENT = "agent"


@dataclass
class ResourceRequest:
    """Request for a resource from an agent"""
    agent_id: str
    resource_type: ResourceType
    resource_path: str
    priority: str = "medium"  # low, medium, high, critical
    timestamp: datetime = field(default_factory=datetime.now)
    
    
@dataclass
class TeachablePattern:
    """Pattern that can be shared across agents"""
    pattern_name: str
    pattern_type: str  # scaling, security, architecture, performance
    context: Dict[str, Any]
    implementation: str
    success_metrics: Dict[str, Any]
    discovered_by: str
    timestamp: datetime = field(default_factory=datetime.now)


class CommunicationBus:
    """Inter-agent communication system"""
    
    def __init__(self):
        self.messages = asyncio.Queue()
        self.subscribers = {}
        
    async def publish(self, topic: str, message: Dict[str, Any]):
        """Publish message to a topic"""
        await self.messages.put({
            'topic': topic,
            'message': message,
            'timestamp': datetime.now().isoformat()
        })
        
        # Notify subscribers
        if topic in self.subscribers:
            for subscriber in self.subscribers[topic]:
                await subscriber(message)
    
    def subscribe(self, topic: str, callback):
        """Subscribe to a topic"""
        if topic not in self.subscribers:
            self.subscribers[topic] = []
        self.subscribers[topic].append(callback)
        
    async def get_message(self) -> Dict[str, Any]:
        """Get next message from the bus"""
        return await self.messages.get()


class ResourceManager:
    """Manage resource allocation and conflict resolution"""
    
    def __init__(self):
        self.resource_locks = {}
        self.request_queue = asyncio.Queue()
        self.resource_owners = {}
        
    async def request_resource(self, request: ResourceRequest) -> bool:
        """Request access to a resource"""
        resource_key = f"{request.resource_type.value}:{request.resource_path}"
        
        # Check if resource is locked
        if resource_key in self.resource_locks:
            if request.priority == "critical":
                # Critical requests can preempt
                await self._preempt_resource(resource_key, request)
                return True
            else:
                # Queue the request
                await self.request_queue.put(request)
                return False
        else:
            # Grant immediate access
            self.resource_locks[resource_key] = request.agent_id
            self.resource_owners[resource_key] = request
            return True
    
    async def release_resource(self, agent_id: str, resource_type: ResourceType, resource_path: str):
        """Release a resource"""
        resource_key = f"{resource_type.value}:{resource_path}"
        
        if resource_key in self.resource_locks and self.resource_locks[resource_key] == agent_id:
            del self.resource_locks[resource_key]
            del self.resource_owners[resource_key]
            
            # Process queued requests
            await self._process_queued_requests(resource_key)
    
    async def _preempt_resource(self, resource_key: str, request: ResourceRequest):
        """Preempt a resource for critical request"""
        current_owner = self.resource_owners.get(resource_key)
        if current_owner:
            logger.warning(f"Preempting resource {resource_key} from {current_owner.agent_id} for {request.agent_id}")
        
        self.resource_locks[resource_key] = request.agent_id
        self.resource_owners[resource_key] = request
    
    async def _process_queued_requests(self, resource_key: str):
        """Process queued requests for a released resource"""
        # Check queue for requests for this resource
        # This is simplified - real implementation would be more sophisticated
        if not self.request_queue.empty():
            request = await self.request_queue.get()
            await self.request_resource(request)


class DependencyGraph:
    """Track and analyze code dependencies"""
    
    def __init__(self):
        self.graph = {}
        self.critical_paths = set()
        
    def add_dependency(self, source: str, target: str, weight: float = 1.0):
        """Add a dependency relationship"""
        if source not in self.graph:
            self.graph[source] = {}
        self.graph[source][target] = weight
        
    def find_critical_paths(self) -> List[List[str]]:
        """Find critical dependency paths that cannot break"""
        paths = []
        
        # Find nodes with high fan-in (many dependencies)
        fan_in = {}
        for source in self.graph:
            for target in self.graph[source]:
                fan_in[target] = fan_in.get(target, 0) + 1
        
        # Mark as critical if fan-in > threshold
        for node, count in fan_in.items():
            if count > 3:  # Configurable threshold
                self.critical_paths.add(node)
                paths.append(self._trace_path_to_node(node))
        
        return paths
    
    def _trace_path_to_node(self, target: str) -> List[str]:
        """Trace all paths leading to a node"""
        paths = []
        for source in self.graph:
            if target in self.graph.get(source, {}):
                paths.append(source)
        return paths
    
    def get_reuse_opportunities(self) -> Dict[str, List[str]]:
        """Identify components that can be reused"""
        reuse_map = {}
        
        # Find commonly used components
        usage_count = {}
        for source in self.graph:
            for target in self.graph[source]:
                usage_count[target] = usage_count.get(target, 0) + 1
        
        # Recommend reuse for frequently used components
        for component, count in usage_count.items():
            if count > 1:
                reuse_map[component] = self._trace_path_to_node(component)
        
        return reuse_map


class DORAMetricsCollector:
    """Collect and track DORA metrics"""
    
    def __init__(self):
        self.metrics = {
            'deployment_frequency': [],
            'lead_time': [],
            'mttr': [],
            'change_failure_rate': []
        }
        self.deployments = []
        self.incidents = []
        
    def track_deployment(self, deployment_id: str, lead_time_hours: float):
        """Track a deployment"""
        self.deployments.append({
            'id': deployment_id,
            'timestamp': datetime.now(),
            'lead_time': lead_time_hours
        })
        
        self.metrics['deployment_frequency'].append(datetime.now())
        self.metrics['lead_time'].append(lead_time_hours)
        
    def track_incident(self, incident_id: str, time_to_recovery_hours: float):
        """Track an incident"""
        self.incidents.append({
            'id': incident_id,
            'timestamp': datetime.now(),
            'mttr': time_to_recovery_hours
        })
        
        self.metrics['mttr'].append(time_to_recovery_hours)
        
    def calculate_metrics(self) -> Dict[str, float]:
        """Calculate current DORA metrics"""
        now = datetime.now()
        
        # Deployment frequency (per day)
        recent_deployments = [d for d in self.metrics['deployment_frequency'] 
                            if (now - d).days <= 30]
        deployment_freq = len(recent_deployments) / 30.0 if recent_deployments else 0
        
        # Lead time (average)
        avg_lead_time = sum(self.metrics['lead_time']) / len(self.metrics['lead_time']) \
                       if self.metrics['lead_time'] else 0
        
        # MTTR (average)
        avg_mttr = sum(self.metrics['mttr']) / len(self.metrics['mttr']) \
                  if self.metrics['mttr'] else 0
        
        # Change failure rate
        total_deployments = len(self.deployments)
        failed_deployments = len([i for i in self.incidents 
                                if any(d['timestamp'] < i['timestamp'] < d['timestamp'] 
                                      for d in self.deployments)])
        
        change_failure_rate = failed_deployments / total_deployments \
                            if total_deployments > 0 else 0
        
        return {
            'deployment_frequency_per_day': deployment_freq,
            'lead_time_hours': avg_lead_time,
            'mttr_hours': avg_mttr,
            'change_failure_rate_percent': change_failure_rate * 100
        }


class AgentProcess:
    """Wrapper for an agent running in a separate process"""
    
    def __init__(self, agent_id: str, agent_type: str, config: Dict[str, Any]):
        self.agent_id = agent_id
        self.agent_type = agent_type
        self.config = config
        self.state = AgentState.IDLE
        self.process = None
        self.start_time = None
        
    async def start(self):
        """Start the agent process"""
        self.state = AgentState.INITIALIZING
        self.start_time = datetime.now()
        
        # In real implementation, this would spawn actual process
        # For now, we'll simulate with async task
        self.state = AgentState.RUNNING
        logger.info(f"Started agent {self.agent_id} of type {self.agent_type}")
        
    async def stop(self):
        """Stop the agent process"""
        self.state = AgentState.COMPLETED
        logger.info(f"Stopped agent {self.agent_id}")
        
    def get_status(self) -> Dict[str, Any]:
        """Get agent status"""
        runtime = (datetime.now() - self.start_time).total_seconds() \
                 if self.start_time else 0
        
        return {
            'agent_id': self.agent_id,
            'agent_type': self.agent_type,
            'state': self.state.value,
            'runtime_seconds': runtime
        }


class CoreNexus:
    """
    Central orchestrator for all agents
    Manages spawning, communication, resources, and metrics
    """
    
    def __init__(self, config_path: Optional[str] = None):
        # Load configuration
        self.config = self._load_config(config_path)
        
        # Initialize components
        self.agents = {}
        self.dependency_graph = DependencyGraph()
        self.resource_manager = ResourceManager()
        self.communication_bus = CommunicationBus()
        self.metrics_collector = DORAMetricsCollector()
        
        # Executor for parallel operations
        self.executor = ThreadPoolExecutor(max_workers=10)
        
        # Pattern library for teaching
        self.pattern_library = []
        
        logger.info("Core Nexus initialized")
        
    def _load_config(self, config_path: Optional[str]) -> Dict[str, Any]:
        """Load nexus configuration"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                return json.load(f)
        
        # Default configuration
        return {
            'max_agents': 20,
            'default_timeout': 300,
            'enable_teaching': True,
            'enable_challenging': True,
            'metrics_interval': 60
        }
    
    async def spawn_agent(self, agent_type: str, config: Dict[str, Any]) -> str:
        """Spawn a new agent in parallel session"""
        agent_id = f"{agent_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # Create agent process
        agent = AgentProcess(agent_id, agent_type, config)
        await agent.start()
        
        # Register agent
        self.agents[agent_id] = agent
        
        # Subscribe agent to relevant topics
        await self._setup_agent_subscriptions(agent_id, agent_type)
        
        logger.info(f"Spawned agent {agent_id} of type {agent_type}")
        return agent_id
    
    async def _setup_agent_subscriptions(self, agent_id: str, agent_type: str):
        """Setup communication subscriptions for an agent"""
        # Subscribe to broadcast topics
        self.communication_bus.subscribe('patterns', 
                                       lambda msg: self._handle_pattern_broadcast(agent_id, msg))
        
        # Subscribe to agent-specific topics
        self.communication_bus.subscribe(f'agent_{agent_id}',
                                       lambda msg: self._handle_agent_message(agent_id, msg))
    
    async def handle_resource_request(self, agent_id: str, resource_type: str, 
                                     resource_path: str, priority: str = "medium") -> bool:
        """Handle resource request from an agent"""
        request = ResourceRequest(
            agent_id=agent_id,
            resource_type=ResourceType[resource_type.upper()],
            resource_path=resource_path,
            priority=priority
        )
        
        granted = await self.resource_manager.request_resource(request)
        
        if granted:
            logger.info(f"Granted resource {resource_type}:{resource_path} to {agent_id}")
        else:
            logger.info(f"Queued resource request from {agent_id} for {resource_type}:{resource_path}")
        
        return granted
    
    async def broadcast_pattern(self, pattern: TeachablePattern):
        """Broadcast a learned pattern to all agents"""
        self.pattern_library.append(pattern)
        
        await self.communication_bus.publish('patterns', {
            'pattern': pattern.__dict__,
            'action': 'new_pattern'
        })
        
        logger.info(f"Broadcast pattern {pattern.pattern_name} to all agents")
    
    def _handle_pattern_broadcast(self, agent_id: str, message: Dict[str, Any]):
        """Handle pattern broadcast for an agent"""
        logger.info(f"Agent {agent_id} received pattern: {message['pattern']['pattern_name']}")
    
    def _handle_agent_message(self, agent_id: str, message: Dict[str, Any]):
        """Handle direct message to an agent"""
        logger.info(f"Agent {agent_id} received message: {message}")
    
    async def orchestrate_workflow(self, workflow_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate a complete workflow"""
        logger.info(f"Starting workflow: {workflow_type}")
        
        if workflow_type == "planning":
            return await self._orchestrate_planning_workflow(context)
        elif workflow_type == "development":
            return await self._orchestrate_development_workflow(context)
        elif workflow_type == "architect":
            return await self._orchestrate_architect_workflow(context)
        elif workflow_type == "guardian":
            return await self._orchestrate_guardian_workflow(context)
        else:
            raise ValueError(f"Unknown workflow type: {workflow_type}")
    
    async def _orchestrate_planning_workflow(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate BMAD planning workflow"""
        results = {}
        
        # Step 1: Analyst phase
        analyst_id = await self.spawn_agent("analyst", context)
        results['project_brief'] = await self._execute_agent_task(analyst_id, "create_project_brief", context)
        
        # Step 2: PM phase
        pm_id = await self.spawn_agent("pm", context)
        results['prd'] = await self._execute_agent_task(pm_id, "create_prd", results['project_brief'])
        
        # Step 3: Architecture phase
        architect_id = await self.spawn_agent("architect", context)
        results['architecture'] = await self._execute_agent_task(architect_id, "design_architecture", results['prd'])
        
        # Step 4: QA assessment
        qa_id = await self.spawn_agent("qa", context)
        results['risk_assessment'] = await self._execute_agent_task(qa_id, "assess_risks", results['architecture'])
        
        # Step 5: PO validation
        po_id = await self.spawn_agent("po", context)
        results['validation'] = await self._execute_agent_task(po_id, "validate_alignment", results)
        
        return results
    
    async def _orchestrate_development_workflow(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate BMAD development workflow with Scout pre-check"""
        results = {}
        
        # Step 1: SM review
        sm_id = await self.spawn_agent("sm", context)
        results['story_assignment'] = await self._execute_agent_task(sm_id, "review_story", context)
        
        # Step 2: Scout pre-check for code duplication
        scout_id = await self.spawn_agent("scout", context)
        scout_results = await self._execute_agent_task(scout_id, "analyze_codebase", context)
        results['reuse_map'] = scout_results
        
        # Step 3: Conditional Development based on Scout's findings
        # This is a critical change to make the workflow intelligent
        if scout_results.get("result") == "significant_duplication_found":
            logger.warning("Scout found significant duplication. Halting development workflow.")
            results['implementation'] = {
                'status': 'halted',
                'reason': 'Significant code duplication detected by Scout.',
                'details': scout_results
            }
        else:
            # Proceed with development if no significant duplication is found
            dev_id = await self.spawn_agent("dev", context)
            results['implementation'] = await self._execute_agent_task(
                dev_id, 
                "implement_story", 
                {**context, 'reuse_map': results['reuse_map']}
            )
            
            # Step 4: Testing (only if development occurred)
            qa_id = await self.spawn_agent("qa", context)
            results['test_results'] = await self._execute_agent_task(
                qa_id, 
                "test_implementation", 
                results['implementation']
            )
            
        return results

    async def _orchestrate_architect_workflow(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate architect analysis workflow"""
        results = {}
        
        # Step 1: Spawn architect agent
        architect_id = await self.spawn_agent("architect", context)
        
        # Step 2: Execute design analysis task
        results['design_recommendations'] = await self._execute_agent_task(
            architect_id, 
            "provide_design_recommendations", 
            context
        )
        
        return results

    async def _orchestrate_guardian_workflow(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Orchestrate guardian security scan workflow"""
        results = {}
        
        # Step 1: Spawn guardian agent
        guardian_id = await self.spawn_agent("guardian", context)
        
        # Step 2: Execute project scan task
        results['scan_report'] = await self._execute_agent_task(
            guardian_id, 
            "scan_project", 
            context
        )
        
        return results
    
    async def _execute_agent_task(self, agent_id: str, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a task on an agent"""
        # In real implementation, this would communicate with actual agent process
        # For now, return simulated result
        logger.info(f"Agent {agent_id} executing task: {task}")
        
        # Simulate task execution
        await asyncio.sleep(0.5)
        
        return {
            'status': 'completed',
            'task': task,
            'agent': agent_id,
            'result': f"Result of {task}",
            'timestamp': datetime.now().isoformat()
        }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get current system metrics"""
        return {
            'agents': {
                'total': len(self.agents),
                'running': len([a for a in self.agents.values() if a.state == AgentState.RUNNING]),
                'completed': len([a for a in self.agents.values() if a.state == AgentState.COMPLETED])
            },
            'patterns': len(self.pattern_library),
            'dora_metrics': self.metrics_collector.calculate_metrics(),
            'resource_locks': len(self.resource_manager.resource_locks)
        }
    
    def get_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        return {
            'nexus': 'operational',
            'agents': [agent.get_status() for agent in self.agents.values()],
            'metrics': self.get_metrics(),
            'timestamp': datetime.now().isoformat()
        }
    
    async def shutdown(self):
        """Shutdown the nexus and all agents"""
        logger.info("Shutting down Core Nexus")
        
        # Stop all agents
        for agent in self.agents.values():
            await agent.stop()
        
        # Cleanup
        self.executor.shutdown(wait=True)
        
        logger.info("Core Nexus shutdown complete")