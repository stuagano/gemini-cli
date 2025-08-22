"""
Guardian Validation Pipeline
Comprehensive validation system for code quality, security, and performance
"""

import asyncio
import logging
import subprocess
import json
import ast
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)

@dataclass
class ValidationContext:
    """Context for validation operations"""
    file_path: str
    content: str
    language: str
    previous_content: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ValidationIssue:
    """Represents a validation issue"""
    severity: str  # info, warning, error, critical
    category: str  # syntax, style, security, performance, breaking_change
    message: str
    line: Optional[int] = None
    column: Optional[int] = None
    rule: Optional[str] = None
    suggestion: Optional[str] = None
    code_snippet: Optional[str] = None

@dataclass
class ValidationReport:
    """Complete validation report for a file"""
    file_path: str
    status: str  # passed, failed, warning
    issues: List[ValidationIssue]
    metrics: Dict[str, Any]
    validated_at: datetime = field(default_factory=datetime.now)
    duration_ms: int = 0

class Validator(ABC):
    """Base class for all validators"""
    
    @abstractmethod
    async def validate(self, context: ValidationContext) -> List[ValidationIssue]:
        """Perform validation and return issues"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Validator name"""
        pass
    
    @property
    def supported_languages(self) -> List[str]:
        """Languages supported by this validator"""
        return []

class SyntaxValidator(Validator):
    """Validates syntax for various languages"""
    
    @property
    def name(self) -> str:
        return "syntax"
    
    @property
    def supported_languages(self) -> List[str]:
        return ['python', 'javascript', 'typescript', 'go', 'java']
    
    async def validate(self, context: ValidationContext) -> List[ValidationIssue]:
        """Check syntax based on language"""
        issues = []
        
        if context.language == 'python':
            issues.extend(await self._validate_python(context))
        elif context.language in ['javascript', 'typescript']:
            issues.extend(await self._validate_javascript(context))
        elif context.language == 'go':
            issues.extend(await self._validate_go(context))
        
        return issues
    
    async def _validate_python(self, context: ValidationContext) -> List[ValidationIssue]:
        """Validate Python syntax"""
        issues = []
        try:
            ast.parse(context.content)
        except SyntaxError as e:
            issues.append(ValidationIssue(
                severity='error',
                category='syntax',
                message=f"Syntax error: {e.msg}",
                line=e.lineno,
                column=e.offset,
                rule='python_syntax'
            ))
        return issues
    
    async def _validate_javascript(self, context: ValidationContext) -> List[ValidationIssue]:
        """Validate JavaScript/TypeScript syntax"""
        # Would integrate with ESLint or similar
        return []
    
    async def _validate_go(self, context: ValidationContext) -> List[ValidationIssue]:
        """Validate Go syntax"""
        # Would run go fmt -e
        return []

class SecurityValidator(Validator):
    """Validates security issues"""
    
    @property
    def name(self) -> str:
        return "security"
    
    async def validate(self, context: ValidationContext) -> List[ValidationIssue]:
        """Check for security vulnerabilities"""
        issues = []
        
        # Check for hardcoded secrets
        issues.extend(self._check_secrets(context))
        
        # Check for SQL injection
        if 'sql' in context.content.lower():
            issues.extend(self._check_sql_injection(context))
        
        # Check for unsafe functions
        issues.extend(self._check_unsafe_functions(context))
        
        return issues
    
    def _check_secrets(self, context: ValidationContext) -> List[ValidationIssue]:
        """Check for hardcoded secrets"""
        issues = []
        
        # Common secret patterns
        secret_patterns = [
            (r'(?i)(api[_-]?key|apikey)\s*=\s*["\'][\w\-]+["\']', 'API key'),
            (r'(?i)(secret|password|passwd|pwd)\s*=\s*["\'][\w\-]+["\']', 'Password'),
            (r'(?i)aws_access_key_id\s*=\s*["\'][\w\-]+["\']', 'AWS key'),
            (r'(?i)private[_-]?key\s*=\s*["\'][\w\-]+["\']', 'Private key'),
            (r'(?i)token\s*=\s*["\'][A-Za-z0-9\-._~+/]+["\']', 'Token'),
        ]
        
        lines = context.content.split('\n')
        for line_num, line in enumerate(lines, 1):
            for pattern, secret_type in secret_patterns:
                if re.search(pattern, line):
                    issues.append(ValidationIssue(
                        severity='critical',
                        category='security',
                        message=f"Potential {secret_type} found in code",
                        line=line_num,
                        rule='no_hardcoded_secrets',
                        suggestion=f"Use environment variables or secure key management for {secret_type}"
                    ))
        
        return issues
    
    def _check_sql_injection(self, context: ValidationContext) -> List[ValidationIssue]:
        """Check for SQL injection vulnerabilities"""
        issues = []
        
        # Look for string concatenation in SQL queries
        sql_concat_pattern = r'(SELECT|INSERT|UPDATE|DELETE|FROM|WHERE).*?\+.*?["\']'
        
        lines = context.content.split('\n')
        for line_num, line in enumerate(lines, 1):
            if re.search(sql_concat_pattern, line, re.IGNORECASE):
                issues.append(ValidationIssue(
                    severity='critical',
                    category='security',
                    message="Potential SQL injection vulnerability",
                    line=line_num,
                    rule='sql_injection',
                    suggestion="Use parameterized queries or prepared statements"
                ))
        
        return issues
    
    def _check_unsafe_functions(self, context: ValidationContext) -> List[ValidationIssue]:
        """Check for unsafe function usage"""
        issues = []
        
        unsafe_functions = {
            'python': ['eval', 'exec', 'compile', '__import__'],
            'javascript': ['eval', 'innerHTML', 'document.write'],
            'php': ['eval', 'exec', 'system', 'shell_exec']
        }
        
        if context.language in unsafe_functions:
            funcs = unsafe_functions[context.language]
            lines = context.content.split('\n')
            
            for line_num, line in enumerate(lines, 1):
                for func in funcs:
                    if func in line:
                        issues.append(ValidationIssue(
                            severity='warning',
                            category='security',
                            message=f"Use of potentially unsafe function: {func}",
                            line=line_num,
                            rule='no_unsafe_functions',
                            suggestion=f"Consider safer alternatives to {func}"
                        ))
        
        return issues

class PerformanceValidator(Validator):
    """Validates performance issues"""
    
    @property
    def name(self) -> str:
        return "performance"
    
    async def validate(self, context: ValidationContext) -> List[ValidationIssue]:
        """Check for performance issues"""
        issues = []
        
        # Check for N+1 queries
        issues.extend(self._check_n_plus_one(context))
        
        # Check for inefficient loops
        issues.extend(self._check_inefficient_loops(context))
        
        # Check for memory leaks
        issues.extend(self._check_memory_leaks(context))
        
        return issues
    
    def _check_n_plus_one(self, context: ValidationContext) -> List[ValidationIssue]:
        """Check for N+1 query patterns"""
        issues = []
        
        # Look for loops with database queries
        loop_with_query_pattern = r'for\s+.*?\n.*?(query|select|find|fetch|get)'
        
        if re.search(loop_with_query_pattern, context.content, re.IGNORECASE | re.MULTILINE):
            issues.append(ValidationIssue(
                severity='warning',
                category='performance',
                message="Potential N+1 query problem detected",
                rule='n_plus_one',
                suggestion="Consider using eager loading or batch queries"
            ))
        
        return issues
    
    def _check_inefficient_loops(self, context: ValidationContext) -> List[ValidationIssue]:
        """Check for inefficient loop patterns"""
        issues = []
        
        # Check for nested loops with high complexity
        nested_loop_pattern = r'for\s+.*?\n.*?for\s+'
        
        if re.search(nested_loop_pattern, context.content, re.MULTILINE):
            issues.append(ValidationIssue(
                severity='info',
                category='performance',
                message="Nested loops detected - review for optimization opportunities",
                rule='nested_loops',
                suggestion="Consider using more efficient algorithms or data structures"
            ))
        
        return issues
    
    def _check_memory_leaks(self, context: ValidationContext) -> List[ValidationIssue]:
        """Check for potential memory leaks"""
        issues = []
        
        # Language-specific checks
        if context.language == 'javascript':
            # Check for event listeners without cleanup
            if 'addEventListener' in context.content and 'removeEventListener' not in context.content:
                issues.append(ValidationIssue(
                    severity='warning',
                    category='performance',
                    message="Event listeners added without cleanup",
                    rule='memory_leak',
                    suggestion="Ensure event listeners are removed when no longer needed"
                ))
        
        return issues

class BreakingChangeDetector(Validator):
    """Detects breaking changes in code"""
    
    @property
    def name(self) -> str:
        return "breaking_change"
    
    async def validate(self, context: ValidationContext) -> List[ValidationIssue]:
        """Detect breaking changes"""
        issues = []
        
        if not context.previous_content:
            return issues
        
        # Check for removed functions
        issues.extend(self._check_removed_functions(context))
        
        # Check for signature changes
        issues.extend(self._check_signature_changes(context))
        
        # Check for removed exports
        issues.extend(self._check_removed_exports(context))
        
        return issues
    
    def _check_removed_functions(self, context: ValidationContext) -> List[ValidationIssue]:
        """Check for removed functions"""
        issues = []
        
        # Extract function names from previous content
        prev_functions = re.findall(r'(?:def|function|func)\s+(\w+)', context.previous_content)
        curr_functions = re.findall(r'(?:def|function|func)\s+(\w+)', context.content)
        
        removed = set(prev_functions) - set(curr_functions)
        
        for func in removed:
            issues.append(ValidationIssue(
                severity='error',
                category='breaking_change',
                message=f"Function '{func}' has been removed",
                rule='function_removed',
                suggestion="Consider deprecating the function first or providing a migration path"
            ))
        
        return issues
    
    def _check_signature_changes(self, context: ValidationContext) -> List[ValidationIssue]:
        """Check for function signature changes"""
        issues = []
        
        # Extract function signatures
        prev_sigs = re.findall(r'(?:def|function)\s+(\w+)\s*\((.*?)\)', context.previous_content)
        curr_sigs = re.findall(r'(?:def|function)\s+(\w+)\s*\((.*?)\)', context.content)
        
        prev_dict = dict(prev_sigs)
        curr_dict = dict(curr_sigs)
        
        for func_name in set(prev_dict.keys()) & set(curr_dict.keys()):
            if prev_dict[func_name] != curr_dict[func_name]:
                issues.append(ValidationIssue(
                    severity='warning',
                    category='breaking_change',
                    message=f"Function signature changed for '{func_name}'",
                    rule='signature_changed',
                    suggestion="Ensure backward compatibility or update all callers"
                ))
        
        return issues
    
    def _check_removed_exports(self, context: ValidationContext) -> List[ValidationIssue]:
        """Check for removed exports/imports"""
        issues = []
        
        # Check for removed exports in JavaScript/TypeScript
        if context.language in ['javascript', 'typescript']:
            prev_exports = re.findall(r'export\s+(?:const|let|var|function|class)\s+(\w+)', 
                                     context.previous_content)
            curr_exports = re.findall(r'export\s+(?:const|let|var|function|class)\s+(\w+)', 
                                     context.content)
            
            removed = set(prev_exports) - set(curr_exports)
            
            for export in removed:
                issues.append(ValidationIssue(
                    severity='error',
                    category='breaking_change',
                    message=f"Export '{export}' has been removed",
                    rule='export_removed',
                    suggestion="This may break dependent modules"
                ))
        
        return issues

class ValidationPipeline:
    """Orchestrates validation across multiple validators"""
    
    def __init__(self):
        self.validators: List[Validator] = [
            SyntaxValidator(),
            SecurityValidator(),
            PerformanceValidator(),
            BreakingChangeDetector()
        ]
        self.cache: Dict[str, ValidationReport] = {}
    
    async def validate_file(self, 
                           file_path: str,
                           content: Optional[str] = None,
                           previous_content: Optional[str] = None) -> ValidationReport:
        """Run all validators on a file"""
        start_time = datetime.now()
        
        # Read content if not provided
        if content is None:
            with open(file_path, 'r') as f:
                content = f.read()
        
        # Determine language
        language = self._detect_language(file_path)
        
        # Create context
        context = ValidationContext(
            file_path=file_path,
            content=content,
            language=language,
            previous_content=previous_content
        )
        
        # Run validators
        all_issues = []
        for validator in self.validators:
            if not validator.supported_languages or language in validator.supported_languages:
                try:
                    issues = await validator.validate(context)
                    all_issues.extend(issues)
                except Exception as e:
                    logger.error(f"Validator {validator.name} failed: {e}")
        
        # Calculate metrics
        metrics = self._calculate_metrics(content, all_issues)
        
        # Determine overall status
        status = self._determine_status(all_issues)
        
        # Create report
        report = ValidationReport(
            file_path=file_path,
            status=status,
            issues=all_issues,
            metrics=metrics,
            duration_ms=int((datetime.now() - start_time).total_seconds() * 1000)
        )
        
        # Cache report
        self.cache[file_path] = report
        
        return report
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension"""
        ext_to_lang = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.go': 'go',
            '.rs': 'rust',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.sql': 'sql'
        }
        
        ext = Path(file_path).suffix
        return ext_to_lang.get(ext, 'unknown')
    
    def _calculate_metrics(self, content: str, issues: List[ValidationIssue]) -> Dict[str, Any]:
        """Calculate validation metrics"""
        lines = content.split('\n')
        
        return {
            'total_lines': len(lines),
            'total_issues': len(issues),
            'critical_issues': sum(1 for i in issues if i.severity == 'critical'),
            'error_issues': sum(1 for i in issues if i.severity == 'error'),
            'warning_issues': sum(1 for i in issues if i.severity == 'warning'),
            'info_issues': sum(1 for i in issues if i.severity == 'info'),
            'security_issues': sum(1 for i in issues if i.category == 'security'),
            'performance_issues': sum(1 for i in issues if i.category == 'performance'),
            'breaking_changes': sum(1 for i in issues if i.category == 'breaking_change')
        }
    
    def _determine_status(self, issues: List[ValidationIssue]) -> str:
        """Determine overall validation status"""
        if any(i.severity == 'critical' for i in issues):
            return 'failed'
        elif any(i.severity == 'error' for i in issues):
            return 'failed'
        elif any(i.severity == 'warning' for i in issues):
            return 'warning'
        else:
            return 'passed'
    
    def get_cached_report(self, file_path: str) -> Optional[ValidationReport]:
        """Get cached validation report"""
        return self.cache.get(file_path)
    
    def clear_cache(self, file_path: Optional[str] = None):
        """Clear validation cache"""
        if file_path:
            self.cache.pop(file_path, None)
        else:
            self.cache.clear()

# Singleton instance
_pipeline_instance: Optional[ValidationPipeline] = None

def get_validation_pipeline() -> ValidationPipeline:
    """Get or create validation pipeline instance"""
    global _pipeline_instance
    if _pipeline_instance is None:
        _pipeline_instance = ValidationPipeline()
    return _pipeline_instance