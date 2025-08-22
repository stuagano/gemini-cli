"""
Agent Server Metrics Integration
Integrates custom metrics collection with the FastAPI agent server
"""

import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from monitoring.telemetry.custom_metrics import metrics_collector
from monitoring.telemetry.tracing import trace_agent_request
from monitoring.logging.structured_logging import AgentLogger

logger = AgentLogger("agent-server")


class MetricsMiddleware(BaseHTTPMiddleware):
    """Middleware to collect HTTP request metrics automatically"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        
        # Extract agent type from path
        agent_type = "unknown"
        if "/agent/" in str(request.url):
            path_parts = str(request.url).split("/")
            if "agent" in path_parts:
                agent_idx = path_parts.index("agent")
                if agent_idx + 1 < len(path_parts):
                    agent_type = path_parts[agent_idx + 1]
        
        try:
            response = await call_next(request)
            duration = time.time() - start_time
            
            # Record successful request
            metrics_collector.record_agent_request(
                agent_type=agent_type,
                action=request.method.lower(),
                duration_seconds=duration,
                success=response.status_code < 400
            )
            
            logger.info(
                "Request completed",
                agent_type=agent_type,
                method=request.method,
                path=str(request.url.path),
                status_code=response.status_code,
                duration_ms=duration * 1000,
                success=response.status_code < 400
            )
            
            return response
            
        except Exception as e:
            duration = time.time() - start_time
            
            # Record failed request
            metrics_collector.record_agent_request(
                agent_type=agent_type,
                action=request.method.lower(),
                duration_seconds=duration,
                success=False,
                error_type=type(e).__name__
            )
            
            logger.error(
                "Request failed",
                agent_type=agent_type,
                method=request.method,
                path=str(request.url.path),
                error=str(e),
                error_type=type(e).__name__,
                duration_ms=duration * 1000
            )
            
            raise


def setup_metrics_endpoints(app: FastAPI):
    """Add metrics endpoints to FastAPI app"""
    
    @app.get("/metrics")
    async def get_metrics():
        """Prometheus metrics endpoint"""
        return Response(
            content=metrics_collector.get_metrics(),
            media_type=CONTENT_TYPE_LATEST
        )
    
    @app.get("/health/metrics")
    async def get_metrics_health():
        """Health check for metrics collection"""
        try:
            # Test metrics collection
            metrics_collector.record_agent_request("health", "check", 0.001, True)
            return {"status": "healthy", "metrics_collector": "operational"}
        except Exception as e:
            return {"status": "unhealthy", "error": str(e)}
    
    @app.get("/scaling-issues/summary")
    async def get_scaling_issues_summary(hours: int = 24):
        """Get scaling issues summary for business insights"""
        return metrics_collector.get_scaling_issues_summary(hours)


def setup_agent_metrics_tracking():
    """Setup agent-specific metrics tracking"""
    
    def track_scout_metrics(file_path: str, language: str, processing_time: float, 
                          function_count: int = 0, duplicates_found: int = 0):
        """Track Scout indexing metrics"""
        metrics_collector.record_scout_file_indexed(
            file_path=file_path,
            language=language,
            processing_time_seconds=processing_time,
            function_count=function_count,
            success=True
        )
        
        if duplicates_found > 0:
            metrics_collector.record_scout_duplicate_found(
                original_file=file_path,
                duplicate_file="detected",
                language=language,
                similarity_score=0.9,
                severity="medium"
            )
    
    def track_guardian_metrics(validation_type: str, processing_time: float,
                             violations: list = None):
        """Track Guardian validation metrics"""
        violation_count = len(violations) if violations else 0
        
        metrics_collector.record_guardian_validation(
            validation_type=validation_type,
            processing_time_seconds=processing_time,
            violation_count=violation_count,
            success=True
        )
        
        # Record individual violations
        if violations:
            for violation in violations:
                metrics_collector.record_guardian_violation(
                    rule_name=violation.get("rule", "unknown"),
                    severity=violation.get("severity", "medium")
                )
    
    def track_killer_demo_metrics(issue_type: str, severity: str, service: str,
                                 cost_savings: float, performance_impact: float,
                                 file_path: str = "", function_name: str = ""):
        """Track Killer Demo scaling issue detection"""
        metrics_collector.record_scaling_issue(
            issue_type=issue_type,
            severity=severity,
            service=service,
            potential_savings_usd=cost_savings,
            performance_impact_percent=performance_impact,
            file_path=file_path,
            function_name=function_name
        )
        
        # Track if optimization was applied
        if cost_savings > 0:
            metrics_collector.record_optimization_applied(
                optimization_type=issue_type,
                cost_savings_usd=cost_savings,
                performance_improvement_percent=performance_impact
            )
    
    def track_knowledge_metrics(query_type: str, duration: float, chunks: int):
        """Track knowledge base query metrics"""
        metrics_collector.record_knowledge_query(
            query_type=query_type,
            duration_seconds=duration,
            chunks_retrieved=chunks,
            success=True
        )
    
    # Return tracking functions for use in agent implementations
    return {
        "scout": track_scout_metrics,
        "guardian": track_guardian_metrics,
        "killer_demo": track_killer_demo_metrics,
        "knowledge": track_knowledge_metrics
    }


def setup_dora_metrics_tracking():
    """Setup DORA metrics tracking functions"""
    
    def track_deployment(environment: str, success: bool = True, failure_type: str = None):
        """Track deployment for DORA metrics"""
        metrics_collector.record_deployment(environment, success, failure_type)
        
        logger.info(
            "Deployment tracked",
            environment=environment,
            success=success,
            failure_type=failure_type if not success else None
        )
    
    def track_lead_time(environment: str, commit_time: float, deploy_time: float):
        """Track lead time from commit to deployment"""
        lead_time_seconds = deploy_time - commit_time
        metrics_collector.record_lead_time(environment, lead_time_seconds)
        
        logger.info(
            "Lead time tracked",
            environment=environment,
            lead_time_hours=lead_time_seconds / 3600
        )
    
    def track_incident_resolution(severity: str, service: str, start_time: float, end_time: float):
        """Track incident resolution time (MTTR)"""
        resolution_time_seconds = end_time - start_time
        metrics_collector.record_incident_resolution(severity, service, resolution_time_seconds)
        
        logger.info(
            "Incident resolution tracked",
            severity=severity,
            service=service,
            mttr_hours=resolution_time_seconds / 3600
        )
    
    return {
        "deployment": track_deployment,
        "lead_time": track_lead_time,
        "incident_resolution": track_incident_resolution
    }


def setup_business_metrics_tracking():
    """Setup business impact metrics tracking"""
    
    def track_cost_savings(savings_type: str, amount_usd: float):
        """Track cost savings from optimizations"""
        metrics_collector.record_cost_savings(savings_type, amount_usd)
        
        logger.info(
            "Cost savings tracked",
            savings_type=savings_type,
            amount_usd=amount_usd
        )
    
    def track_developer_productivity(team: str, requests_per_hour: float):
        """Track developer productivity metrics"""
        metrics_collector.update_developer_productivity(team, requests_per_hour)
        
        logger.info(
            "Developer productivity tracked",
            team=team,
            requests_per_hour=requests_per_hour
        )
    
    def track_infrastructure_cost(service: str, environment: str, monthly_cost: float):
        """Track infrastructure costs"""
        metrics_collector.update_infrastructure_cost(service, environment, monthly_cost)
    
    return {
        "cost_savings": track_cost_savings,
        "developer_productivity": track_developer_productivity,
        "infrastructure_cost": track_infrastructure_cost
    }


# Export all tracking functions for easy import
__all__ = [
    "MetricsMiddleware",
    "setup_metrics_endpoints", 
    "setup_agent_metrics_tracking",
    "setup_dora_metrics_tracking",
    "setup_business_metrics_tracking"
]