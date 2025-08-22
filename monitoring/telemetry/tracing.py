"""
OpenTelemetry Tracing Integration for Gemini Enterprise Architect
Provides distributed tracing across all agent operations and services
"""

import os
import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
from contextlib import contextmanager

from opentelemetry import trace, metrics, baggage
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import OTLPMetricExporter
from opentelemetry.exporter.jaeger.thrift import JaegerExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.propagate import set_global_textmap
from opentelemetry.propagators.b3 import B3MultiFormat
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor, ConsoleSpanExporter
from opentelemetry.sdk.metrics import MeterProvider
from opentelemetry.sdk.metrics.export import PeriodicExportingMetricReader
from opentelemetry.sdk.resources import Resource
from opentelemetry.trace.status import Status, StatusCode
from opentelemetry.trace import SpanKind
from opentelemetry.semconv.trace import SpanAttributes
from opentelemetry.semconv.resource import ResourceAttributes


class GeminiTracer:
    """
    Centralized tracing configuration for Gemini Enterprise Architect
    """
    
    def __init__(self, service_name: str, service_version: str = "1.0.0"):
        self.service_name = service_name
        self.service_version = service_version
        self.environment = os.getenv('ENVIRONMENT', 'development')
        
        # Setup OpenTelemetry
        self._setup_tracing()
        self._setup_metrics()
        self._setup_auto_instrumentation()
        
        # Get tracer and meter instances
        self.tracer = trace.get_tracer(service_name, service_version)
        self.meter = metrics.get_meter(service_name, service_version)
        
        # Create custom metrics
        self._setup_custom_metrics()
    
    def _setup_tracing(self):
        """Configure OpenTelemetry tracing"""
        
        # Create resource with service information
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: self.service_name,
            ResourceAttributes.SERVICE_VERSION: self.service_version,
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: self.environment,
            ResourceAttributes.SERVICE_NAMESPACE: "gemini-enterprise",
        })
        
        # Create tracer provider
        tracer_provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(tracer_provider)
        
        # Configure exporters based on environment
        if self.environment == 'development':
            # Console exporter for development
            console_exporter = ConsoleSpanExporter()
            tracer_provider.add_span_processor(
                BatchSpanProcessor(console_exporter)
            )
        
        # OTLP exporter for production
        otlp_endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://otel-collector:4317')
        if otlp_endpoint:
            otlp_exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
            tracer_provider.add_span_processor(
                BatchSpanProcessor(otlp_exporter)
            )
        
        # Jaeger exporter for trace visualization
        jaeger_endpoint = os.getenv('JAEGER_ENDPOINT', 'http://jaeger:14268/api/traces')
        if jaeger_endpoint:
            jaeger_exporter = JaegerExporter(
                agent_host_name=os.getenv('JAEGER_AGENT_HOST', 'jaeger'),
                agent_port=int(os.getenv('JAEGER_AGENT_PORT', '6831')),
            )
            tracer_provider.add_span_processor(
                BatchSpanProcessor(jaeger_exporter)
            )
        
        # Set global text map propagator for distributed tracing
        set_global_textmap(B3MultiFormat())
    
    def _setup_metrics(self):
        """Configure OpenTelemetry metrics"""
        
        # OTLP metric exporter
        otlp_endpoint = os.getenv('OTEL_EXPORTER_OTLP_ENDPOINT', 'http://otel-collector:4317')
        otlp_exporter = OTLPMetricExporter(endpoint=otlp_endpoint, insecure=True)
        
        # Create metric reader
        metric_reader = PeriodicExportingMetricReader(
            exporter=otlp_exporter,
            export_interval_millis=30000,  # Export every 30 seconds
        )
        
        # Create resource
        resource = Resource.create({
            ResourceAttributes.SERVICE_NAME: self.service_name,
            ResourceAttributes.SERVICE_VERSION: self.service_version,
            ResourceAttributes.DEPLOYMENT_ENVIRONMENT: self.environment,
        })
        
        # Create meter provider
        meter_provider = MeterProvider(
            resource=resource,
            metric_readers=[metric_reader]
        )
        metrics.set_meter_provider(meter_provider)
    
    def _setup_auto_instrumentation(self):
        """Setup automatic instrumentation for common libraries"""
        
        # FastAPI instrumentation
        FastAPIInstrumentor().instrument()
        
        # HTTP requests instrumentation
        RequestsInstrumentor().instrument()
        
        # Database instrumentation
        Psycopg2Instrumentor().instrument()
        
        # Redis instrumentation
        RedisInstrumentor().instrument()
    
    def _setup_custom_metrics(self):
        """Create custom metrics for Gemini-specific operations"""
        
        # Agent operation metrics
        self.agent_request_counter = self.meter.create_counter(
            name="gemini_agent_requests_total",
            description="Total number of agent requests",
            unit="1"
        )
        
        self.agent_request_duration = self.meter.create_histogram(
            name="gemini_agent_request_duration_seconds",
            description="Agent request processing time",
            unit="s"
        )
        
        self.agent_error_counter = self.meter.create_counter(
            name="gemini_agent_errors_total",
            description="Total number of agent errors",
            unit="1"
        )
        
        # Scout metrics
        self.scout_files_indexed = self.meter.create_counter(
            name="gemini_scout_files_indexed_total",
            description="Total number of files indexed by Scout",
            unit="1"
        )
        
        self.scout_duplicates_found = self.meter.create_counter(
            name="gemini_scout_duplicates_found_total",
            description="Total number of duplicates found by Scout",
            unit="1"
        )
        
        self.scout_processing_time = self.meter.create_histogram(
            name="gemini_scout_processing_time_seconds",
            description="Scout file processing time",
            unit="s"
        )
        
        # Guardian metrics
        self.guardian_validations = self.meter.create_counter(
            name="gemini_guardian_validations_total",
            description="Total number of Guardian validations",
            unit="1"
        )
        
        self.guardian_violations = self.meter.create_counter(
            name="gemini_guardian_violations_total",
            description="Total number of Guardian violations",
            unit="1"
        )
        
        # Killer Demo metrics
        self.scaling_issues_detected = self.meter.create_counter(
            name="gemini_scaling_issues_detected_total",
            description="Total number of scaling issues detected",
            unit="1"
        )
        
        self.cost_savings = self.meter.create_counter(
            name="gemini_cost_savings_usd_total",
            description="Total cost savings from optimizations",
            unit="USD"
        )


# Global tracer instance
_tracer_instance: Optional[GeminiTracer] = None


def initialize_tracing(service_name: str, service_version: str = "1.0.0") -> GeminiTracer:
    """Initialize global tracing configuration"""
    global _tracer_instance
    _tracer_instance = GeminiTracer(service_name, service_version)
    return _tracer_instance


def get_tracer() -> GeminiTracer:
    """Get the global tracer instance"""
    if _tracer_instance is None:
        raise RuntimeError("Tracing not initialized. Call initialize_tracing() first.")
    return _tracer_instance


def trace_agent_request(agent_type: str):
    """Decorator to trace agent requests"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            tracer = get_tracer()
            
            with tracer.tracer.start_as_current_span(
                f"agent.{agent_type}.request",
                kind=SpanKind.SERVER
            ) as span:
                # Set span attributes
                span.set_attribute("agent.type", agent_type)
                span.set_attribute("service.name", tracer.service_name)
                
                # Extract request details
                if args and hasattr(args[0], 'action'):
                    span.set_attribute("agent.action", args[0].action)
                    span.set_attribute("agent.request_id", getattr(args[0], 'id', ''))
                
                # Add baggage context
                baggage.set_baggage("agent.type", agent_type)
                
                start_time = time.time()
                
                try:
                    result = await func(*args, **kwargs)
                    
                    # Record success metrics
                    duration = time.time() - start_time
                    tracer.agent_request_duration.record(
                        duration,
                        {"agent_type": agent_type, "status": "success"}
                    )
                    tracer.agent_request_counter.add(
                        1,
                        {"agent_type": agent_type, "status": "success"}
                    )
                    
                    span.set_status(Status(StatusCode.OK))
                    span.set_attribute("agent.duration_seconds", duration)
                    
                    return result
                    
                except Exception as e:
                    # Record error metrics
                    duration = time.time() - start_time
                    tracer.agent_request_duration.record(
                        duration,
                        {"agent_type": agent_type, "status": "error"}
                    )
                    tracer.agent_error_counter.add(
                        1,
                        {"agent_type": agent_type, "error_type": type(e).__name__}
                    )
                    
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.set_attribute("agent.error", str(e))
                    span.set_attribute("agent.error_type", type(e).__name__)
                    span.set_attribute("agent.duration_seconds", duration)
                    
                    raise
        
        return wrapper
    return decorator


def trace_scout_operation(operation_type: str):
    """Decorator to trace Scout operations"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            
            with tracer.tracer.start_as_current_span(
                f"scout.{operation_type}",
                kind=SpanKind.INTERNAL
            ) as span:
                # Set span attributes
                span.set_attribute("scout.operation", operation_type)
                span.set_attribute("service.name", "scout")
                
                # Extract file path if available
                file_path = kwargs.get('file_path') or (args[0] if args else None)
                if file_path:
                    span.set_attribute("scout.file_path", str(file_path))
                
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Record metrics based on operation type
                    duration = time.time() - start_time
                    
                    if operation_type == "index_file":
                        tracer.scout_files_indexed.add(1, {"status": "success"})
                        tracer.scout_processing_time.record(duration, {"operation": "index"})
                    elif operation_type == "find_duplicates":
                        duplicate_count = len(result) if isinstance(result, list) else 0
                        tracer.scout_duplicates_found.add(duplicate_count)
                        span.set_attribute("scout.duplicates_found", duplicate_count)
                    
                    span.set_status(Status(StatusCode.OK))
                    span.set_attribute("scout.duration_seconds", duration)
                    
                    return result
                    
                except Exception as e:
                    duration = time.time() - start_time
                    
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.set_attribute("scout.error", str(e))
                    span.set_attribute("scout.duration_seconds", duration)
                    
                    raise
        
        return wrapper
    return decorator


def trace_guardian_validation(validation_type: str):
    """Decorator to trace Guardian validation operations"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            
            with tracer.tracer.start_as_current_span(
                f"guardian.validation.{validation_type}",
                kind=SpanKind.INTERNAL
            ) as span:
                # Set span attributes
                span.set_attribute("guardian.validation_type", validation_type)
                span.set_attribute("service.name", "guardian")
                
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Record metrics
                    duration = time.time() - start_time
                    tracer.guardian_validations.add(1, {
                        "validation_type": validation_type,
                        "status": "success"
                    })
                    
                    # Count violations if result contains them
                    if hasattr(result, 'violations'):
                        violation_count = len(result.violations)
                        tracer.guardian_violations.add(violation_count, {
                            "validation_type": validation_type
                        })
                        span.set_attribute("guardian.violations_found", violation_count)
                    
                    span.set_status(Status(StatusCode.OK))
                    span.set_attribute("guardian.duration_seconds", duration)
                    
                    return result
                    
                except Exception as e:
                    duration = time.time() - start_time
                    
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.set_attribute("guardian.error", str(e))
                    span.set_attribute("guardian.duration_seconds", duration)
                    
                    raise
        
        return wrapper
    return decorator


def trace_killer_demo_analysis():
    """Decorator to trace Killer Demo scaling analysis"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            tracer = get_tracer()
            
            with tracer.tracer.start_as_current_span(
                "killer_demo.scaling_analysis",
                kind=SpanKind.INTERNAL
            ) as span:
                # Set span attributes
                span.set_attribute("service.name", "killer-demo")
                
                start_time = time.time()
                
                try:
                    result = func(*args, **kwargs)
                    
                    # Record metrics for detected issues
                    if hasattr(result, 'scaling_issues'):
                        issue_count = len(result.scaling_issues)
                        total_savings = sum(issue.potential_savings_usd for issue in result.scaling_issues)
                        
                        tracer.scaling_issues_detected.add(issue_count, {
                            "analysis_type": "scaling"
                        })
                        tracer.cost_savings.add(total_savings)
                        
                        span.set_attribute("killer_demo.issues_found", issue_count)
                        span.set_attribute("killer_demo.potential_savings_usd", total_savings)
                    
                    duration = time.time() - start_time
                    span.set_status(Status(StatusCode.OK))
                    span.set_attribute("killer_demo.duration_seconds", duration)
                    
                    return result
                    
                except Exception as e:
                    duration = time.time() - start_time
                    
                    span.set_status(Status(StatusCode.ERROR, str(e)))
                    span.set_attribute("killer_demo.error", str(e))
                    span.set_attribute("killer_demo.duration_seconds", duration)
                    
                    raise
        
        return wrapper
    return decorator


@contextmanager
def trace_operation(operation_name: str, attributes: Dict[str, Any] = None):
    """Context manager for tracing arbitrary operations"""
    tracer = get_tracer()
    
    with tracer.tracer.start_as_current_span(operation_name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, value)
        
        start_time = time.time()
        
        try:
            yield span
            
            duration = time.time() - start_time
            span.set_status(Status(StatusCode.OK))
            span.set_attribute("operation.duration_seconds", duration)
            
        except Exception as e:
            duration = time.time() - start_time
            span.set_status(Status(StatusCode.ERROR, str(e)))
            span.set_attribute("operation.error", str(e))
            span.set_attribute("operation.duration_seconds", duration)
            raise


def add_span_event(event_name: str, attributes: Dict[str, Any] = None):
    """Add an event to the current span"""
    current_span = trace.get_current_span()
    if current_span and current_span.is_recording():
        current_span.add_event(event_name, attributes or {})