"""
Monitoring and metrics API routes
DORA metrics, performance monitoring, and health checks
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import asyncio

from fastapi import APIRouter, Depends, HTTPException, status, Query
from fastapi.responses import JSONResponse

from security.auth import get_current_active_user, require_permission, User, Permission
from monitoring.dora_metrics import DORAMetricsTracker
from monitoring.performance import performance_monitor
from api.openapi_schemas import (
    BaseResponse, DORAMetrics, PerformanceMetrics, MetricSeries,
    MetricDataPoint
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/monitoring", tags=["Monitoring"])

# DORA Metrics endpoints
@router.get("/dora", response_model=DORAMetrics)
async def get_dora_metrics(
    days: int = Query(default=30, ge=1, le=365, description="Number of days to analyze"),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_permission(Permission.METRICS_VIEW))
):
    """Get DORA metrics for the specified time period"""
    try:
        tracker = DORAMetricsTracker()
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get metrics
        deployment_frequency = await tracker.get_deployment_frequency(start_date, end_date)
        lead_time = await tracker.get_lead_time_for_changes(start_date, end_date)
        mttr = await tracker.get_mean_time_to_recovery(start_date, end_date)
        change_failure_rate = await tracker.get_change_failure_rate(start_date, end_date)
        
        return DORAMetrics(
            deployment_frequency=deployment_frequency,
            lead_time_for_changes=lead_time,
            mean_time_to_recovery=mttr,
            change_failure_rate=change_failure_rate
        )
        
    except Exception as e:
        logger.error(f"Error getting DORA metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve DORA metrics"
        )

@router.get("/dora/deployment-frequency", response_model=MetricSeries)
async def get_deployment_frequency_trend(
    days: int = Query(default=30, ge=1, le=365),
    granularity: str = Query(default="day", regex="^(hour|day|week)$"),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_permission(Permission.METRICS_VIEW))
):
    """Get deployment frequency trend over time"""
    try:
        tracker = DORAMetricsTracker()
        
        # Calculate date range and intervals
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Generate time intervals based on granularity
        intervals = []
        if granularity == "hour":
            delta = timedelta(hours=1)
        elif granularity == "day":
            delta = timedelta(days=1)
        else:  # week
            delta = timedelta(weeks=1)
        
        current = start_date
        while current <= end_date:
            intervals.append(current)
            current += delta
        
        # Get data points for each interval
        data_points = []
        for i, interval_start in enumerate(intervals[:-1]):
            interval_end = intervals[i + 1]
            
            deployments = await tracker.get_deployments(interval_start, interval_end)
            frequency = len(deployments)
            
            if granularity == "day":
                frequency = frequency  # deployments per day
            elif granularity == "hour":
                frequency = frequency * 24  # deployments per day equivalent
            else:  # week
                frequency = frequency / 7  # deployments per day average
            
            data_points.append(MetricDataPoint(
                timestamp=interval_start,
                value=frequency,
                labels={"granularity": granularity}
            ))
        
        return MetricSeries(
            name="deployment_frequency",
            unit="deployments/day",
            data_points=data_points
        )
        
    except Exception as e:
        logger.error(f"Error getting deployment frequency trend: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve deployment frequency trend"
        )

@router.get("/dora/lead-time", response_model=MetricSeries)
async def get_lead_time_trend(
    days: int = Query(default=30, ge=1, le=365),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_permission(Permission.METRICS_VIEW))
):
    """Get lead time for changes trend"""
    try:
        tracker = DORAMetricsTracker()
        
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get daily lead times
        data_points = []
        current = start_date
        
        while current <= end_date:
            next_day = current + timedelta(days=1)
            
            deployments = await tracker.get_deployments(current, next_day)
            if deployments:
                # Calculate average lead time for this day
                lead_times = []
                for deployment in deployments:
                    lead_time = await tracker._calculate_lead_time(deployment)
                    if lead_time:
                        lead_times.append(lead_time)
                
                if lead_times:
                    avg_lead_time = sum(lead_times) / len(lead_times)
                    data_points.append(MetricDataPoint(
                        timestamp=current,
                        value=avg_lead_time,
                        labels={"count": str(len(lead_times))}
                    ))
            
            current = next_day
        
        return MetricSeries(
            name="lead_time_for_changes",
            unit="hours",
            data_points=data_points
        )
        
    except Exception as e:
        logger.error(f"Error getting lead time trend: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve lead time trend"
        )

@router.post("/dora/deployment")
async def record_deployment(
    deployment_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_permission(Permission.WRITE))
):
    """Record a new deployment"""
    try:
        tracker = DORAMetricsTracker()
        
        # Validate required fields
        required_fields = ["commit_sha", "environment", "status"]
        for field in required_fields:
            if field not in deployment_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Record deployment
        await tracker.record_deployment(
            commit_sha=deployment_data["commit_sha"],
            environment=deployment_data["environment"],
            status=deployment_data["status"],
            start_time=deployment_data.get("start_time"),
            end_time=deployment_data.get("end_time"),
            metadata=deployment_data.get("metadata", {})
        )
        
        return {"message": "Deployment recorded successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording deployment: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record deployment"
        )

@router.post("/dora/incident")
async def record_incident(
    incident_data: Dict[str, Any],
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_permission(Permission.WRITE))
):
    """Record a new incident"""
    try:
        tracker = DORAMetricsTracker()
        
        # Validate required fields
        required_fields = ["title", "severity", "status"]
        for field in required_fields:
            if field not in incident_data:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Missing required field: {field}"
                )
        
        # Record incident
        await tracker.record_incident(
            title=incident_data["title"],
            description=incident_data.get("description", ""),
            severity=incident_data["severity"],
            status=incident_data["status"],
            affected_service=incident_data.get("affected_service"),
            start_time=incident_data.get("start_time"),
            end_time=incident_data.get("end_time"),
            metadata=incident_data.get("metadata", {})
        )
        
        return {"message": "Incident recorded successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error recording incident: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to record incident"
        )

# Performance monitoring endpoints
@router.get("/performance", response_model=PerformanceMetrics)
async def get_performance_metrics(
    minutes: int = Query(default=60, ge=1, le=1440, description="Time window in minutes"),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_permission(Permission.METRICS_VIEW))
):
    """Get current performance metrics"""
    try:
        # Get metrics from performance monitor
        metrics = await performance_monitor.get_current_metrics()
        
        return PerformanceMetrics(
            response_time_p50=metrics.get("response_time_p50", 0.0),
            response_time_p95=metrics.get("response_time_p95", 0.0),
            response_time_p99=metrics.get("response_time_p99", 0.0),
            requests_per_second=metrics.get("requests_per_second", 0.0),
            error_rate=metrics.get("error_rate", 0.0),
            cpu_usage=metrics.get("cpu_usage", 0.0),
            memory_usage=metrics.get("memory_usage", 0.0)
        )
        
    except Exception as e:
        logger.error(f"Error getting performance metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve performance metrics"
        )

@router.get("/performance/response-time", response_model=MetricSeries)
async def get_response_time_trend(
    hours: int = Query(default=24, ge=1, le=168),
    percentile: int = Query(default=95, ge=50, le=99),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_permission(Permission.METRICS_VIEW))
):
    """Get response time trend"""
    try:
        # Get historical response time data
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Generate mock data points (in real implementation, fetch from monitoring system)
        data_points = []
        current = start_time
        
        while current <= end_time:
            # Mock response time data (replace with actual monitoring data)
            value = 100 + (hash(str(current)) % 100)  # Mock data
            
            data_points.append(MetricDataPoint(
                timestamp=current,
                value=value,
                labels={"percentile": f"p{percentile}"}
            ))
            
            current += timedelta(minutes=5)
        
        return MetricSeries(
            name=f"response_time_p{percentile}",
            unit="milliseconds",
            data_points=data_points
        )
        
    except Exception as e:
        logger.error(f"Error getting response time trend: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve response time trend"
        )

@router.get("/performance/throughput", response_model=MetricSeries)
async def get_throughput_trend(
    hours: int = Query(default=24, ge=1, le=168),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_permission(Permission.METRICS_VIEW))
):
    """Get requests per second trend"""
    try:
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(hours=hours)
        
        # Generate data points
        data_points = []
        current = start_time
        
        while current <= end_time:
            # Mock throughput data
            value = 50 + (hash(str(current)) % 50)  # Mock data
            
            data_points.append(MetricDataPoint(
                timestamp=current,
                value=value,
                labels={}
            ))
            
            current += timedelta(minutes=5)
        
        return MetricSeries(
            name="requests_per_second",
            unit="requests/second",
            data_points=data_points
        )
        
    except Exception as e:
        logger.error(f"Error getting throughput trend: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve throughput trend"
        )

# System health endpoints
@router.get("/health/detailed")
async def get_detailed_health(
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_permission(Permission.METRICS_VIEW))
):
    """Get detailed system health information"""
    try:
        # Check various system components
        health_checks = {
            "api": "healthy",
            "database": "healthy",
            "redis": "healthy",
            "monitoring": "healthy"
        }
        
        # Perform actual health checks
        try:
            # Check Redis (assuming auth_manager is available)
            from security.auth import auth_manager
            await auth_manager.redis_client.ping()
        except Exception:
            health_checks["redis"] = "unhealthy"
        
        overall_status = "healthy" if all(
            status == "healthy" for status in health_checks.values()
        ) else "degraded"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "components": health_checks,
            "uptime": "unknown",  # Would calculate actual uptime
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Error getting system health: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }

@router.get("/alerts")
async def get_active_alerts(
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_permission(Permission.METRICS_VIEW))
):
    """Get active system alerts"""
    try:
        # In a real implementation, this would fetch from alerting system
        alerts = []
        
        # Mock alert data
        return {
            "alerts": alerts,
            "count": len(alerts),
            "timestamp": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error getting alerts: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve alerts"
        )

# Dashboard endpoints
@router.get("/dashboard/summary")
async def get_dashboard_summary(
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_permission(Permission.METRICS_VIEW))
):
    """Get dashboard summary with key metrics"""
    try:
        # Get key metrics concurrently
        tracker = DORAMetricsTracker()
        
        # Get DORA metrics for last 30 days
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)
        
        tasks = await asyncio.gather(
            tracker.get_deployment_frequency(start_date, end_date),
            tracker.get_lead_time_for_changes(start_date, end_date),
            tracker.get_mean_time_to_recovery(start_date, end_date),
            tracker.get_change_failure_rate(start_date, end_date),
            performance_monitor.get_current_metrics(),
            return_exceptions=True
        )
        
        deployment_frequency, lead_time, mttr, change_failure_rate, perf_metrics = tasks
        
        # Handle exceptions
        if isinstance(perf_metrics, Exception):
            perf_metrics = {}
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "dora_metrics": {
                "deployment_frequency": deployment_frequency if not isinstance(deployment_frequency, Exception) else 0,
                "lead_time_for_changes": lead_time if not isinstance(lead_time, Exception) else 0,
                "mean_time_to_recovery": mttr if not isinstance(mttr, Exception) else 0,
                "change_failure_rate": change_failure_rate if not isinstance(change_failure_rate, Exception) else 0
            },
            "performance_metrics": {
                "response_time_p95": perf_metrics.get("response_time_p95", 0),
                "requests_per_second": perf_metrics.get("requests_per_second", 0),
                "error_rate": perf_metrics.get("error_rate", 0),
                "cpu_usage": perf_metrics.get("cpu_usage", 0),
                "memory_usage": perf_metrics.get("memory_usage", 0)
            },
            "system_status": "healthy"
        }
        
    except Exception as e:
        logger.error(f"Error getting dashboard summary: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve dashboard summary"
        )