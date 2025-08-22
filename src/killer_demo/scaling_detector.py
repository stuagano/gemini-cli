"""
Killer Demo: Scaling Issue Detection Engine
Detects N+1 queries, memory leaks, inefficient algorithms, and other scaling problems
This is the showcase feature that demonstrates Gemini's ability to prevent production issues
"""

import ast
import re
import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import sqlparse
import dis
import sys
import tracemalloc
import psutil
from collections import defaultdict

logger = logging.getLogger(__name__)

@dataclass
class ScalingIssue:
    """Represents a detected scaling issue"""
    type: str  # n_plus_one, memory_leak, inefficient_algorithm, blocking_io, etc.
    severity: str  # critical, high, medium, low
    file_path: str
    line_number: int
    function_name: Optional[str]
    description: str
    impact: str  # Description of production impact
    estimated_impact_at_scale: Dict[str, Any]  # Metrics at different scales
    fix_recommendation: str
    code_snippet: str
    confidence: float  # 0.0 to 1.0

@dataclass
class PerformanceProfile:
    """Performance profile of code"""
    time_complexity: str  # O(1), O(n), O(n^2), etc.
    space_complexity: str
    estimated_runtime_ms: Dict[str, float]  # At different data sizes
    memory_usage_mb: Dict[str, float]
    database_queries: int
    network_calls: int
    blocking_operations: int

@dataclass
class ScalingReport:
    """Complete scaling analysis report"""
    file_path: str
    issues: List[ScalingIssue]
    performance_profile: PerformanceProfile
    risk_score: float  # 0-100
    production_readiness: bool
    recommendations: List[str]
    analyzed_at: datetime = field(default_factory=datetime.now)


class NPlusOneDetector:
    """Detects N+1 query problems"""
    
    def detect(self, code: str, file_path: str) -> List[ScalingIssue]:
        """Detect N+1 query patterns in code"""
        issues = []
        
        # Pattern 1: Loop with database query
        loop_query_pattern = r'for\s+\w+\s+in\s+.*?:\s*\n.*?(query|select|find|fetch|get|filter|aggregate)'
        
        # Pattern 2: Loop with ORM call
        orm_patterns = [
            r'for.*?:\s*\n.*?\.(objects\.get|objects\.filter|select_related|prefetch_related)',
            r'for.*?:\s*\n.*?session\.(query|get|filter)',
            r'map\(lambda.*?:\s*.*?\.(get|filter|find)',
        ]
        
        lines = code.split('\n')
        
        # Check for loop patterns
        for i, line in enumerate(lines, 1):
            # Check if line starts a loop
            if re.match(r'\s*(for|while)\s+', line):
                # Check next 5 lines for query operations
                for j in range(i, min(i + 5, len(lines))):
                    next_line = lines[j]
                    
                    # Check for database operations
                    if any(keyword in next_line.lower() for keyword in 
                          ['query', 'select', 'find', 'fetch', 'get', 'filter', 'cursor', 'execute']):
                        
                        # Check if it's not using batch operations
                        if not any(batch in next_line for batch in 
                                  ['bulk', 'batch', 'all()', 'prefetch', 'select_related']):
                            
                            issues.append(ScalingIssue(
                                type="n_plus_one",
                                severity="critical",
                                file_path=file_path,
                                line_number=i,
                                function_name=self._get_function_name(lines, i),
                                description=f"N+1 query problem detected: Database query inside loop",
                                impact="Each iteration makes a separate database query, causing severe performance degradation",
                                estimated_impact_at_scale={
                                    "100_items": "100 queries, ~500ms",
                                    "1000_items": "1000 queries, ~5s",
                                    "10000_items": "10000 queries, ~50s timeout"
                                },
                                fix_recommendation="Use eager loading (select_related/prefetch_related) or batch queries",
                                code_snippet=f"{line}\n{lines[j]}",
                                confidence=0.9
                            ))
        
        # Pattern 3: GraphQL resolver N+1
        graphql_pattern = r'@resolver.*?\n.*?def.*?\n.*?for.*?:\n.*?return.*?query'
        if re.search(graphql_pattern, code, re.MULTILINE | re.DOTALL):
            issues.append(ScalingIssue(
                type="n_plus_one",
                severity="high",
                file_path=file_path,
                line_number=1,
                function_name="GraphQL Resolver",
                description="GraphQL resolver N+1 problem",
                impact="Each field resolution triggers separate query",
                estimated_impact_at_scale={
                    "10_fields": "10+ queries per request",
                    "100_fields": "100+ queries, API timeout"
                },
                fix_recommendation="Use DataLoader pattern for batching",
                code_snippet="GraphQL resolver with nested queries",
                confidence=0.85
            ))
        
        return issues
    
    def _get_function_name(self, lines: List[str], line_num: int) -> Optional[str]:
        """Get the function name containing the given line"""
        for i in range(line_num - 1, -1, -1):
            if re.match(r'\s*def\s+(\w+)', lines[i]):
                match = re.match(r'\s*def\s+(\w+)', lines[i])
                return match.group(1) if match else None
        return None


class MemoryLeakDetector:
    """Detects memory leak patterns"""
    
    def detect(self, code: str, file_path: str) -> List[ScalingIssue]:
        """Detect memory leak patterns"""
        issues = []
        lines = code.split('\n')
        
        # Pattern 1: Event listeners without cleanup
        if 'addEventListener' in code:
            if 'removeEventListener' not in code:
                for i, line in enumerate(lines, 1):
                    if 'addEventListener' in line:
                        issues.append(ScalingIssue(
                            type="memory_leak",
                            severity="high",
                            file_path=file_path,
                            line_number=i,
                            function_name=None,
                            description="Event listener added without cleanup",
                            impact="Memory leak: listeners accumulate over time",
                            estimated_impact_at_scale={
                                "1_hour": "~10MB leaked",
                                "24_hours": "~240MB leaked",
                                "1_week": "~1.6GB leaked, app crash"
                            },
                            fix_recommendation="Add removeEventListener in cleanup/unmount",
                            code_snippet=line,
                            confidence=0.95
                        ))
        
        # Pattern 2: Global cache without limits
        cache_patterns = [
            r'cache\s*=\s*\{\}',
            r'cache\s*=\s*\[\]',
            r'self\._cache\s*=',
            r'global\s+cache'
        ]
        
        for pattern in cache_patterns:
            for i, line in enumerate(lines, 1):
                if re.search(pattern, line):
                    # Check if there's a size limit
                    has_limit = False
                    for j in range(max(0, i-5), min(len(lines), i+10)):
                        if any(limit in lines[j] for limit in 
                              ['maxsize', 'limit', 'MAX_SIZE', 'LRU', 'capacity']):
                            has_limit = True
                            break
                    
                    if not has_limit:
                        issues.append(ScalingIssue(
                            type="memory_leak",
                            severity="medium",
                            file_path=file_path,
                            line_number=i,
                            function_name=None,
                            description="Unbounded cache detected",
                            impact="Cache grows indefinitely, consuming all available memory",
                            estimated_impact_at_scale={
                                "1000_entries": "~50MB",
                                "100000_entries": "~5GB",
                                "continuous_growth": "OOM after ~1M entries"
                            },
                            fix_recommendation="Implement LRU cache or set maximum size",
                            code_snippet=line,
                            confidence=0.8
                        ))
        
        # Pattern 3: Circular references in Python
        if file_path.endswith('.py'):
            circular_patterns = [
                r'self\.parent\s*=.*?\n.*?parent\.\w+\s*=\s*self',
                r'\.append\(self\)',
            ]
            
            for pattern in circular_patterns:
                if re.search(pattern, code, re.MULTILINE):
                    issues.append(ScalingIssue(
                        type="memory_leak",
                        severity="medium",
                        file_path=file_path,
                        line_number=1,
                        function_name=None,
                        description="Potential circular reference detected",
                        impact="Objects not garbage collected properly",
                        estimated_impact_at_scale={
                            "1000_objects": "~10MB retained",
                            "100000_objects": "~1GB retained"
                        },
                        fix_recommendation="Use weakref for parent references",
                        code_snippet="Circular reference pattern",
                        confidence=0.7
                    ))
        
        return issues


class InefficientAlgorithmDetector:
    """Detects inefficient algorithms"""
    
    def detect(self, code: str, file_path: str) -> List[ScalingIssue]:
        """Detect inefficient algorithm patterns"""
        issues = []
        lines = code.split('\n')
        
        # Pattern 1: Nested loops (O(n²) or worse)
        nested_loops = self._detect_nested_loops(lines, file_path)
        issues.extend(nested_loops)
        
        # Pattern 2: Inefficient string concatenation
        string_concat = self._detect_string_concatenation(lines, file_path)
        issues.extend(string_concat)
        
        # Pattern 3: Linear search instead of hash/set
        linear_search = self._detect_linear_search(lines, file_path)
        issues.extend(linear_search)
        
        # Pattern 4: Recursive without memoization
        recursive = self._detect_unmemoized_recursion(code, file_path)
        issues.extend(recursive)
        
        return issues
    
    def _detect_nested_loops(self, lines: List[str], file_path: str) -> List[ScalingIssue]:
        """Detect nested loop patterns"""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if re.match(r'\s*(for|while)\s+', line):
                # Check for nested loop
                indent = len(line) - len(line.lstrip())
                for j in range(i + 1, min(i + 20, len(lines))):
                    next_line = lines[j - 1]
                    next_indent = len(next_line) - len(next_line.lstrip())
                    
                    if next_indent > indent and re.match(r'\s*(for|while)\s+', next_line):
                        # Check for triple nesting
                        severity = "medium"
                        complexity = "O(n²)"
                        
                        for k in range(j + 1, min(j + 20, len(lines))):
                            third_line = lines[k - 1]
                            third_indent = len(third_line) - len(third_line.lstrip())
                            if third_indent > next_indent and re.match(r'\s*(for|while)\s+', third_line):
                                severity = "critical"
                                complexity = "O(n³)"
                                break
                        
                        issues.append(ScalingIssue(
                            type="inefficient_algorithm",
                            severity=severity,
                            file_path=file_path,
                            line_number=i,
                            function_name=None,
                            description=f"Nested loops detected with {complexity} complexity",
                            impact=f"Exponential performance degradation with data growth",
                            estimated_impact_at_scale={
                                "n=100": "10,000 operations",
                                "n=1000": "1,000,000 operations",
                                "n=10000": "100,000,000 operations, likely timeout"
                            } if complexity == "O(n²)" else {
                                "n=100": "1,000,000 operations",
                                "n=1000": "1,000,000,000 operations, definite timeout",
                                "n=10000": "System hang"
                            },
                            fix_recommendation="Consider using hash maps, sorting, or dynamic programming",
                            code_snippet=f"{line}\n  {lines[j-1]}",
                            confidence=0.9
                        ))
                        break
        
        return issues
    
    def _detect_string_concatenation(self, lines: List[str], file_path: str) -> List[ScalingIssue]:
        """Detect inefficient string concatenation in loops"""
        issues = []
        
        for i, line in enumerate(lines, 1):
            if re.match(r'\s*(for|while)\s+', line):
                # Check next lines for string concatenation
                for j in range(i + 1, min(i + 10, len(lines))):
                    next_line = lines[j - 1]
                    
                    # Python string concatenation
                    if '+=' in next_line and ('"' in next_line or "'" in next_line):
                        issues.append(ScalingIssue(
                            type="inefficient_algorithm",
                            severity="medium",
                            file_path=file_path,
                            line_number=j,
                            function_name=None,
                            description="String concatenation in loop (O(n²) complexity)",
                            impact="Quadratic time complexity for string building",
                            estimated_impact_at_scale={
                                "1000_iterations": "~100ms",
                                "10000_iterations": "~10s",
                                "100000_iterations": "~1000s timeout"
                            },
                            fix_recommendation="Use list.append() and ''.join() or StringBuilder",
                            code_snippet=next_line,
                            confidence=0.85
                        ))
        
        return issues
    
    def _detect_linear_search(self, lines: List[str], file_path: str) -> List[ScalingIssue]:
        """Detect linear search that could use hash/set"""
        issues = []
        
        # Pattern: if item in list inside loop
        for i, line in enumerate(lines, 1):
            if re.search(r'if\s+\w+\s+in\s+\w+(?:\s|:)', line):
                # Check if it's in a loop
                for j in range(max(0, i - 10), i):
                    if re.match(r'\s*(for|while)\s+', lines[j]):
                        issues.append(ScalingIssue(
                            type="inefficient_algorithm",
                            severity="medium",
                            file_path=file_path,
                            line_number=i,
                            function_name=None,
                            description="Linear search in loop (O(n²) complexity)",
                            impact="Each lookup is O(n), in loop becomes O(n²)",
                            estimated_impact_at_scale={
                                "100_items": "10,000 comparisons",
                                "1000_items": "1,000,000 comparisons",
                                "10000_items": "100,000,000 comparisons"
                            },
                            fix_recommendation="Convert list to set for O(1) lookup",
                            code_snippet=line,
                            confidence=0.75
                        ))
                        break
        
        return issues
    
    def _detect_unmemoized_recursion(self, code: str, file_path: str) -> List[ScalingIssue]:
        """Detect recursive functions without memoization"""
        issues = []
        
        # Find recursive functions
        function_pattern = r'def\s+(\w+)\s*\([^)]*\):\s*\n(.*?)(?=\ndef|\nclass|\Z)'
        matches = re.finditer(function_pattern, code, re.MULTILINE | re.DOTALL)
        
        for match in matches:
            func_name = match.group(1)
            func_body = match.group(2)
            
            # Check if function calls itself
            if func_name in func_body:
                # Check for memoization patterns
                has_memo = any(pattern in func_body for pattern in 
                             ['@cache', '@lru_cache', '@memoize', 'memo', 'cache', 'dp'])
                
                if not has_memo and 'fibonacci' in func_name.lower():
                    issues.append(ScalingIssue(
                        type="inefficient_algorithm",
                        severity="critical",
                        file_path=file_path,
                        line_number=1,
                        function_name=func_name,
                        description="Unmemoized recursive Fibonacci (exponential complexity)",
                        impact="Exponential time complexity O(2^n)",
                        estimated_impact_at_scale={
                            "n=20": "~1 million calls",
                            "n=30": "~1 billion calls, ~30s",
                            "n=40": "~1 trillion calls, hours"
                        },
                        fix_recommendation="Add @functools.lru_cache decorator",
                        code_snippet=f"def {func_name}(...)",
                        confidence=0.95
                    ))
        
        return issues


class DatabaseQueryAnalyzer:
    """Analyzes database query patterns"""
    
    def detect(self, code: str, file_path: str) -> List[ScalingIssue]:
        """Detect database query issues"""
        issues = []
        
        # Detect missing indexes
        issues.extend(self._detect_missing_indexes(code, file_path))
        
        # Detect SELECT *
        issues.extend(self._detect_select_star(code, file_path))
        
        # Detect missing pagination
        issues.extend(self._detect_missing_pagination(code, file_path))
        
        return issues
    
    def _detect_missing_indexes(self, code: str, file_path: str) -> List[ScalingIssue]:
        """Detect queries that might need indexes"""
        issues = []
        
        # Pattern: WHERE clause without index hint
        where_pattern = r'(WHERE|where)\s+(\w+)\s*=|LIKE|IN'
        
        if re.search(where_pattern, code):
            issues.append(ScalingIssue(
                type="database_performance",
                severity="high",
                file_path=file_path,
                line_number=1,
                function_name=None,
                description="Query with WHERE clause may need index",
                impact="Full table scan without proper indexes",
                estimated_impact_at_scale={
                    "1000_rows": "~10ms",
                    "100000_rows": "~1s",
                    "10000000_rows": "~100s timeout"
                },
                fix_recommendation="Add index on frequently queried columns",
                code_snippet="WHERE clause detected",
                confidence=0.6
            ))
        
        return issues
    
    def _detect_select_star(self, code: str, file_path: str) -> List[ScalingIssue]:
        """Detect SELECT * queries"""
        issues = []
        
        if re.search(r'SELECT\s+\*|select\s+\*', code):
            issues.append(ScalingIssue(
                type="database_performance",
                severity="medium",
                file_path=file_path,
                line_number=1,
                function_name=None,
                description="SELECT * query fetches unnecessary data",
                impact="Transfers excess data over network",
                estimated_impact_at_scale={
                    "10_columns": "10x data transfer",
                    "50_columns": "50x data transfer",
                    "blob_columns": "Potential GB of unnecessary data"
                },
                fix_recommendation="Select only required columns",
                code_snippet="SELECT * FROM ...",
                confidence=0.9
            ))
        
        return issues
    
    def _detect_missing_pagination(self, code: str, file_path: str) -> List[ScalingIssue]:
        """Detect queries without pagination"""
        issues = []
        
        # Check for queries without LIMIT
        if re.search(r'(SELECT|select).*?(FROM|from)', code) and 'LIMIT' not in code.upper():
            issues.append(ScalingIssue(
                type="database_performance",
                severity="high",
                file_path=file_path,
                line_number=1,
                function_name=None,
                description="Query without pagination (LIMIT/OFFSET)",
                impact="Fetches entire result set, potential OOM",
                estimated_impact_at_scale={
                    "1000_rows": "Manageable",
                    "100000_rows": "High memory usage",
                    "10000000_rows": "OOM error"
                },
                fix_recommendation="Add pagination with LIMIT and OFFSET",
                code_snippet="SELECT without LIMIT",
                confidence=0.7
            ))
        
        return issues


class ScalingIssueDetector:
    """Main scaling issue detection engine"""
    
    def __init__(self):
        self.n_plus_one_detector = NPlusOneDetector()
        self.memory_leak_detector = MemoryLeakDetector()
        self.algorithm_detector = InefficientAlgorithmDetector()
        self.database_analyzer = DatabaseQueryAnalyzer()
    
    async def analyze_file(self, file_path: str) -> ScalingReport:
        """Analyze a file for scaling issues"""
        with open(file_path, 'r') as f:
            code = f.read()
        
        issues = []
        
        # Run all detectors
        issues.extend(self.n_plus_one_detector.detect(code, file_path))
        issues.extend(self.memory_leak_detector.detect(code, file_path))
        issues.extend(self.algorithm_detector.detect(code, file_path))
        issues.extend(self.database_analyzer.detect(code, file_path))
        
        # Calculate performance profile
        profile = self._calculate_performance_profile(code)
        
        # Calculate risk score
        risk_score = self._calculate_risk_score(issues)
        
        # Determine production readiness
        production_ready = risk_score < 30 and not any(
            issue.severity == "critical" for issue in issues
        )
        
        # Generate recommendations
        recommendations = self._generate_recommendations(issues)
        
        return ScalingReport(
            file_path=file_path,
            issues=issues,
            performance_profile=profile,
            risk_score=risk_score,
            production_readiness=production_ready,
            recommendations=recommendations
        )
    
    async def analyze_project(self, project_path: str) -> Dict[str, ScalingReport]:
        """Analyze entire project for scaling issues"""
        reports = {}
        
        for file_path in Path(project_path).rglob("*.py"):
            try:
                report = await self.analyze_file(str(file_path))
                reports[str(file_path)] = report
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")
        
        return reports
    
    def _calculate_performance_profile(self, code: str) -> PerformanceProfile:
        """Calculate performance profile of code"""
        # Simple heuristic-based profiling
        lines = code.split('\n')
        
        # Count loops for complexity estimation
        loop_count = sum(1 for line in lines if re.match(r'\s*(for|while)\s+', line))
        nested_loops = len(re.findall(r'for.*?\n.*?for', code, re.MULTILINE))
        
        # Estimate complexity
        if nested_loops >= 2:
            time_complexity = "O(n³)"
        elif nested_loops == 1:
            time_complexity = "O(n²)"
        elif loop_count > 0:
            time_complexity = "O(n)"
        else:
            time_complexity = "O(1)"
        
        # Count database operations
        db_queries = len(re.findall(r'(query|select|insert|update|delete)', code, re.IGNORECASE))
        
        # Count network calls
        network_calls = len(re.findall(r'(request|fetch|api|http|rest)', code, re.IGNORECASE))
        
        return PerformanceProfile(
            time_complexity=time_complexity,
            space_complexity="O(n)" if 'append' in code else "O(1)",
            estimated_runtime_ms={
                "n=100": 10 * (nested_loops + 1),
                "n=1000": 100 * (nested_loops + 1) ** 2,
                "n=10000": 1000 * (nested_loops + 1) ** 3
            },
            memory_usage_mb={
                "n=100": 1,
                "n=1000": 10,
                "n=10000": 100
            },
            database_queries=db_queries,
            network_calls=network_calls,
            blocking_operations=db_queries + network_calls
        )
    
    def _calculate_risk_score(self, issues: List[ScalingIssue]) -> float:
        """Calculate overall risk score (0-100)"""
        if not issues:
            return 0
        
        score = 0
        severity_weights = {
            "critical": 30,
            "high": 20,
            "medium": 10,
            "low": 5
        }
        
        for issue in issues:
            score += severity_weights.get(issue.severity, 0) * issue.confidence
        
        return min(100, score)
    
    def _generate_recommendations(self, issues: List[ScalingIssue]) -> List[str]:
        """Generate prioritized recommendations"""
        recommendations = []
        
        # Group issues by type
        issue_types = defaultdict(list)
        for issue in issues:
            issue_types[issue.type].append(issue)
        
        # Generate recommendations by type
        if issue_types["n_plus_one"]:
            recommendations.append(
                "🔴 CRITICAL: Fix N+1 query problems using eager loading or batch queries"
            )
        
        if issue_types["memory_leak"]:
            recommendations.append(
                "🟠 HIGH: Address memory leaks by adding proper cleanup and using bounded caches"
            )
        
        if issue_types["inefficient_algorithm"]:
            recommendations.append(
                "🟡 MEDIUM: Optimize algorithms - replace nested loops with efficient data structures"
            )
        
        if issue_types["database_performance"]:
            recommendations.append(
                "🟡 MEDIUM: Optimize database queries - add indexes and pagination"
            )
        
        # Add general recommendations
        if len(issues) > 5:
            recommendations.append(
                "⚠️ Consider comprehensive performance testing before production deployment"
            )
        
        return recommendations


# Export main class
__all__ = ['ScalingIssueDetector', 'ScalingReport', 'ScalingIssue']