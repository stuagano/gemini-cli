"""
Custom Metrics Collection for Gemini Enterprise Architect
Provides business-specific metrics and performance indicators
"""

import time
import psutil
import threading
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from datetime import datetime, timedelta
from collections import defaultdict, deque
from concurrent.futures import ThreadPoolExecutor

from prometheus_client import Counter, Histogram, Gauge, Info, CollectorRegistry, generate_latest
from prometheus_client.core import REGISTRY


@dataclass
class ScalingIssue:
    file_path: str
    function_name: str
    issue_type: str
    severity: str
    potential_savings_usd: float
    performance_impact_percent: float
    detection_confidence: float
    detected_at: datetime


@dataclass
class AgentMetrics:
    request_count: int = 0
    error_count: int = 0
    total_duration_ms: float = 0
    active_sessions: int = 0
    queue_size: int = 0


class GeminiMetricsCollector:
    """
    Custom metrics collector for Gemini-specific business metrics
    """
    
    def __init__(self):
        # Create custom registry for Gemini metrics
        self.registry = CollectorRegistry()
        
        # Agent Performance Metrics
        self.agent_requests_total = Counter(
            'gemini_agent_requests_total',
            'Total number of agent requests',
            ['agent_type', 'action', 'status'],
            registry=self.registry
        )
        
        self.agent_response_time_seconds = Histogram(
            'gemini_agent_response_time_seconds',
            'Agent response time in seconds',
            ['agent_type', 'action'],
            buckets=[0.1, 0.25, 0.5, 1, 2.5, 5, 10, 25, 50, 100],
            registry=self.registry
        )
        
        self.agent_active_sessions = Gauge(
            'gemini_agent_active_sessions',
            'Number of active agent sessions',
            ['agent_type'],
            registry=self.registry
        )
        
        self.agent_queue_size = Gauge(
            'gemini_agent_queue_size',
            'Number of requests in agent queue',
            ['agent_type'],
            registry=self.registry
        )
        
        # Scout Metrics
        self.scout_files_indexed_total = Counter(
            'gemini_scout_files_indexed_total',
            'Total number of files indexed by Scout',
            ['language', 'status'],
            registry=self.registry
        )
        
        self.scout_duplicates_detected_total = Counter(
            'gemini_scout_duplicates_detected_total',
            'Total number of duplicates detected',
            ['language', 'severity'],
            registry=self.registry
        )
        
        self.scout_processing_time_seconds = Histogram(
            'gemini_scout_processing_time_seconds',
            'Scout file processing time',
            ['language'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5, 10],
            registry=self.registry
        )
        
        self.scout_duplicate_detection_accuracy_percent = Gauge(
            'gemini_scout_duplicate_detection_accuracy_percent',
            'Scout duplicate detection accuracy percentage',
            registry=self.registry
        )
        
        self.scout_index_memory_usage_bytes = Gauge(
            'gemini_scout_index_memory_usage_bytes',
            'Memory usage of Scout indexes',
            ['index_type'],
            registry=self.registry
        )
        
        # Guardian Metrics
        self.guardian_validations_total = Counter(
            'gemini_guardian_validations_total',
            'Total number of Guardian validations',
            ['validation_type', 'status'],
            registry=self.registry
        )
        
        self.guardian_violations_total = Counter(
            'gemini_guardian_violations_total',
            'Total number of Guardian violations',
            ['rule_name', 'severity'],
            registry=self.registry
        )
        
        self.guardian_validation_time_seconds = Histogram(
            'gemini_guardian_validation_time_seconds',
            'Guardian validation processing time',
            ['validation_type'],
            buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5],
            registry=self.registry
        )
        
        # Killer Demo Metrics
        self.scaling_issues_detected_total = Counter(
            'gemini_scaling_issues_detected_total',
            'Total number of scaling issues detected',
            ['issue_type', 'severity', 'service'],
            registry=self.registry
        )
        
        self.scaling_optimizations_cost_savings_usd = Counter(
            'gemini_scaling_optimizations_cost_savings_usd',
            'Total cost savings from scaling optimizations in USD',
            ['optimization_type'],
            registry=self.registry
        )
        
        self.scaling_optimizations_performance_improvement_percent = Histogram(
            'gemini_scaling_optimizations_performance_improvement_percent',
            'Performance improvement percentage from optimizations',
            ['optimization_type'],
            buckets=[5, 10, 15, 25, 50, 75, 100, 150, 200],
            registry=self.registry
        )
        
        self.killer_demo_detection_accuracy_percent = Gauge(
            'gemini_killer_demo_detection_accuracy_percent',
            'Killer Demo detection accuracy percentage',
            registry=self.registry
        )
        
        # Knowledge Base Metrics
        self.knowledge_queries_total = Counter(
            'gemini_knowledge_queries_total',
            'Total number of knowledge base queries',
            ['query_type', 'status'],
            registry=self.registry
        )
        
        self.knowledge_query_duration_seconds = Histogram(
            'gemini_knowledge_query_duration_seconds',
            'Knowledge base query duration',
            ['query_type'],
            buckets=[0.1, 0.25, 0.5, 1, 2, 5, 10, 30],
            registry=self.registry
        )
        
        self.knowledge_chunks_retrieved = Histogram(
            'gemini_knowledge_chunks_retrieved',
            'Number of chunks retrieved per query',
            ['query_type'],
            buckets=[1, 3, 5, 10, 15, 20, 30, 50],
            registry=self.registry
        )
        
        # Business Impact Metrics
        self.cost_savings_usd_total = Counter(
            'gemini_cost_savings_usd_total',
            'Total cost savings in USD',
            ['savings_type'],
            registry=self.registry
        )
        
        self.infrastructure_cost_monthly_usd = Gauge(
            'gemini_infrastructure_cost_monthly_usd',
            'Monthly infrastructure cost in USD',
            ['service', 'environment'],
            registry=self.registry
        )
        
        self.developer_productivity_requests_per_hour = Gauge(
            'gemini_developer_productivity_requests_per_hour',
            'Developer productivity measured in requests per hour',
            ['team'],
            registry=self.registry
        )
        
        # DORA Metrics
        self.deployments_total = Counter(
            'gemini_deployments_total',
            'Total number of deployments',
            ['environment', 'status'],
            registry=self.registry
        )
        
        self.deployment_failures_total = Counter(
            'gemini_deployment_failures_total',
            'Total number of deployment failures',
            ['environment', 'failure_type'],
            registry=self.registry
        )
        
        self.lead_time_seconds = Histogram(
            'gemini_lead_time_seconds',
            'Lead time from code commit to production deployment',
            ['environment'],
            buckets=[3600, 7200, 14400, 43200, 86400, 172800, 604800, 1209600],  # 1h to 2 weeks
            registry=self.registry
        )
        
        self.incident_resolution_time_seconds = Histogram(
            'gemini_incident_resolution_time_seconds',
            'Time to resolve incidents (MTTR)',
            ['severity', 'service'],
            buckets=[300, 600, 1800, 3600, 7200, 14400, 43200, 86400],  # 5min to 1 day
            registry=self.registry
        )
        
        # System Health Metrics
        self.system_memory_usage_bytes = Gauge(
            'gemini_system_memory_usage_bytes',
            'System memory usage in bytes',
            ['component'],
            registry=self.registry
        )
        
        self.system_cpu_usage_percent = Gauge(
            'gemini_system_cpu_usage_percent',
            'System CPU usage percentage',
            ['component'],
            registry=self.registry
        )
        
        self.database_connections_active = Gauge(
            'gemini_database_connections_active',
            'Number of active database connections',
            ['database'],
            registry=self.registry
        )
        
        # Internal tracking
        self.agent_metrics: Dict[str, AgentMetrics] = defaultdict(AgentMetrics)
        self.scaling_issues: List[ScalingIssue] = []
        self.last_metrics_update = time.time()
        
        # Start background metrics collection
        self._start_background_collection()
    
    def _start_background_collection(self):
        """Start background thread for periodic metrics collection"""
        def collect_system_metrics():
            while True:
                try:
                    # Collect system metrics
                    self._collect_system_metrics()
                    time.sleep(30)  # Update every 30 seconds
                except Exception as e:
                    print(f"Error collecting system metrics: {e}")
                    time.sleep(30)
        
        thread = threading.Thread(target=collect_system_metrics, daemon=True)
        thread.start()
    
    def _collect_system_metrics(self):
        """Collect system-level metrics"""
        # Memory usage
        memory = psutil.virtual_memory()
        self.system_memory_usage_bytes.labels(component="system").set(memory.used)
        
        # CPU usage
        cpu_percent = psutil.cpu_percent(interval=1)
        self.system_cpu_usage_percent.labels(component="system").set(cpu_percent)
        
        # Process-specific metrics
        process = psutil.Process()
        self.system_memory_usage_bytes.labels(component="agent-server").set(process.memory_info().rss)
        self.system_cpu_usage_percent.labels(component="agent-server").set(process.cpu_percent())
    
    # Agent Metrics Methods
    def record_agent_request(self, agent_type: str, action: str, duration_seconds: float, 
                           success: bool = True, error_type: str = None):
        """Record agent request metrics"""
        status = "success" if success else "error"
        
        self.agent_requests_total.labels(
            agent_type=agent_type,
            action=action,
            status=status
        ).inc()
        
        self.agent_response_time_seconds.labels(
            agent_type=agent_type,
            action=action
        ).observe(duration_seconds)
        
        # Update internal tracking
        metrics = self.agent_metrics[agent_type]
        metrics.request_count += 1
        metrics.total_duration_ms += duration_seconds * 1000
        
        if not success:
            metrics.error_count += 1
    
    def update_agent_sessions(self, agent_type: str, active_sessions: int):
        """Update active agent sessions"""
        self.agent_active_sessions.labels(agent_type=agent_type).set(active_sessions)
        self.agent_metrics[agent_type].active_sessions = active_sessions
    
    def update_agent_queue(self, agent_type: str, queue_size: int):
        """Update agent queue size"""
        self.agent_queue_size.labels(agent_type=agent_type).set(queue_size)
        self.agent_metrics[agent_type].queue_size = queue_size
    
    # Scout Metrics Methods
    def record_scout_file_indexed(self, file_path: str, language: str, processing_time_seconds: float,
                                 function_count: int = 0, success: bool = True):
        """Record Scout file indexing metrics"""
        status = "success" if success else "error"
        
        self.scout_files_indexed_total.labels(
            language=language,
            status=status
        ).inc()
        
        if success:
            self.scout_processing_time_seconds.labels(language=language).observe(processing_time_seconds)
    
    def record_scout_duplicate_found(self, original_file: str, duplicate_file: str, 
                                   language: str, similarity_score: float, severity: str = "medium"):
        """Record Scout duplicate detection"""
        self.scout_duplicates_detected_total.labels(
            language=language,
            severity=severity
        ).inc()
    
    def update_scout_accuracy(self, accuracy_percent: float):
        """Update Scout detection accuracy"""
        self.scout_duplicate_detection_accuracy_percent.set(accuracy_percent)
    
    def update_scout_memory_usage(self, index_type: str, memory_bytes: int):
        """Update Scout memory usage"""
        self.scout_index_memory_usage_bytes.labels(index_type=index_type).set(memory_bytes)
    
    # Guardian Metrics Methods
    def record_guardian_validation(self, validation_type: str, processing_time_seconds: float,
                                 violation_count: int = 0, success: bool = True):
        """Record Guardian validation metrics"""
        status = "success" if success else "error"
        
        self.guardian_validations_total.labels(
            validation_type=validation_type,
            status=status
        ).inc()
        
        if success:
            self.guardian_validation_time_seconds.labels(
                validation_type=validation_type
            ).observe(processing_time_seconds)
    
    def record_guardian_violation(self, rule_name: str, severity: str):
        """Record Guardian validation violation"""
        self.guardian_violations_total.labels(
            rule_name=rule_name,
            severity=severity
        ).inc()
    
    # Killer Demo Metrics Methods
    def record_scaling_issue(self, issue_type: str, severity: str, service: str,
                           potential_savings_usd: float, performance_impact_percent: float,
                           file_path: str = "", function_name: str = "", detection_confidence: float = 0.9):
        """Record scaling issue detection"""
        self.scaling_issues_detected_total.labels(
            issue_type=issue_type,
            severity=severity,
            service=service
        ).inc()
        
        # Store for detailed tracking
        issue = ScalingIssue(
            file_path=file_path,
            function_name=function_name,
            issue_type=issue_type,
            severity=severity,
            potential_savings_usd=potential_savings_usd,
            performance_impact_percent=performance_impact_percent,
            detection_confidence=detection_confidence,
            detected_at=datetime.now()
        )
        self.scaling_issues.append(issue)
        
        # Keep only last 1000 issues
        if len(self.scaling_issues) > 1000:
            self.scaling_issues = self.scaling_issues[-1000:]
    
    def record_optimization_applied(self, optimization_type: str, cost_savings_usd: float,
                                  performance_improvement_percent: float):
        """Record applied optimization"""
        self.scaling_optimizations_cost_savings_usd.labels(
            optimization_type=optimization_type
        ).inc(cost_savings_usd)
        
        self.scaling_optimizations_performance_improvement_percent.labels(
            optimization_type=optimization_type
        ).observe(performance_improvement_percent)
    
    def update_killer_demo_accuracy(self, accuracy_percent: float):
        """Update Killer Demo detection accuracy"""
        self.killer_demo_detection_accuracy_percent.set(accuracy_percent)
    
    # Knowledge Base Metrics Methods
    def record_knowledge_query(self, query_type: str, duration_seconds: float,
                             chunks_retrieved: int, success: bool = True):
        """Record knowledge base query metrics"""
        status = "success" if success else "error"
        
        self.knowledge_queries_total.labels(
            query_type=query_type,
            status=status
        ).inc()
        
        if success:
            self.knowledge_query_duration_seconds.labels(
                query_type=query_type
            ).observe(duration_seconds)
            
            self.knowledge_chunks_retrieved.labels(
                query_type=query_type
            ).observe(chunks_retrieved)
    
    # Business Impact Metrics Methods
    def record_cost_savings(self, savings_type: str, amount_usd: float):
        """Record cost savings"""
        self.cost_savings_usd_total.labels(savings_type=savings_type).inc(amount_usd)
    
    def update_infrastructure_cost(self, service: str, environment: str, monthly_cost_usd: float):
        """Update infrastructure cost"""
        self.infrastructure_cost_monthly_usd.labels(
            service=service,
            environment=environment
        ).set(monthly_cost_usd)
    
    def update_developer_productivity(self, team: str, requests_per_hour: float):
        """Update developer productivity metrics"""
        self.developer_productivity_requests_per_hour.labels(team=team).set(requests_per_hour)
    
    # DORA Metrics Methods
    def record_deployment(self, environment: str, success: bool = True, failure_type: str = None):
        """Record deployment"""
        status = "success" if success else "failure"
        
        self.deployments_total.labels(
            environment=environment,
            status=status
        ).inc()
        
        if not success and failure_type:
            self.deployment_failures_total.labels(
                environment=environment,
                failure_type=failure_type
            ).inc()
    
    def record_lead_time(self, environment: str, lead_time_seconds: float):
        """Record lead time for changes"""
        self.lead_time_seconds.labels(environment=environment).observe(lead_time_seconds)
    
    def record_incident_resolution(self, severity: str, service: str, resolution_time_seconds: float):
        """Record incident resolution time (MTTR)"""
        self.incident_resolution_time_seconds.labels(
            severity=severity,
            service=service
        ).observe(resolution_time_seconds)
    
    def update_database_connections(self, database: str, active_connections: int):
        """Update database connection count"""
        self.database_connections_active.labels(database=database).set(active_connections)
    
    def get_metrics(self) -> str:
        """Get all metrics in Prometheus format"""
        return generate_latest(self.registry).decode('utf-8')
    
    def get_scaling_issues_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get summary of scaling issues detected in the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        recent_issues = [issue for issue in self.scaling_issues if issue.detected_at > cutoff_time]
        
        return {
            "total_issues": len(recent_issues),
            "critical_issues": len([i for i in recent_issues if i.severity == "critical"]),
            "total_potential_savings": sum(i.potential_savings_usd for i in recent_issues),
            "average_performance_impact": sum(i.performance_impact_percent for i in recent_issues) / max(1, len(recent_issues)),
            "issues_by_type": defaultdict(int, {i.issue_type: recent_issues.count(i) for i in recent_issues}),
            "issues_by_severity": defaultdict(int, {i.severity: recent_issues.count(i) for i in recent_issues})
        }


# Global metrics collector instance
metrics_collector = GeminiMetricsCollector()