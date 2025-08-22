"""
FastAPI Server for BMAD Agent System
Provides REST and WebSocket endpoints for TypeScript CLI to interact with Python agents
"""

from fastapi import FastAPI, WebSocket, HTTPException, Depends, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse
from pydantic import BaseModel, Field
from typing import Dict, Any, Optional, List, AsyncGenerator
import asyncio
import json
import logging
import uuid
import time
from datetime import datetime
from contextlib import asynccontextmanager
import sys
import os
from pathlib import Path

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.unified_agent_base import UnifiedAgent, AgentConfig
from agents.enhanced.analyst import EnhancedAnalyst
from agents.enhanced.pm import EnhancedPM
from agents.enhanced.architect import EnhancedArchitect
from agents.enhanced.developer import EnhancedDeveloper
from agents.enhanced.qa import EnhancedQA
from agents.enhanced.scout import EnhancedScout
from agents.enhanced.po import EnhancedPO
from nexus.core import CoreNexus
from scout.indexer import initialize_indexer, get_indexer
from rag_endpoints import router as rag_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Import monitoring components
try:
    from prometheus_client import Counter, Histogram, Gauge, Info, generate_latest, CONTENT_TYPE_LATEST
    from prometheus_client.core import CollectorRegistry
    PROMETHEUS_AVAILABLE = True
except ImportError:
    PROMETHEUS_AVAILABLE = False
    logger.warning("Prometheus client not available. Metrics collection disabled.")

# Import OpenTelemetry tracing
try:
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'monitoring', 'telemetry'))
    from tracing import initialize_tracing, trace_agent_request, get_tracer
    from custom_metrics import metrics_collector
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False
    logger.warning("OpenTelemetry tracing not available. Distributed tracing disabled.")

# Import DORA metrics
try:
    from monitoring.dora_metrics import router as dora_router, DORAMetricsTracker, tracker
    from monitoring.dashboard import create_dashboard_app
    DORA_AVAILABLE = True
except ImportError:
    DORA_AVAILABLE = False
    logger.warning("DORA metrics not available.")

# Import structured logging
try:
    sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 'monitoring', 'logging'))
    from structured_logging import AgentLogger, agent_logger, log_performance
    STRUCTURED_LOGGING_AVAILABLE = True
except ImportError:
    STRUCTURED_LOGGING_AVAILABLE = False
    logger.warning("Structured logging not available. Using standard logging.")

# Configure logging
if STRUCTURED_LOGGING_AVAILABLE:
    logger = AgentLogger("agent-server")
else:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Request/Response Models
class AgentRequest(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str = Field(..., description="Agent type: analyst, pm, architect, developer, qa, scout, po")
    action: str = Field(..., description="Action to perform")
    payload: Dict[str, Any] = Field(default_factory=dict)
    context: Dict[str, Any] = Field(default_factory=dict)
    timeout: Optional[int] = Field(default=30, description="Timeout in seconds")
    priority: Optional[str] = Field(default="normal", description="Priority: low, normal, high, critical")

class AgentResponse(BaseModel):
    id: str
    success: bool
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
class HealthStatus(BaseModel):
    status: str
    agents: Dict[str, str]
    uptime: float
    version: str = "1.0.0"

class SystemMetrics(BaseModel):
    total_requests: int
    active_requests: int
    average_response_time: float
    agent_metrics: Dict[str, Dict[str, Any]]
    memory_usage: float
    cpu_usage: float

# Agent Registry
class AgentRegistry:
    """Manages agent instances and lifecycle"""
    
    def __init__(self):
        self.agents: Dict[str, UnifiedAgent] = {}
        self.nexus: Optional[CoreNexus] = None
        self._initialized = False
        
    async def initialize(self):
        """Initialize all agents and nexus"""
        if self._initialized:
            return
            
        try:
            # Initialize Nexus
            self.nexus = CoreNexus()
            
            # Initialize enhanced agents
            self.agents = {
                'analyst': EnhancedAnalyst(self._create_config('analyst')),
                'pm': EnhancedPM(self._create_config('pm')),
                'architect': EnhancedArchitect(self._create_config('architect')),
                'developer': EnhancedDeveloper(self._create_config('developer')),
                'qa': EnhancedQA(self._create_config('qa')),
                'scout': EnhancedScout(self._create_config('scout')),
                'po': EnhancedPO(self._create_config('po'))
            }
            
            # Spawn agents through the nexus
            for agent_type, agent in self.agents.items():
                await self.nexus.spawn_agent(agent_type, agent.config.__dict__)
            
            self._initialized = True
            logger.info(f"Initialized {len(self.agents)} agents")
            
        except Exception as e:
            logger.error(f"Failed to initialize agents: {e}")
            raise
    
    def _create_config(self, agent_type: str) -> AgentConfig:
        """Create configuration for an agent by loading its YAML file"""
        config_path = Path(f".bmad-core/agents/{agent_type}.yaml")
        if not config_path.exists():
            # Fallback for non-standard agent types or testing
            return AgentConfig(
                id=agent_type,
                name=agent_type.capitalize(),
                title=f"{agent_type.capitalize()} Agent",
                icon="🤖",
                when_to_use=f"Use for {agent_type} tasks.",
                persona={'role': f'The {agent_type} agent'},
                commands=[],
                dependencies={}
            )
        
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f)
            # The actual agent config is nested under the 'agent' key
            agent_data = config_data.get('agent', {})
            
            return AgentConfig(
                id=agent_data.get('id', agent_type),
                name=agent_data.get('name', agent_type.capitalize()),
                title=agent_data.get('title', f"{agent_type.capitalize()} Agent"),
                icon=agent_data.get('icon', '🤖'),
                when_to_use=agent_data.get('whenToUse', f"Use for {agent_type} tasks."),
                persona=config_data.get('persona', {}),
                commands=config_data.get('commands', []),
                dependencies=config_data.get('dependencies', {}),
                customization=agent_data.get('customization')
            )
    
    def get_agent(self, agent_type: str) -> Optional[UnifiedAgent]:
        """Get an agent instance"""
        return self.agents.get(agent_type)
    
    def get_status(self) -> Dict[str, str]:
        """Get status of all agents"""
        return {
            agent_type: "active" if agent else "inactive"
            for agent_type, agent in self.agents.items()
        }

# Global instances
agent_registry = AgentRegistry()
metrics_tracker = {
    'total_requests': 0,
    'active_requests': 0,
    'response_times': [],
    'agent_requests': {}
}
app_start_time = datetime.now()

# Initialize Prometheus metrics if available
if PROMETHEUS_AVAILABLE:
    # Create custom registry for agent server metrics
    prometheus_registry = CollectorRegistry()
    
    # HTTP request metrics
    http_requests_total = Counter(
        'gemini_http_requests_total',
        'Total HTTP requests',
        ['method', 'endpoint', 'status_code'],
        registry=prometheus_registry
    )
    
    http_request_duration_seconds = Histogram(
        'gemini_http_request_duration_seconds',
        'HTTP request duration in seconds',
        ['method', 'endpoint'],
        buckets=[0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
        registry=prometheus_registry
    )
    
    # Agent-specific metrics
    agent_requests_total = Counter(
        'gemini_agent_requests_total',
        'Total agent requests',
        ['agent_type', 'action', 'status'],
        registry=prometheus_registry
    )
    
    agent_response_time_seconds = Histogram(
        'gemini_agent_response_time_seconds',
        'Agent response time in seconds',
        ['agent_type', 'action'],
        buckets=[0.1, 0.25, 0.5, 1, 2.5, 5, 10, 25, 50, 100],
        registry=prometheus_registry
    )
    
    agent_active_sessions = Gauge(
        'gemini_agent_active_sessions',
        'Number of active agent sessions',
        ['agent_type'],
        registry=prometheus_registry
    )
    
    agent_queue_size = Gauge(
        'gemini_agent_queue_size',
        'Number of requests in agent queue',
        ['agent_type'],
        registry=prometheus_registry
    )
    
    # WebSocket metrics
    websocket_connections_total = Counter(
        'gemini_websocket_connections_total',
        'Total WebSocket connections',
        ['status'],
        registry=prometheus_registry
    )
    
    websocket_active_connections = Gauge(
        'gemini_websocket_active_connections',
        'Number of active WebSocket connections',
        registry=prometheus_registry
    )
    
    # Application info
    app_info = Info(
        'gemini_app_info',
        'Application information',
        registry=prometheus_registry
    )
    app_info.info({
        'version': '1.0.0',
        'service': 'agent-server',
        'environment': os.getenv('ENVIRONMENT', 'development')
    })
    
    # System metrics
    system_memory_usage_bytes = Gauge(
        'gemini_system_memory_usage_bytes',
        'System memory usage in bytes',
        registry=prometheus_registry
    )
    
    system_cpu_usage_percent = Gauge(
        'gemini_system_cpu_usage_percent',
        'System CPU usage percentage',
        registry=prometheus_registry
    )
    
else:
    # Create dummy metrics if Prometheus not available
    prometheus_registry = None
    http_requests_total = None
    http_request_duration_seconds = None
    agent_requests_total = None
    agent_response_time_seconds = None
    agent_active_sessions = None
    agent_queue_size = None
    websocket_connections_total = None
    websocket_active_connections = None
    system_memory_usage_bytes = None
    system_cpu_usage_percent = None

# Initialize tracing if available
if TRACING_AVAILABLE:
    tracer = initialize_tracing("gemini-agent-server", "1.0.0")
    logger.info("OpenTelemetry tracing initialized")
else:
    tracer = None

# Metrics collection functions
def collect_system_metrics():
    """Collect system metrics if monitoring is available"""
    if PROMETHEUS_AVAILABLE:
        try:
            import psutil
            process = psutil.Process()
            
            # Memory usage
            memory_usage = process.memory_info().rss
            system_memory_usage_bytes.set(memory_usage)
            
            # CPU usage
            cpu_usage = process.cpu_percent()
            system_cpu_usage_percent.set(cpu_usage)
            
        except Exception as e:
            logger.warning(f"Failed to collect system metrics: {e}")

# Background task for metrics collection
async def periodic_metrics_collection():
    """Periodically collect system metrics"""
    while True:
        try:
            collect_system_metrics()
            
            # Update agent session counts
            if PROMETHEUS_AVAILABLE:
                for agent_type in agent_registry.agents.keys():
                    # This would be updated by actual session tracking
                    agent_active_sessions.labels(agent_type=agent_type).set(
                        metrics_tracker['agent_requests'].get(agent_type, {}).get('active_sessions', 0)
                    )
                    agent_queue_size.labels(agent_type=agent_type).set(
                        metrics_tracker['agent_requests'].get(agent_type, {}).get('queue_size', 0)
                    )
            
            await asyncio.sleep(30)  # Collect every 30 seconds
            
        except Exception as e:
            logger.error(f"Error in periodic metrics collection: {e}")
            await asyncio.sleep(30)

# Metrics middleware
class MetricsMiddleware:
    """Middleware to collect HTTP request metrics"""
    
    def __init__(self, app):
        self.app = app
    
    async def __call__(self, scope, receive, send):
        if scope["type"] == "http" and PROMETHEUS_AVAILABLE:
            method = scope["method"]
            path = scope["path"]
            
            # Skip metrics endpoint to avoid recursion
            if path == "/metrics":
                await self.app(scope, receive, send)
                return
            
            start_time = time.time()
            
            # Track the response
            async def send_wrapper(message):
                if message["type"] == "http.response.start":
                    status_code = message["status"]
                    duration = time.time() - start_time
                    
                    # Record metrics
                    http_requests_total.labels(
                        method=method,
                        endpoint=path,
                        status_code=status_code
                    ).inc()
                    
                    http_request_duration_seconds.labels(
                        method=method,
                        endpoint=path
                    ).observe(duration)
                
                await send(message)
            
            await self.app(scope, receive, send_wrapper)
        else:
            await self.app(scope, receive, send)

# Import and setup security
try:
    from security.middleware import setup_security_middleware
    from api.auth_routes import router as auth_router
    from security.auth import auth_manager
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False
    logger.warning("Security modules not available.")

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifecycle"""
    # Startup
    logger.info("Starting BMAD Agent Server...")
    await agent_registry.initialize()
    
    # Initialize Scout indexer
    project_root = os.environ.get('BMAD_PROJECT_ROOT', os.getcwd())
    indexer = initialize_indexer(project_root)
    logger.info(f"Scout indexer initialized for {project_root}")
    
    # Initialize security system
    if SECURITY_AVAILABLE:
        try:
            await auth_manager.initialize()
            logger.info("Authentication system initialized")
        except Exception as e:
            logger.error(f"Failed to initialize authentication: {e}")
    
    # Initialize DORA metrics
    if DORA_AVAILABLE:
        try:
            await tracker.initialize()
            logger.info("DORA metrics tracker initialized")
        except Exception as e:
            logger.error(f"Failed to initialize DORA metrics: {e}")
    
    # Start background full indexing
    indexer.full_index()
    
    # Start background metrics collection
    metrics_task = asyncio.create_task(periodic_metrics_collection())
    
    logger.info("BMAD Agent Server started successfully")
    
    yield
    
    # Shutdown
    logger.info("Shutting down BMAD Agent Server...")
    
    # Cancel metrics collection
    metrics_task.cancel()
    try:
        await metrics_task
    except asyncio.CancelledError:
        pass
    
    indexer = get_indexer()
    if indexer:
        indexer.stop()
        logger.info("Scout indexer stopped")

# Create FastAPI app
app = FastAPI(
    title="BMAD Agent Server",
    description="Agent orchestration server for Gemini Enterprise Architect",
    version="1.0.0",
    lifespan=lifespan
)

# Setup security middleware
if SECURITY_AVAILABLE:
    setup_security_middleware(app)
    logger.info("Security middleware configured")

# Add metrics middleware
if PROMETHEUS_AVAILABLE:
    app.add_middleware(MetricsMiddleware)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:*", "https://*.gemini.ai"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import and setup security
try:
    from security.middleware import setup_security_middleware
    from api.auth_routes import router as auth_router
    from security.auth import auth_manager
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False
    logger.warning("Security modules not available.")

# Include routers
app.include_router(rag_router)

# Include DORA metrics router if available
if DORA_AVAILABLE:
    app.include_router(dora_router)
    logger.info("DORA metrics endpoints enabled")

# Include authentication router if available
if SECURITY_AVAILABLE:
    app.include_router(auth_router)
    logger.info("Authentication endpoints enabled")

# Request ID middleware
@app.middleware("http")
async def add_request_id(request, call_next):
    """Add request ID to all requests"""
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id
    return response

# Endpoints
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "service": "BMAD Agent Server",
        "version": "1.0.0",
        "status": "running",
        "documentation": "/docs"
    }

@app.get("/api/v1/health", response_model=HealthStatus)
async def health_check():
    """Health check endpoint"""
    uptime = (datetime.now() - app_start_time).total_seconds()
    return HealthStatus(
        status="healthy",
        agents=agent_registry.get_status(),
        uptime=uptime
    )

@app.get("/metrics", response_class=PlainTextResponse)
async def prometheus_metrics():
    """Prometheus metrics endpoint"""
    if PROMETHEUS_AVAILABLE and prometheus_registry:
        return generate_latest(prometheus_registry).decode('utf-8')
    else:
        return "# Prometheus metrics not available\n"

@app.get("/api/v1/metrics", response_model=SystemMetrics)
async def get_metrics():
    """Get system metrics (legacy endpoint)"""
    import psutil
    
    process = psutil.Process()
    
    return SystemMetrics(
        total_requests=metrics_tracker['total_requests'],
        active_requests=metrics_tracker['active_requests'],
        average_response_time=sum(metrics_tracker['response_times'][-100:]) / max(1, len(metrics_tracker['response_times'][-100:])) if metrics_tracker['response_times'] else 0,
        agent_metrics=metrics_tracker['agent_requests'],
        memory_usage=process.memory_info().rss / 1024 / 1024,  # MB
        cpu_usage=process.cpu_percent()
    )

@app.get("/api/v1/scout/stats")
async def get_scout_stats():
    """Get Scout indexer statistics"""
    indexer = get_indexer()
    if not indexer:
        raise HTTPException(status_code=503, detail="Scout indexer not available")
    
    return indexer.get_stats()

@app.get("/api/v1/scout/duplicates")
async def get_duplicates(similarity_threshold: float = 0.8):
    """Get duplicate functions found by Scout"""
    indexer = get_indexer()
    if not indexer:
        raise HTTPException(status_code=503, detail="Scout indexer not available")
    
    duplicates = indexer.find_duplicates(similarity_threshold)
    return {
        'duplicates': [
            {
                'original_file': d.original_file,
                'duplicate_file': d.duplicate_file,
                'function_name': d.function_name,
                'similarity_score': d.similarity_score,
                'line_start': d.line_start,
                'line_end': d.line_end
            } for d in duplicates
        ],
        'total_count': len(duplicates),
        'similarity_threshold': similarity_threshold
    }

@app.get("/api/v1/scout/file/{file_path:path}")
async def get_file_analysis(file_path: str):
    """Get Scout analysis for a specific file"""
    indexer = get_indexer()
    if not indexer:
        raise HTTPException(status_code=503, detail="Scout indexer not available")
    
    file_info = indexer.get_file_info(file_path)
    if not file_info:
        raise HTTPException(status_code=404, detail="File not found in index")
    
    return {
        'file_path': file_info.file_path,
        'language': file_info.language,
        'size_lines': file_info.size_lines,
        'functions': file_info.functions,
        'classes': file_info.classes,
        'imports': file_info.imports,
        'patterns': file_info.patterns,
        'complexity': file_info.complexity,
        'indexed_at': file_info.indexed_at
    }

@app.post("/api/v1/scout/reindex")
async def trigger_reindex():
    """Trigger a full reindex of the codebase"""
    indexer = get_indexer()
    if not indexer:
        raise HTTPException(status_code=503, detail="Scout indexer not available")
    
    # Trigger reindex in background
    import threading
    threading.Thread(target=indexer.full_index, daemon=True).start()
    
    return {"message": "Full reindex started in background"}

async def scout_pre_check(request: AgentRequest) -> Dict[str, Any]:
    """Scout-First Architecture: Run Scout analysis before all operations"""
    indexer = get_indexer()
    if not indexer:
        return {'scout_enabled': False, 'message': 'Scout indexer not initialized'}
    
    scout_results = {
        'scout_enabled': True,
        'duplicates_found': [],
        'similar_functions': [],
        'recommendations': []
    }
    
    # Check if this is a code generation request
    if request.action in ['generate_code', 'create', 'implement', 'build']:
        # Look for existing similar functionality
        context_hints = request.payload.get('specification', '') or request.payload.get('requirements', '')
        
        if context_hints:
            # Find potentially duplicate functionality
            duplicates = indexer.find_duplicates(similarity_threshold=0.8)
            if duplicates:
                scout_results['duplicates_found'] = [
                    {
                        'original_file': d.original_file,
                        'duplicate_file': d.duplicate_file,
                        'function_name': d.function_name,
                        'similarity': d.similarity_score
                    } for d in duplicates[:5]  # Limit to top 5
                ]
                
                scout_results['recommendations'].append({
                    'type': 'duplication_warning',
                    'message': f'Found {len(duplicates)} potential duplicates. Consider reusing existing code.',
                    'action': 'Review existing implementations before creating new code'
                })
    
    return scout_results

async def get_knowledge_context(request: AgentRequest) -> Dict[str, Any]:
    """Get relevant knowledge context from RAG system"""
    try:
        from .rag_endpoints import get_rag_system
        
        rag_system = get_rag_system()
        
        # Extract query from request
        query_text = ""
        if hasattr(request.payload, 'query'):
            query_text = request.payload.query
        elif hasattr(request.payload, 'specification'):
            query_text = request.payload.specification
        elif hasattr(request.payload, 'requirements'):
            query_text = request.payload.requirements
        elif hasattr(request.payload, 'prompt'):
            query_text = request.payload.prompt
        
        if not query_text:
            return {'knowledge_enabled': False, 'message': 'No query text found'}
        
        # Query knowledge base
        from ..knowledge.rag_system import RAGQuery
        rag_query = RAGQuery(
            query=query_text,
            context=request.context or {},
            query_type='architecture' if request.type == 'architect' else 'general',
            max_context_chunks=3,  # Limit context for performance
            temperature=0.1,  # Lower temperature for more factual responses
            include_sources=True
        )
        
        rag_response = await rag_system.process_query(rag_query)
        
        return {
            'knowledge_enabled': True,
            'relevant_docs': [
                {
                    'title': source.title,
                    'service': source.service,
                    'url': source.url,
                    'snippet': source.content[:200]
                } for source in rag_response.sources[:3]
            ],
            'context_summary': rag_response.reasoning,
            'confidence': rag_response.confidence
        }
        
    except Exception as e:
        logger.warning(f"Knowledge context retrieval failed: {e}")
        return {'knowledge_enabled': False, 'error': str(e)}
    
    return {'knowledge_enabled': False}

@app.post("/api/v1/agent/request", response_model=AgentResponse)
async def handle_request(request: AgentRequest, background_tasks: BackgroundTasks):
    """Handle single agent request with Scout-First Architecture"""
    start_time = time.time()
    start_datetime = datetime.now()
    
    # Update legacy metrics tracker
    metrics_tracker['total_requests'] += 1
    metrics_tracker['active_requests'] += 1
    
    # Track agent-specific metrics
    if request.type not in metrics_tracker['agent_requests']:
        metrics_tracker['agent_requests'][request.type] = {'count': 0, 'errors': 0}
    metrics_tracker['agent_requests'][request.type]['count'] += 1
    
    # Set up structured logging context
    if STRUCTURED_LOGGING_AVAILABLE:
        logger.set_context(
            request_id=request.id,
            agent_type=request.type
        )
        logger.info(f"Agent request started: {request.action}", 
                   action=request.action, 
                   payload_size=len(str(request.payload)))
    
    # Initialize success flag
    success = False
    error_type = None
    
    try:
        # Scout-First Architecture: Run Scout pre-check (unless bypassed)
        scout_results = {}
        bypass_scout = request.context and request.context.get('bypass_scout', False)
        
        if not bypass_scout:
            scout_results = await scout_pre_check(request)
        
        # Knowledge-Augmented Architecture: Get RAG context (unless bypassed)
        knowledge_context = {}
        bypass_knowledge = request.context and request.context.get('bypass_knowledge', False)
        
        if not bypass_knowledge:
            knowledge_context = await get_knowledge_context(request)
        
        # Get the appropriate agent
        agent = agent_registry.get_agent(request.type)
        if not agent:
            raise HTTPException(status_code=404, detail=f"Agent '{request.type}' not found")
        
        # Add Scout and Knowledge results to context for agent processing
        enhanced_context = {
            **(request.context or {}), 
            'scout_results': scout_results,
            'knowledge_context': knowledge_context
        }
        
        # Process the request with tracing if available
        if TRACING_AVAILABLE:
            @trace_agent_request(request.type)
            async def process_with_tracing():
                return await agent.process_request(request.action, request.payload, enhanced_context)
            
            result = await asyncio.wait_for(
                process_with_tracing(),
                timeout=request.timeout
            )
        else:
            result = await asyncio.wait_for(
                agent.process_request(request.action, request.payload, enhanced_context),
                timeout=request.timeout
            )
        
        # Mark as successful
        success = True
        
        # Calculate response time
        response_time = time.time() - start_time
        metrics_tracker['response_times'].append(response_time)
        
        # Record Prometheus metrics
        if PROMETHEUS_AVAILABLE:
            agent_requests_total.labels(
                agent_type=request.type,
                action=request.action,
                status="success"
            ).inc()
            
            agent_response_time_seconds.labels(
                agent_type=request.type,
                action=request.action
            ).observe(response_time)
        
        # Record custom metrics if available
        if TRACING_AVAILABLE and hasattr(metrics_collector, 'record_agent_request'):
            metrics_collector.record_agent_request(
                agent_type=request.type,
                action=request.action,
                duration_seconds=response_time,
                success=True
            )
        
        # Log success
        if STRUCTURED_LOGGING_AVAILABLE:
            logger.info(f"Agent request completed: {request.action}",
                       action=request.action,
                       duration_ms=response_time * 1000,
                       success=True)
        
        return AgentResponse(
            id=request.id,
            success=True,
            result=result,
            metadata={
                'agent': request.type,
                'action': request.action,
                'response_time': response_time,
                'timestamp': start_datetime.isoformat(),
                'scout_results': scout_results,
                'knowledge_context': knowledge_context
            }
        )
        
    except asyncio.TimeoutError:
        error_type = "timeout"
        metrics_tracker['agent_requests'][request.type]['errors'] += 1
        
        # Record error metrics
        if PROMETHEUS_AVAILABLE:
            agent_requests_total.labels(
                agent_type=request.type,
                action=request.action,
                status="timeout"
            ).inc()
        
        if STRUCTURED_LOGGING_AVAILABLE:
            logger.error(f"Agent request timeout: {request.action}",
                        action=request.action,
                        timeout_seconds=request.timeout,
                        duration_ms=(time.time() - start_time) * 1000)
        
        raise HTTPException(status_code=408, detail=f"Request timed out after {request.timeout} seconds")
    
    except Exception as e:
        error_type = type(e).__name__
        metrics_tracker['agent_requests'][request.type]['errors'] += 1
        
        # Record error metrics
        if PROMETHEUS_AVAILABLE:
            agent_requests_total.labels(
                agent_type=request.type,
                action=request.action,
                status="error"
            ).inc()
        
        # Record custom metrics if available
        if TRACING_AVAILABLE and hasattr(metrics_collector, 'record_agent_request'):
            metrics_collector.record_agent_request(
                agent_type=request.type,
                action=request.action,
                duration_seconds=time.time() - start_time,
                success=False,
                error_type=error_type
            )
        
        if STRUCTURED_LOGGING_AVAILABLE:
            logger.error(f"Agent request failed: {request.action}",
                        error=e,
                        action=request.action,
                        error_type=error_type,
                        duration_ms=(time.time() - start_time) * 1000)
        else:
            logger.error(f"Error processing request {request.id}: {e}")
        
        return AgentResponse(
            id=request.id,
            success=False,
            error={
                'code': 'PROCESSING_ERROR',
                'message': str(e),
                'agent': request.type,
                'action': request.action,
                'error_type': error_type
            },
            metadata={
                'timestamp': start_datetime.isoformat(),
                'duration_ms': (time.time() - start_time) * 1000
            }
        )
    
    finally:
        metrics_tracker['active_requests'] -= 1

@app.post("/api/v1/agent/batch", response_model=List[AgentResponse])
async def handle_batch(requests: List[AgentRequest]):
    """Handle batch agent requests"""
    tasks = [handle_request(req, BackgroundTasks()) for req in requests]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Convert exceptions to error responses
    responses = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            responses.append(AgentResponse(
                id=requests[i].id,
                success=False,
                error={
                    'code': 'BATCH_ERROR',
                    'message': str(result)
                },
                metadata={'batch_index': i}
            ))
        else:
            responses.append(result)
    
    return responses

# WebSocket handling
class WebSocketManager:
    """Manages WebSocket connections"""
    
    def __init__(self):
        self.connections: Dict[str, WebSocket] = {}
        self.subscriptions: Dict[str, List[str]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str):
        """Accept a new connection"""
        await websocket.accept()
        self.connections[client_id] = websocket
        logger.info(f"Client {client_id} connected")
    
    async def disconnect(self, client_id: str):
        """Remove a connection"""
        if client_id in self.connections:
            del self.connections[client_id]
            # Clean up subscriptions
            for agent_type in list(self.subscriptions.keys()):
                if client_id in self.subscriptions[agent_type]:
                    self.subscriptions[agent_type].remove(client_id)
        logger.info(f"Client {client_id} disconnected")
    
    async def send_message(self, client_id: str, message: dict):
        """Send message to a specific client"""
        if client_id in self.connections:
            try:
                await self.connections[client_id].send_json(message)
            except Exception as e:
                logger.error(f"Error sending to {client_id}: {e}")
                await self.disconnect(client_id)
    
    async def broadcast(self, message: dict, agent_type: Optional[str] = None):
        """Broadcast message to subscribed clients"""
        if agent_type and agent_type in self.subscriptions:
            client_ids = self.subscriptions[agent_type]
        else:
            client_ids = list(self.connections.keys())
        
        for client_id in client_ids:
            await self.send_message(client_id, message)

ws_manager = WebSocketManager()

@app.websocket("/ws/agent/stream")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for streaming agent responses"""
    client_id = str(uuid.uuid4())
    
    # Record WebSocket connection metrics
    if PROMETHEUS_AVAILABLE:
        websocket_connections_total.labels(status="connected").inc()
        websocket_active_connections.inc()
    
    await ws_manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            data = await websocket.receive_text()
            message = json.loads(data)
            
            # Handle different message types
            if message['type'] == 'init':
                # Initialize connection
                await ws_manager.send_message(client_id, {
                    'type': 'connected',
                    'sessionId': client_id,
                    'timestamp': datetime.now().isoformat()
                })
            
            elif message['type'] == 'stream_request':
                # Handle streaming request
                request = AgentRequest(**message['request'])
                
                # Set up structured logging for WebSocket
                if STRUCTURED_LOGGING_AVAILABLE:
                    logger.set_context(
                        request_id=request.id,
                        session_id=client_id,
                        agent_type=request.type
                    )
                    logger.info(f"WebSocket agent request: {request.action}",
                               action=request.action,
                               client_id=client_id)
                
                # Get agent
                agent = agent_registry.get_agent(request.type)
                if not agent:
                    await ws_manager.send_message(client_id, {
                        'type': 'error',
                        'error': f"Agent '{request.type}' not found"
                    })
                    continue
                
                start_time = time.time()
                try:
                    # Process with streaming
                    async for chunk in agent.stream_response(request.action, request.payload, request.context):
                        await ws_manager.send_message(client_id, {
                            'type': 'stream_chunk',
                            'data': chunk
                        })
                    
                    # Send completion
                    await ws_manager.send_message(client_id, {
                        'type': 'stream_complete',
                        'requestId': request.id
                    })
                    
                    # Record successful streaming metrics
                    if PROMETHEUS_AVAILABLE:
                        agent_requests_total.labels(
                            agent_type=request.type,
                            action=request.action,
                            status="success_stream"
                        ).inc()
                        
                        response_time = time.time() - start_time
                        agent_response_time_seconds.labels(
                            agent_type=request.type,
                            action=request.action
                        ).observe(response_time)
                    
                    if STRUCTURED_LOGGING_AVAILABLE:
                        logger.info(f"WebSocket agent request completed: {request.action}",
                                   action=request.action,
                                   duration_ms=(time.time() - start_time) * 1000,
                                   client_id=client_id)
                
                except Exception as stream_error:
                    # Record streaming error metrics
                    if PROMETHEUS_AVAILABLE:
                        agent_requests_total.labels(
                            agent_type=request.type,
                            action=request.action,
                            status="error_stream"
                        ).inc()
                    
                    if STRUCTURED_LOGGING_AVAILABLE:
                        logger.error(f"WebSocket agent request failed: {request.action}",
                                    error=stream_error,
                                    action=request.action,
                                    client_id=client_id)
                    
                    await ws_manager.send_message(client_id, {
                        'type': 'error',
                        'error': str(stream_error),
                        'requestId': request.id
                    })
            
            elif message['type'] == 'subscribe':
                # Subscribe to agent events
                agent_type = message.get('agent')
                if agent_type not in ws_manager.subscriptions:
                    ws_manager.subscriptions[agent_type] = []
                ws_manager.subscriptions[agent_type].append(client_id)
            
            elif message['type'] == 'ping':
                # Respond to ping
                await ws_manager.send_message(client_id, {'type': 'pong'})
                
    except Exception as e:
        if STRUCTURED_LOGGING_AVAILABLE:
            logger.error(f"WebSocket error for client {client_id}",
                        error=e,
                        client_id=client_id)
        else:
            logger.error(f"WebSocket error for {client_id}: {e}")
        
        # Record WebSocket error metrics
        if PROMETHEUS_AVAILABLE:
            websocket_connections_total.labels(status="error").inc()
    
    finally:
        await ws_manager.disconnect(client_id)
        
        # Record WebSocket disconnection metrics
        if PROMETHEUS_AVAILABLE:
            websocket_connections_total.labels(status="disconnected").inc()
            websocket_active_connections.dec()

# Agent-specific endpoints
@app.get("/api/v1/agents")
async def list_agents():
    """List all available agents"""
    agents = []
    for agent_type, agent in agent_registry.agents.items():
        agents.append({
            'type': agent_type,
            'name': agent.name if hasattr(agent, 'name') else agent_type.capitalize(),
            'status': 'active',
            'capabilities': agent.get_capabilities() if hasattr(agent, 'get_capabilities') else []
        })
    return {'agents': agents}

@app.get("/api/v1/agents/{agent_type}/status")
async def get_agent_status(agent_type: str):
    """Get status of a specific agent"""
    agent = agent_registry.get_agent(agent_type)
    if not agent:
        raise HTTPException(status_code=404, detail=f"Agent '{agent_type}' not found")
    
    return {
        'type': agent_type,
        'status': 'active',
        'metrics': metrics_tracker['agent_requests'].get(agent_type, {'count': 0, 'errors': 0}),
        'capabilities': agent.get_capabilities() if hasattr(agent, 'get_capabilities') else []
    }

# Error handlers
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            'error': {
                'code': f'HTTP_{exc.status_code}',
                'message': exc.detail,
                'timestamp': datetime.now().isoformat()
            }
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': 'An internal error occurred',
                'timestamp': datetime.now().isoformat()
            }
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "agent_server:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )