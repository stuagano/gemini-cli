"""
Guardian Continuous Validation
Real-time validation during development to catch issues before production
Epic 1: Story 1.4 - Guardian Continuous Validation
"""

import asyncio
import time
from typing import Dict, List, Optional, Any, Callable, Set
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
import os
import hashlib
from pathlib import Path

logger = logging.getLogger(__name__)

class ValidationSeverity(Enum):
    """Severity levels for validation issues"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class ValidationCategory(Enum):
    """Categories of validation checks"""
    SECURITY = "security"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    ARCHITECTURE = "architecture"
    TESTING = "testing"
    DEPLOYMENT = "deployment"

@dataclass
class ValidationRule:
    """Individual validation rule"""
    id: str
    name: str
    category: ValidationCategory
    severity: ValidationSeverity
    description: str
    check_function: Callable
    enabled: bool = True
    auto_fix: bool = False
    fix_function: Optional[Callable] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ValidationIssue:
    """Validation issue found during continuous validation"""
    id: str
    rule_id: str
    severity: ValidationSeverity
    category: ValidationCategory
    title: str
    description: str
    file_path: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    code_snippet: Optional[str] = None
    suggestion: Optional[str] = None
    auto_fixable: bool = False
    timestamp: datetime = field(default_factory=datetime.now)
    resolved: bool = False
    resolution_notes: Optional[str] = None

@dataclass
class ValidationReport:
    """Comprehensive validation report"""
    session_id: str
    timestamp: datetime
    duration_seconds: float
    files_checked: int
    rules_executed: int
    issues_found: List[ValidationIssue]
    performance_metrics: Dict[str, Any]
    summary: Dict[ValidationSeverity, int] = field(default_factory=dict)

class ContinuousValidator:
    """Core continuous validation engine"""
    
    def __init__(self):
        self.validation_rules: Dict[str, ValidationRule] = {}
        self.active_watchers = {}
        self.validation_history = []
        self.issue_cache = {}
        self.performance_metrics = {
            'validations_run': 0,
            'issues_found': 0,
            'issues_auto_fixed': 0,
            'avg_validation_time': 0,
            'files_monitored': 0
        }
        
        # Configuration
        self.config = {
            'real_time_validation': True,
            'auto_fix_enabled': True,
            'validation_interval': 5,  # seconds
            'batch_size': 10,  # files to validate per batch
            'exclude_patterns': ['.git/', 'node_modules/', '__pycache__/', '*.pyc'],
            'include_patterns': ['*.py', '*.js', '*.ts', '*.java', '*.go'],
            'severity_thresholds': {
                ValidationSeverity.CRITICAL: 0,  # Block on any critical
                ValidationSeverity.ERROR: 5,     # Block if more than 5 errors
                ValidationSeverity.WARNING: 20   # Block if more than 20 warnings
            }
        }
        
        # Initialize default rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default validation rules"""
        
        # Security rules
        self.add_rule(ValidationRule(
            id="sec_001",
            name="Hardcoded Secrets Detection",
            category=ValidationCategory.SECURITY,
            severity=ValidationSeverity.CRITICAL,
            description="Detect hardcoded passwords, API keys, and secrets",
            check_function=self._check_hardcoded_secrets,
            auto_fix=False
        ))
        
        self.add_rule(ValidationRule(
            id="sec_002",
            name="SQL Injection Risk",
            category=ValidationCategory.SECURITY,
            severity=ValidationSeverity.ERROR,
            description="Detect potential SQL injection vulnerabilities",
            check_function=self._check_sql_injection_risk
        ))
        
        # Performance rules
        self.add_rule(ValidationRule(
            id="perf_001",
            name="N+1 Query Detection",
            category=ValidationCategory.PERFORMANCE,
            severity=ValidationSeverity.WARNING,
            description="Detect potential N+1 query problems",
            check_function=self._check_n_plus_one_queries
        ))
        
        self.add_rule(ValidationRule(
            id="perf_002",
            name="Memory Leak Detection",
            category=ValidationCategory.PERFORMANCE,
            severity=ValidationSeverity.ERROR,
            description="Detect potential memory leaks",
            check_function=self._check_memory_leaks
        ))
        
        # Quality rules
        self.add_rule(ValidationRule(
            id="qual_001",
            name="Code Complexity",
            category=ValidationCategory.QUALITY,
            severity=ValidationSeverity.WARNING,
            description="Check cyclomatic complexity",
            check_function=self._check_code_complexity
        ))
        
        self.add_rule(ValidationRule(
            id="qual_002",
            name="Dead Code Detection",
            category=ValidationCategory.QUALITY,
            severity=ValidationSeverity.INFO,
            description="Detect unused functions and variables",
            check_function=self._check_dead_code,
            auto_fix=True,
            fix_function=self._fix_dead_code
        ))
        
        # Architecture rules
        self.add_rule(ValidationRule(
            id="arch_001",
            name="Dependency Cycle Detection",
            category=ValidationCategory.ARCHITECTURE,
            severity=ValidationSeverity.ERROR,
            description="Detect circular dependencies",
            check_function=self._check_dependency_cycles
        ))
        
        self.add_rule(ValidationRule(
            id="arch_002",
            name="Layer Violation Detection",
            category=ValidationCategory.ARCHITECTURE,
            severity=ValidationSeverity.WARNING,
            description="Detect architectural layer violations",
            check_function=self._check_layer_violations
        ))
        
        # Testing rules
        self.add_rule(ValidationRule(
            id="test_001",
            name="Test Coverage Check",
            category=ValidationCategory.TESTING,
            severity=ValidationSeverity.WARNING,
            description="Check test coverage requirements",
            check_function=self._check_test_coverage
        ))
        
        logger.info(f"Initialized {len(self.validation_rules)} default validation rules")
    
    def add_rule(self, rule: ValidationRule):
        """Add a validation rule"""
        self.validation_rules[rule.id] = rule
        logger.debug(f"Added validation rule: {rule.name}")
    
    def remove_rule(self, rule_id: str) -> bool:
        """Remove a validation rule"""
        if rule_id in self.validation_rules:
            del self.validation_rules[rule_id]
            logger.debug(f"Removed validation rule: {rule_id}")
            return True
        return False
    
    def enable_rule(self, rule_id: str) -> bool:
        """Enable a validation rule"""
        if rule_id in self.validation_rules:
            self.validation_rules[rule_id].enabled = True
            return True
        return False
    
    def disable_rule(self, rule_id: str) -> bool:
        """Disable a validation rule"""
        if rule_id in self.validation_rules:
            self.validation_rules[rule_id].enabled = False
            return True
        return False
    
    async def validate_file(
        self,
        file_path: str,
        rules: Optional[List[str]] = None
    ) -> List[ValidationIssue]:
        """Validate a single file"""
        issues = []
        
        if not os.path.exists(file_path):
            return issues
        
        # Check if file should be excluded
        if self._should_exclude_file(file_path):
            return issues
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            logger.warning(f"Could not read {file_path}: {e}")
            return issues
        
        # Determine which rules to run
        rules_to_run = rules if rules else list(self.validation_rules.keys())
        
        # Run validation rules
        for rule_id in rules_to_run:
            if rule_id not in self.validation_rules:
                continue
            
            rule = self.validation_rules[rule_id]
            if not rule.enabled:
                continue
            
            try:
                rule_issues = await rule.check_function(file_path, content)
                issues.extend(rule_issues)
            except Exception as e:
                logger.error(f"Error running rule {rule_id} on {file_path}: {e}")
        
        return issues
    
    async def validate_project(
        self,
        project_path: str = ".",
        rules: Optional[List[str]] = None
    ) -> ValidationReport:
        """Validate entire project"""
        start_time = time.time()
        session_id = f"validation_{int(start_time)}"
        
        logger.info(f"Starting project validation: {session_id}")
        
        # Find files to validate
        files_to_check = self._find_files_to_validate(project_path)
        
        all_issues = []
        files_checked = 0
        
        # Validate files in batches
        batch_size = self.config['batch_size']
        
        for i in range(0, len(files_to_check), batch_size):
            batch = files_to_check[i:i + batch_size]
            
            # Process batch concurrently
            tasks = [self.validate_file(file_path, rules) for file_path in batch]
            batch_results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for result in batch_results:
                if isinstance(result, Exception):
                    logger.error(f"Validation error: {result}")
                else:
                    all_issues.extend(result)
                    files_checked += 1
            
            # Small delay between batches to prevent overwhelming
            await asyncio.sleep(0.1)
        
        duration = time.time() - start_time
        
        # Create report
        report = ValidationReport(
            session_id=session_id,
            timestamp=datetime.now(),
            duration_seconds=duration,
            files_checked=files_checked,
            rules_executed=len(rules or self.validation_rules),
            issues_found=all_issues,
            performance_metrics={
                'files_per_second': files_checked / duration if duration > 0 else 0,
                'issues_per_file': len(all_issues) / files_checked if files_checked > 0 else 0
            }
        )
        
        # Calculate summary
        for issue in all_issues:
            severity = issue.severity
            report.summary[severity] = report.summary.get(severity, 0) + 1
        
        # Update metrics
        self.performance_metrics['validations_run'] += 1
        self.performance_metrics['issues_found'] += len(all_issues)
        self.performance_metrics['files_monitored'] = files_checked
        
        # Store in history
        self.validation_history.append(report)
        
        logger.info(f"Validation complete: {len(all_issues)} issues found in {duration:.2f}s")
        
        return report
    
    async def start_continuous_validation(self, project_path: str = "."):
        """Start continuous validation with file watching"""
        logger.info("Starting continuous validation")
        
        if not self.config['real_time_validation']:
            logger.info("Real-time validation is disabled")
            return
        
        # Start file watchers
        await self._start_file_watchers(project_path)
        
        # Start periodic validation
        while True:
            try:
                await self._periodic_validation(project_path)
                await asyncio.sleep(self.config['validation_interval'])
            except KeyboardInterrupt:
                logger.info("Stopping continuous validation")
                break
            except Exception as e:
                logger.error(f"Error in continuous validation: {e}")
                await asyncio.sleep(self.config['validation_interval'])
    
    async def _periodic_validation(self, project_path: str):
        """Run periodic validation"""
        # Get recently changed files
        changed_files = self._get_recently_changed_files(project_path)
        
        if not changed_files:
            return
        
        logger.debug(f"Validating {len(changed_files)} changed files")
        
        # Validate changed files
        all_issues = []
        for file_path in changed_files:
            issues = await self.validate_file(file_path)
            all_issues.extend(issues)
            
            # Auto-fix if enabled and possible
            if self.config['auto_fix_enabled']:
                await self._attempt_auto_fixes(file_path, issues)
        
        # Report issues if found
        if all_issues:
            await self._report_issues(all_issues)
    
    async def _start_file_watchers(self, project_path: str):
        """Start file system watchers"""
        # This is a simplified implementation
        # In production, you'd use a proper file watching library
        logger.info("File watchers started (simplified implementation)")
    
    def _get_recently_changed_files(self, project_path: str) -> List[str]:
        """Get files that have been recently changed"""
        # Simplified implementation - in production, this would use file system events
        return []
    
    async def _attempt_auto_fixes(self, file_path: str, issues: List[ValidationIssue]):
        """Attempt to auto-fix issues"""
        auto_fixed = 0
        
        for issue in issues:
            if not issue.auto_fixable:
                continue
            
            rule = self.validation_rules.get(issue.rule_id)
            if not rule or not rule.auto_fix or not rule.fix_function:
                continue
            
            try:
                success = await rule.fix_function(file_path, issue)
                if success:
                    issue.resolved = True
                    issue.resolution_notes = "Auto-fixed by Guardian"
                    auto_fixed += 1
                    logger.info(f"Auto-fixed issue {issue.id} in {file_path}")
            except Exception as e:
                logger.error(f"Error auto-fixing issue {issue.id}: {e}")
        
        if auto_fixed > 0:
            self.performance_metrics['issues_auto_fixed'] += auto_fixed
            logger.info(f"Auto-fixed {auto_fixed} issues in {file_path}")
    
    async def _report_issues(self, issues: List[ValidationIssue]):
        """Report validation issues"""
        # Group by severity
        by_severity = {}
        for issue in issues:
            severity = issue.severity
            if severity not in by_severity:
                by_severity[severity] = []
            by_severity[severity].append(issue)
        
        # Report each severity level
        for severity, severity_issues in by_severity.items():
            logger.warning(f"Found {len(severity_issues)} {severity.value} issues")
            
            # Show first few issues
            for issue in severity_issues[:3]:
                logger.warning(f"  {issue.title} in {issue.file_path}")
    
    def _find_files_to_validate(self, project_path: str) -> List[str]:
        """Find files that should be validated"""
        files = []
        
        for root, dirs, filenames in os.walk(project_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if not any(
                pattern in os.path.join(root, d) 
                for pattern in self.config['exclude_patterns']
            )]
            
            for filename in filenames:
                file_path = os.path.join(root, filename)
                
                if self._should_include_file(file_path):
                    files.append(file_path)
        
        return files
    
    def _should_include_file(self, file_path: str) -> bool:
        """Check if file should be included in validation"""
        # Check include patterns
        for pattern in self.config['include_patterns']:
            if file_path.endswith(pattern.replace('*', '')):
                return True
        
        return False
    
    def _should_exclude_file(self, file_path: str) -> bool:
        """Check if file should be excluded from validation"""
        for pattern in self.config['exclude_patterns']:
            if pattern in file_path:
                return True
        
        return False
    
    def get_validation_status(self) -> Dict[str, Any]:
        """Get current validation status"""
        recent_reports = self.validation_history[-5:]  # Last 5 reports
        
        total_issues = sum(len(report.issues_found) for report in recent_reports)
        
        return {
            "active_rules": len([r for r in self.validation_rules.values() if r.enabled]),
            "total_rules": len(self.validation_rules),
            "recent_validations": len(recent_reports),
            "recent_issues": total_issues,
            "auto_fix_enabled": self.config['auto_fix_enabled'],
            "real_time_validation": self.config['real_time_validation'],
            "performance_metrics": self.performance_metrics
        }
    
    # Validation rule implementations
    
    async def _check_hardcoded_secrets(self, file_path: str, content: str) -> List[ValidationIssue]:
        """Check for hardcoded secrets"""
        issues = []
        
        # Common secret patterns
        secret_patterns = [
            (r'password\s*=\s*["\']([^"\']+)["\']', "Hardcoded password detected"),
            (r'api[_-]?key\s*=\s*["\']([^"\']+)["\']', "Hardcoded API key detected"),
            (r'secret\s*=\s*["\']([^"\']+)["\']', "Hardcoded secret detected"),
            (r'token\s*=\s*["\']([^"\']+)["\']', "Hardcoded token detected"),
        ]
        
        import re
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern, message in secret_patterns:
                matches = re.finditer(pattern, line, re.IGNORECASE)
                for match in matches:
                    secret_value = match.group(1)
                    
                    # Skip obvious placeholders
                    if secret_value.lower() in ['your_password', 'your_api_key', 'placeholder', 'xxx']:
                        continue
                    
                    issue_id = hashlib.md5(f"{file_path}:{line_num}:{message}".encode()).hexdigest()[:8]
                    
                    issues.append(ValidationIssue(
                        id=issue_id,
                        rule_id="sec_001",
                        severity=ValidationSeverity.CRITICAL,
                        category=ValidationCategory.SECURITY,
                        title="Hardcoded Secret",
                        description=message,
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=line.strip(),
                        suggestion="Use environment variables or secure configuration management"
                    ))
        
        return issues
    
    async def _check_sql_injection_risk(self, file_path: str, content: str) -> List[ValidationIssue]:
        """Check for SQL injection risks"""
        issues = []
        
        # Look for string concatenation in SQL queries
        sql_patterns = [
            r'SELECT.*\+.*',
            r'INSERT.*\+.*',
            r'UPDATE.*\+.*',
            r'DELETE.*\+.*',
            r'query.*\+.*',
            r'execute\s*\(.*\+.*\)'
        ]
        
        import re
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern in sql_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    issue_id = hashlib.md5(f"{file_path}:{line_num}:sql_injection".encode()).hexdigest()[:8]
                    
                    issues.append(ValidationIssue(
                        id=issue_id,
                        rule_id="sec_002",
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.SECURITY,
                        title="Potential SQL Injection",
                        description="SQL query uses string concatenation",
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=line.strip(),
                        suggestion="Use parameterized queries or prepared statements"
                    ))
        
        return issues
    
    async def _check_n_plus_one_queries(self, file_path: str, content: str) -> List[ValidationIssue]:
        """Check for N+1 query problems"""
        issues = []
        
        # Look for queries inside loops
        import re
        
        lines = content.split('\n')
        in_loop = False
        loop_start = 0
        
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip().lower()
            
            # Detect loop start
            if any(keyword in line_stripped for keyword in ['for ', 'while ', 'foreach']):
                in_loop = True
                loop_start = line_num
            
            # Detect loop end (simplified)
            if in_loop and line_stripped == '}':
                in_loop = False
            
            # Check for database queries in loop
            if in_loop and any(keyword in line_stripped for keyword in ['.get(', '.find(', '.query(', 'select ']):
                issue_id = hashlib.md5(f"{file_path}:{line_num}:n_plus_one".encode()).hexdigest()[:8]
                
                issues.append(ValidationIssue(
                    id=issue_id,
                    rule_id="perf_001",
                    severity=ValidationSeverity.WARNING,
                    category=ValidationCategory.PERFORMANCE,
                    title="Potential N+1 Query",
                    description="Database query inside loop detected",
                    file_path=file_path,
                    line_number=line_num,
                    code_snippet=line.strip(),
                    suggestion="Consider batch loading or eager loading"
                ))
        
        return issues
    
    async def _check_memory_leaks(self, file_path: str, content: str) -> List[ValidationIssue]:
        """Check for potential memory leaks"""
        issues = []
        
        # Look for common memory leak patterns
        leak_patterns = [
            (r'setInterval\([^)]+\)', "setInterval without clearInterval"),
            (r'addEventListener\([^)]+\)', "Event listener without removal"),
            (r'new\s+\w+\([^)]*\)(?!.*\.close\(\))', "Resource creation without cleanup"),
        ]
        
        import re
        
        lines = content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern, description in leak_patterns:
                if re.search(pattern, line):
                    issue_id = hashlib.md5(f"{file_path}:{line_num}:memory_leak".encode()).hexdigest()[:8]
                    
                    issues.append(ValidationIssue(
                        id=issue_id,
                        rule_id="perf_002",
                        severity=ValidationSeverity.ERROR,
                        category=ValidationCategory.PERFORMANCE,
                        title="Potential Memory Leak",
                        description=description,
                        file_path=file_path,
                        line_number=line_num,
                        code_snippet=line.strip(),
                        suggestion="Ensure proper cleanup of resources"
                    ))
        
        return issues
    
    async def _check_code_complexity(self, file_path: str, content: str) -> List[ValidationIssue]:
        """Check code complexity"""
        issues = []
        
        # Simple complexity calculation
        complexity_keywords = ['if', 'elif', 'else', 'for', 'while', 'try', 'except', 'and', 'or']
        
        lines = content.split('\n')
        current_function = None
        function_complexity = 0
        function_start_line = 0
        
        import re
        
        for line_num, line in enumerate(lines, 1):
            line_stripped = line.strip().lower()
            
            # Detect function start
            func_match = re.match(r'def\s+(\w+)', line_stripped)
            if func_match:
                # Report previous function if complex
                if current_function and function_complexity > 10:
                    issue_id = hashlib.md5(f"{file_path}:{function_start_line}:complexity".encode()).hexdigest()[:8]
                    
                    issues.append(ValidationIssue(
                        id=issue_id,
                        rule_id="qual_001",
                        severity=ValidationSeverity.WARNING,
                        category=ValidationCategory.QUALITY,
                        title="High Code Complexity",
                        description=f"Function '{current_function}' has complexity {function_complexity}",
                        file_path=file_path,
                        line_number=function_start_line,
                        suggestion="Consider breaking down into smaller functions"
                    ))
                
                # Start tracking new function
                current_function = func_match.group(1)
                function_complexity = 1  # Base complexity
                function_start_line = line_num
            
            # Count complexity keywords
            if current_function:
                for keyword in complexity_keywords:
                    function_complexity += line_stripped.count(keyword)
        
        # Check final function
        if current_function and function_complexity > 10:
            issue_id = hashlib.md5(f"{file_path}:{function_start_line}:complexity".encode()).hexdigest()[:8]
            
            issues.append(ValidationIssue(
                id=issue_id,
                rule_id="qual_001",
                severity=ValidationSeverity.WARNING,
                category=ValidationCategory.QUALITY,
                title="High Code Complexity",
                description=f"Function '{current_function}' has complexity {function_complexity}",
                file_path=file_path,
                line_number=function_start_line,
                suggestion="Consider breaking down into smaller functions"
            ))
        
        return issues
    
    async def _check_dead_code(self, file_path: str, content: str) -> List[ValidationIssue]:
        """Check for dead/unused code"""
        issues = []
        
        # Simple dead code detection (functions that are defined but never called)
        import re
        
        # Find all function definitions
        function_defs = re.findall(r'def\s+(\w+)', content)
        
        # Find all function calls
        function_calls = set()
        for match in re.finditer(r'(\w+)\s*\(', content):
            function_calls.add(match.group(1))
        
        lines = content.split('\n')
        
        # Check for unused functions
        for func_name in function_defs:
            if func_name not in function_calls and not func_name.startswith('_'):
                # Find line number of function definition
                for line_num, line in enumerate(lines, 1):
                    if f'def {func_name}' in line:
                        issue_id = hashlib.md5(f"{file_path}:{line_num}:dead_code".encode()).hexdigest()[:8]
                        
                        issues.append(ValidationIssue(
                            id=issue_id,
                            rule_id="qual_002",
                            severity=ValidationSeverity.INFO,
                            category=ValidationCategory.QUALITY,
                            title="Unused Function",
                            description=f"Function '{func_name}' is defined but never called",
                            file_path=file_path,
                            line_number=line_num,
                            code_snippet=line.strip(),
                            suggestion="Remove unused function or add call",
                            auto_fixable=True
                        ))
                        break
        
        return issues
    
    async def _fix_dead_code(self, file_path: str, issue: ValidationIssue) -> bool:
        """Auto-fix dead code by commenting it out"""
        try:
            with open(file_path, 'r') as f:
                lines = f.readlines()
            
            # Comment out the function (simplified)
            if issue.line_number and issue.line_number <= len(lines):
                line_idx = issue.line_number - 1
                lines[line_idx] = f"# UNUSED: {lines[line_idx]}"
                
                with open(file_path, 'w') as f:
                    f.writelines(lines)
                
                return True
        except Exception as e:
            logger.error(f"Error fixing dead code: {e}")
        
        return False
    
    async def _check_dependency_cycles(self, file_path: str, content: str) -> List[ValidationIssue]:
        """Check for dependency cycles"""
        # This would require more sophisticated analysis
        # For now, return empty list
        return []
    
    async def _check_layer_violations(self, file_path: str, content: str) -> List[ValidationIssue]:
        """Check for architectural layer violations"""
        # This would require configuration of layer rules
        # For now, return empty list
        return []
    
    async def _check_test_coverage(self, file_path: str, content: str) -> List[ValidationIssue]:
        """Check test coverage"""
        # This would integrate with coverage tools
        # For now, return empty list
        return []

class GuardianIntegration:
    """Integration with other systems"""
    
    def __init__(self, validator: ContinuousValidator):
        self.validator = validator
        self.blocking_thresholds = {
            ValidationSeverity.CRITICAL: 0,
            ValidationSeverity.ERROR: 5,
            ValidationSeverity.WARNING: 20
        }
    
    async def validate_before_commit(self, changed_files: List[str]) -> Dict[str, Any]:
        """Validate changes before commit"""
        logger.info("Running pre-commit validation")
        
        all_issues = []
        for file_path in changed_files:
            issues = await self.validator.validate_file(file_path)
            all_issues.extend(issues)
        
        # Check blocking conditions
        should_block = self._should_block_commit(all_issues)
        
        return {
            "validation_passed": not should_block,
            "issues_found": len(all_issues),
            "issues": [
                {
                    "severity": issue.severity.value,
                    "title": issue.title,
                    "file": issue.file_path,
                    "line": issue.line_number
                }
                for issue in all_issues
            ],
            "blocking_reason": self._get_blocking_reason(all_issues) if should_block else None
        }
    
    async def validate_before_deploy(self, deployment_target: str) -> Dict[str, Any]:
        """Validate before deployment"""
        logger.info(f"Running pre-deployment validation for {deployment_target}")
        
        report = await self.validator.validate_project()
        
        # More strict validation for production
        strict_thresholds = {
            ValidationSeverity.CRITICAL: 0,
            ValidationSeverity.ERROR: 0,
            ValidationSeverity.WARNING: 5
        } if deployment_target == "production" else self.blocking_thresholds
        
        should_block = self._should_block_deployment(report.issues_found, strict_thresholds)
        
        return {
            "deployment_approved": not should_block,
            "validation_report": report,
            "blocking_reason": self._get_deployment_blocking_reason(
                report.issues_found, strict_thresholds
            ) if should_block else None
        }
    
    def _should_block_commit(self, issues: List[ValidationIssue]) -> bool:
        """Determine if commit should be blocked"""
        issue_counts = {}
        for issue in issues:
            severity = issue.severity
            issue_counts[severity] = issue_counts.get(severity, 0) + 1
        
        for severity, count in issue_counts.items():
            threshold = self.blocking_thresholds.get(severity, float('inf'))
            if count > threshold:
                return True
        
        return False
    
    def _should_block_deployment(
        self,
        issues: List[ValidationIssue],
        thresholds: Dict[ValidationSeverity, int]
    ) -> bool:
        """Determine if deployment should be blocked"""
        issue_counts = {}
        for issue in issues:
            severity = issue.severity
            issue_counts[severity] = issue_counts.get(severity, 0) + 1
        
        for severity, count in issue_counts.items():
            threshold = thresholds.get(severity, float('inf'))
            if count > threshold:
                return True
        
        return False
    
    def _get_blocking_reason(self, issues: List[ValidationIssue]) -> str:
        """Get reason for blocking commit"""
        issue_counts = {}
        for issue in issues:
            severity = issue.severity
            issue_counts[severity] = issue_counts.get(severity, 0) + 1
        
        reasons = []
        for severity, count in issue_counts.items():
            threshold = self.blocking_thresholds.get(severity, float('inf'))
            if count > threshold:
                reasons.append(f"{count} {severity.value} issues (threshold: {threshold})")
        
        return "Commit blocked due to: " + ", ".join(reasons)
    
    def _get_deployment_blocking_reason(
        self,
        issues: List[ValidationIssue],
        thresholds: Dict[ValidationSeverity, int]
    ) -> str:
        """Get reason for blocking deployment"""
        issue_counts = {}
        for issue in issues:
            severity = issue.severity
            issue_counts[severity] = issue_counts.get(severity, 0) + 1
        
        reasons = []
        for severity, count in issue_counts.items():
            threshold = thresholds.get(severity, float('inf'))
            if count > threshold:
                reasons.append(f"{count} {severity.value} issues (threshold: {threshold})")
        
        return "Deployment blocked due to: " + ", ".join(reasons)

# Global instances
guardian_validator = ContinuousValidator()
guardian_integration = GuardianIntegration(guardian_validator)

# Example usage
async def example_usage():
    """Example of Guardian continuous validation"""
    
    # Configure Guardian
    guardian_validator.config.update({
        'auto_fix_enabled': True,
        'real_time_validation': True,
        'validation_interval': 10
    })
    
    # Validate a single file
    issues = await guardian_validator.validate_file("src/example.py")
    print(f"Found {len(issues)} issues in single file")
    
    for issue in issues:
        print(f"  {issue.severity.value}: {issue.title}")
    
    # Validate entire project
    report = await guardian_validator.validate_project()
    print(f"Project validation: {len(report.issues_found)} issues in {report.duration_seconds:.2f}s")
    
    # Get validation status
    status = guardian_validator.get_validation_status()
    print(f"Validation status: {status}")
    
    # Test pre-commit validation
    commit_result = await guardian_integration.validate_before_commit(["src/example.py"])
    print(f"Pre-commit validation: {'PASSED' if commit_result['validation_passed'] else 'BLOCKED'}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    asyncio.run(example_usage())