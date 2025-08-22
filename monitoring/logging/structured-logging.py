"""
Structured Logging Configuration for Gemini Enterprise Architect
Provides consistent, searchable, and analyzable logging across all components
"""

import json
import logging
import time
import traceback
from datetime import datetime
from typing import Dict, Any, Optional, Union
from contextvars import ContextVar
from functools import wraps
import uuid
import os

# Context variables for request tracking
request_id_var: ContextVar[str] = ContextVar('request_id', default='')
session_id_var: ContextVar[str] = ContextVar('session_id', default='')
user_id_var: ContextVar[str] = ContextVar('user_id', default='')
agent_type_var: ContextVar[str] = ContextVar('agent_type', default='')


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter for structured JSON logging
    """
    
    def __init__(self, service_name: str, environment: str = "production"):
        self.service_name = service_name
        self.environment = environment
        super().__init__()
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        
        # Base log structure
        log_entry = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "service": self.service_name,
            "environment": self.environment,
            "message": record.getMessage(),
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "process_id": os.getpid(),
            "thread_id": record.thread,
        }
        
        # Add context variables if available
        if request_id_var.get():
            log_entry["request_id"] = request_id_var.get()
        if session_id_var.get():
            log_entry["session_id"] = session_id_var.get()
        if user_id_var.get():
            log_entry["user_id"] = user_id_var.get()
        if agent_type_var.get():
            log_entry["agent_type"] = agent_type_var.get()
        
        # Add exception information if present
        if record.exc_info:
            log_entry.update({
                "exception": {
                    "type": record.exc_info[0].__name__,
                    "message": str(record.exc_info[1]),
                    "stack_trace": traceback.format_exception(*record.exc_info)
                }
            })
        
        # Add custom fields from extra parameter
        if hasattr(record, 'extra_fields'):
            log_entry.update(record.extra_fields)
        
        return json.dumps(log_entry, default=str, ensure_ascii=False)


class GeminiLogger:
    """
    Enhanced logger for Gemini Enterprise Architect with structured logging
    """
    
    def __init__(self, name: str, service: str, log_level: str = "INFO"):
        self.service = service
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, log_level.upper()))
        
        # Remove existing handlers to avoid duplication
        self.logger.handlers.clear()
        
        # Setup structured JSON formatter
        environment = os.getenv('ENVIRONMENT', 'development')
        formatter = StructuredFormatter(service, environment)
        
        # Console handler for development
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # File handler for production
        if environment in ['production', 'staging']:
            log_dir = f"/var/log/gemini/{service}"
            os.makedirs(log_dir, exist_ok=True)
            
            file_handler = logging.FileHandler(f"{log_dir}/{service}.log")
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
            # Separate error log file
            error_handler = logging.FileHandler(f"{log_dir}/{service}-errors.log")
            error_handler.setLevel(logging.ERROR)
            error_handler.setFormatter(formatter)
            self.logger.addHandler(error_handler)
    
    def set_context(self, request_id: str = None, session_id: str = None, 
                   user_id: str = None, agent_type: str = None):
        """Set logging context variables"""
        if request_id:
            request_id_var.set(request_id)
        if session_id:
            session_id_var.set(session_id)
        if user_id:
            user_id_var.set(user_id)
        if agent_type:
            agent_type_var.set(agent_type)
    
    def info(self, message: str, **extra):
        """Log info message with optional extra fields"""
        self.logger.info(message, extra={'extra_fields': extra})
    
    def warning(self, message: str, **extra):
        """Log warning message with optional extra fields"""
        self.logger.warning(message, extra={'extra_fields': extra})
    
    def error(self, message: str, error: Exception = None, **extra):
        """Log error message with optional exception and extra fields"""
        if error:
            extra.update({
                'error_type': type(error).__name__,
                'error_message': str(error)
            })
        self.logger.error(message, exc_info=error, extra={'extra_fields': extra})
    
    def debug(self, message: str, **extra):
        """Log debug message with optional extra fields"""
        self.logger.debug(message, extra={'extra_fields': extra})
    
    def critical(self, message: str, **extra):
        """Log critical message with optional extra fields"""
        self.logger.critical(message, extra={'extra_fields': extra})


class AgentLogger(GeminiLogger):
    """Specialized logger for agent operations"""
    
    def __init__(self, agent_type: str):
        super().__init__(f"agent.{agent_type}", f"{agent_type}-agent")
        self.agent_type = agent_type
        agent_type_var.set(agent_type)
    
    def log_request_start(self, action: str, payload: Dict[str, Any], request_id: str = None):
        """Log the start of an agent request"""
        if not request_id:
            request_id = str(uuid.uuid4())
        
        self.set_context(request_id=request_id)
        
        self.info(
            f"Agent request started: {action}",
            action=action,
            payload_size=len(str(payload)),
            request_start_time=time.time()
        )
        return request_id
    
    def log_request_complete(self, action: str, duration_ms: float, success: bool = True, **extra):
        """Log the completion of an agent request"""
        self.info(
            f"Agent request completed: {action}",
            action=action,
            duration_ms=duration_ms,
            success=success,
            **extra
        )
    
    def log_processing_step(self, step: str, **extra):
        """Log intermediate processing steps"""
        self.debug(
            f"Processing step: {step}",
            processing_step=step,
            **extra
        )


class ScoutLogger(GeminiLogger):
    """Specialized logger for Scout indexing operations"""
    
    def __init__(self):
        super().__init__("scout.indexer", "scout")
    
    def log_file_indexed(self, file_path: str, language: str, function_count: int, 
                        processing_time_ms: float, **extra):
        """Log successful file indexing"""
        self.info(
            f"File indexed: {file_path}",
            file_path=file_path,
            language=language,
            function_count=function_count,
            processing_time_ms=processing_time_ms,
            **extra
        )
    
    def log_duplicate_found(self, original_file: str, duplicate_file: str, 
                          function_name: str, similarity_score: float, **extra):
        """Log duplicate detection"""
        self.info(
            f"Duplicate found: {function_name}",
            original_file=original_file,
            duplicate_file=duplicate_file,
            function_name=function_name,
            similarity_score=similarity_score,
            duplicate_detection=True,
            **extra
        )
    
    def log_indexing_error(self, file_path: str, error: Exception, **extra):
        """Log indexing errors"""
        self.error(
            f"Indexing failed: {file_path}",
            error=error,
            file_path=file_path,
            error_type="indexing_failure",
            **extra
        )


class GuardianLogger(GeminiLogger):
    """Specialized logger for Guardian validation operations"""
    
    def __init__(self):
        super().__init__("guardian.validator", "guardian")
    
    def log_validation_start(self, validation_type: str, file_path: str, **extra):
        """Log start of validation"""
        self.info(
            f"Validation started: {validation_type} for {file_path}",
            validation_type=validation_type,
            file_path=file_path,
            validation_start_time=time.time(),
            **extra
        )
    
    def log_validation_complete(self, validation_type: str, file_path: str, 
                              violation_count: int, validation_time_ms: float, **extra):
        """Log validation completion"""
        self.info(
            f"Validation completed: {validation_type}",
            validation_type=validation_type,
            file_path=file_path,
            violation_count=violation_count,
            validation_time_ms=validation_time_ms,
            **extra
        )
    
    def log_violation(self, rule_name: str, severity: str, file_path: str, 
                     line_number: int, message: str, **extra):
        """Log validation violations"""
        self.warning(
            f"Validation violation: {rule_name}",
            rule_name=rule_name,
            severity=severity,
            file_path=file_path,
            line_number=line_number,
            violation_message=message,
            violation=True,
            **extra
        )


class KillerDemoLogger(GeminiLogger):
    """Specialized logger for Killer Demo scaling detection"""
    
    def __init__(self):
        super().__init__("killer_demo.detector", "killer-demo")
    
    def log_scaling_issue_detected(self, issue_type: str, severity: str, file_path: str,
                                  function_name: str, potential_savings_usd: float,
                                  performance_impact_percent: float, detection_confidence: float, **extra):
        """Log detected scaling issues"""
        self.warning(
            f"Scaling issue detected: {issue_type} in {function_name}",
            issue_type=issue_type,
            severity=severity,
            file_path=file_path,
            function_name=function_name,
            potential_savings_usd=potential_savings_usd,
            performance_impact_percent=performance_impact_percent,
            detection_confidence=detection_confidence,
            scaling_issue=True,
            **extra
        )
    
    def log_optimization_recommendation(self, recommendation_type: str, file_path: str,
                                      estimated_impact: str, implementation_effort: str, **extra):
        """Log optimization recommendations"""
        self.info(
            f"Optimization recommended: {recommendation_type}",
            recommendation_type=recommendation_type,
            file_path=file_path,
            estimated_impact=estimated_impact,
            implementation_effort=implementation_effort,
            optimization_recommendation=True,
            **extra
        )


def log_performance(func):
    """Decorator to log function performance metrics"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        function_name = f"{func.__module__}.{func.__name__}"
        
        logger = GeminiLogger("performance", "performance")
        logger.debug(f"Function started: {function_name}")
        
        try:
            result = func(*args, **kwargs)
            duration_ms = (time.time() - start_time) * 1000
            
            logger.info(
                f"Function completed: {function_name}",
                function_name=function_name,
                duration_ms=duration_ms,
                success=True
            )
            
            return result
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            logger.error(
                f"Function failed: {function_name}",
                error=e,
                function_name=function_name,
                duration_ms=duration_ms,
                success=False
            )
            raise
    
    return wrapper


# Global logger instances
agent_logger = lambda agent_type: AgentLogger(agent_type)
scout_logger = ScoutLogger()
guardian_logger = GuardianLogger()
killer_demo_logger = KillerDemoLogger()

# Default logger for general use
logger = GeminiLogger("gemini", "gemini-enterprise")