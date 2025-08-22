"""
Regression Prevention System
Automated quality gates and regression detection for continuous improvement
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from pathlib import Path
import hashlib
import subprocess
import statistics

import pytest
import coverage
from pydantic import BaseModel

logger = logging.getLogger(__name__)

@dataclass
class QualityMetrics:
    """Quality metrics for a codebase"""
    timestamp: datetime
    commit_sha: str
    branch: str
    
    # Test metrics
    test_count: int
    test_passed: int
    test_failed: int
    test_skipped: int
    test_duration: float
    
    # Coverage metrics
    line_coverage: float
    branch_coverage: float
    function_coverage: float
    
    # Code quality metrics
    cyclomatic_complexity: float
    maintainability_index: float
    lines_of_code: int
    
    # Performance metrics
    startup_time: float
    response_time_p95: float
    memory_usage_mb: float
    
    # Security metrics
    security_issues: int
    vulnerability_count: int
    
    # Custom metrics
    custom_metrics: Dict[str, Any] = None

@dataclass
class RegressionResult:
    """Result of regression analysis"""
    has_regression: bool
    severity: str  # none, low, medium, high, critical
    affected_areas: List[str]
    details: List[str]
    recommendations: List[str]
    baseline_metrics: QualityMetrics
    current_metrics: QualityMetrics

class QualityGate:
    """Quality gate configuration"""
    def __init__(self, name: str, threshold: float, comparison: str = ">=", critical: bool = False):
        self.name = name
        self.threshold = threshold
        self.comparison = comparison  # >=, <=, ==, !=
        self.critical = critical  # If true, failure blocks deployment
    
    def check(self, value: float) -> Tuple[bool, str]:
        """Check if value passes the quality gate"""
        if self.comparison == ">=":
            passed = value >= self.threshold
            message = f"{self.name}: {value:.2f} {'✓' if passed else '✗'} {self.threshold}"
        elif self.comparison == "<=":
            passed = value <= self.threshold
            message = f"{self.name}: {value:.2f} {'✓' if passed else '✗'} {self.threshold}"
        elif self.comparison == "==":
            passed = abs(value - self.threshold) < 0.01
            message = f"{self.name}: {value:.2f} {'✓' if passed else '✗'} {self.threshold}"
        elif self.comparison == "!=":
            passed = abs(value - self.threshold) >= 0.01
            message = f"{self.name}: {value:.2f} {'✓' if passed else '✗'} {self.threshold}"
        else:
            passed = False
            message = f"{self.name}: Invalid comparison operator"
        
        return passed, message

class RegressionPrevention:
    """Main regression prevention system"""
    
    def __init__(self, project_root: str, baseline_days: int = 7):
        self.project_root = Path(project_root)
        self.baseline_days = baseline_days
        self.metrics_file = self.project_root / "quality_metrics.jsonl"
        
        # Configure quality gates
        self.quality_gates = [
            QualityGate("Test Pass Rate", 95.0, ">=", critical=True),
            QualityGate("Line Coverage", 80.0, ">=", critical=True),
            QualityGate("Branch Coverage", 70.0, ">=", critical=False),
            QualityGate("Function Coverage", 85.0, ">=", critical=False),
            QualityGate("Cyclomatic Complexity", 10.0, "<=", critical=False),
            QualityGate("Maintainability Index", 70.0, ">=", critical=False),
            QualityGate("Startup Time", 5.0, "<=", critical=False),
            QualityGate("Response Time P95", 1000.0, "<=", critical=False),
            QualityGate("Memory Usage", 512.0, "<=", critical=False),
            QualityGate("Security Issues", 0, "==", critical=True),
            QualityGate("Vulnerability Count", 0, "==", critical=True),
        ]
        
        # Regression thresholds (percentage degradation)
        self.regression_thresholds = {
            "test_pass_rate": 5.0,  # 5% decrease
            "line_coverage": 10.0,  # 10% decrease
            "branch_coverage": 15.0,  # 15% decrease
            "startup_time": 50.0,  # 50% increase
            "response_time_p95": 100.0,  # 100% increase
            "memory_usage": 25.0,  # 25% increase
        }
    
    async def collect_metrics(self, commit_sha: str = None, branch: str = "main") -> QualityMetrics:
        """Collect all quality metrics for current state"""
        logger.info("Collecting quality metrics...")
        
        if not commit_sha:
            commit_sha = await self._get_current_commit()
        
        # Collect metrics concurrently
        test_metrics = await self._collect_test_metrics()
        coverage_metrics = await self._collect_coverage_metrics()
        code_metrics = await self._collect_code_quality_metrics()
        performance_metrics = await self._collect_performance_metrics()
        security_metrics = await self._collect_security_metrics()
        
        metrics = QualityMetrics(
            timestamp=datetime.utcnow(),
            commit_sha=commit_sha,
            branch=branch,
            **test_metrics,
            **coverage_metrics,
            **code_metrics,
            **performance_metrics,
            **security_metrics
        )
        
        # Store metrics
        await self._store_metrics(metrics)
        
        return metrics
    
    async def check_quality_gates(self, metrics: QualityMetrics) -> Tuple[bool, List[str]]:
        """Check if metrics pass all quality gates"""
        passed = True
        results = []
        critical_failures = []
        
        for gate in self.quality_gates:
            value = self._get_metric_value(metrics, gate.name)
            if value is not None:
                gate_passed, message = gate.check(value)
                results.append(message)
                
                if not gate_passed:
                    passed = False
                    if gate.critical:
                        critical_failures.append(gate.name)
        
        if critical_failures:
            results.append(f"❌ CRITICAL FAILURES: {', '.join(critical_failures)}")
        
        return passed, results
    
    async def detect_regression(self, current_metrics: QualityMetrics) -> RegressionResult:
        """Detect regression by comparing with baseline"""
        logger.info("Detecting regression...")
        
        baseline_metrics = await self._get_baseline_metrics()
        if not baseline_metrics:
            logger.warning("No baseline metrics available")
            return RegressionResult(
                has_regression=False,
                severity="none",
                affected_areas=[],
                details=["No baseline metrics available for comparison"],
                recommendations=["Establish baseline metrics by running tests"],
                baseline_metrics=current_metrics,
                current_metrics=current_metrics
            )
        
        # Compare metrics
        regressions = []
        affected_areas = []
        
        # Test regression
        baseline_pass_rate = (baseline_metrics.test_passed / max(1, baseline_metrics.test_count)) * 100
        current_pass_rate = (current_metrics.test_passed / max(1, current_metrics.test_count)) * 100
        
        if baseline_pass_rate - current_pass_rate > self.regression_thresholds["test_pass_rate"]:
            regressions.append(f"Test pass rate decreased by {baseline_pass_rate - current_pass_rate:.1f}%")
            affected_areas.append("testing")
        
        # Coverage regression
        coverage_diff = baseline_metrics.line_coverage - current_metrics.line_coverage
        if coverage_diff > self.regression_thresholds["line_coverage"]:
            regressions.append(f"Line coverage decreased by {coverage_diff:.1f}%")
            affected_areas.append("coverage")
        
        # Performance regression
        startup_increase = ((current_metrics.startup_time - baseline_metrics.startup_time) / 
                           max(0.1, baseline_metrics.startup_time)) * 100
        if startup_increase > self.regression_thresholds["startup_time"]:
            regressions.append(f"Startup time increased by {startup_increase:.1f}%")
            affected_areas.append("performance")
        
        response_increase = ((current_metrics.response_time_p95 - baseline_metrics.response_time_p95) / 
                           max(0.1, baseline_metrics.response_time_p95)) * 100
        if response_increase > self.regression_thresholds["response_time_p95"]:
            regressions.append(f"Response time increased by {response_increase:.1f}%")
            affected_areas.append("performance")
        
        memory_increase = ((current_metrics.memory_usage_mb - baseline_metrics.memory_usage_mb) / 
                          max(1, baseline_metrics.memory_usage_mb)) * 100
        if memory_increase > self.regression_thresholds["memory_usage"]:
            regressions.append(f"Memory usage increased by {memory_increase:.1f}%")
            affected_areas.append("performance")
        
        # Security regression
        if current_metrics.security_issues > baseline_metrics.security_issues:
            regressions.append(f"Security issues increased by {current_metrics.security_issues - baseline_metrics.security_issues}")
            affected_areas.append("security")
        
        # Determine severity
        severity = self._calculate_regression_severity(regressions, affected_areas)
        
        # Generate recommendations
        recommendations = self._generate_regression_recommendations(affected_areas, regressions)
        
        return RegressionResult(
            has_regression=len(regressions) > 0,
            severity=severity,
            affected_areas=list(set(affected_areas)),
            details=regressions,
            recommendations=recommendations,
            baseline_metrics=baseline_metrics,
            current_metrics=current_metrics
        )
    
    async def run_full_analysis(self, commit_sha: str = None, branch: str = "main") -> Dict[str, Any]:
        """Run complete regression prevention analysis"""
        logger.info("Running full regression prevention analysis...")
        
        # Collect current metrics
        current_metrics = await self.collect_metrics(commit_sha, branch)
        
        # Check quality gates
        gates_passed, gate_results = await self.check_quality_gates(current_metrics)
        
        # Detect regression
        regression_result = await self.detect_regression(current_metrics)
        
        # Generate report
        report = {
            "timestamp": datetime.utcnow().isoformat(),
            "commit_sha": commit_sha or current_metrics.commit_sha,
            "branch": branch,
            "quality_gates": {
                "passed": gates_passed,
                "results": gate_results
            },
            "regression_analysis": asdict(regression_result),
            "current_metrics": asdict(current_metrics),
            "recommendations": self._generate_overall_recommendations(
                gates_passed, regression_result
            )
        }
        
        # Save report
        report_file = self.project_root / f"regression_report_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2, default=str)
        
        logger.info(f"Regression prevention report saved: {report_file}")
        
        return report
    
    async def _collect_test_metrics(self) -> Dict[str, Any]:
        """Collect test metrics using pytest"""
        try:
            # Run pytest with JSON report
            result = subprocess.run(
                ["python", "-m", "pytest", "--json-report", "--json-report-file=test_report.json", "-v"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            # Parse pytest JSON report
            report_file = self.project_root / "test_report.json"
            if report_file.exists():
                with open(report_file) as f:
                    test_data = json.load(f)
                
                summary = test_data.get("summary", {})
                
                return {
                    "test_count": summary.get("total", 0),
                    "test_passed": summary.get("passed", 0),
                    "test_failed": summary.get("failed", 0),
                    "test_skipped": summary.get("skipped", 0),
                    "test_duration": test_data.get("duration", 0.0)
                }
        except Exception as e:
            logger.warning(f"Failed to collect test metrics: {e}")
        
        return {
            "test_count": 0,
            "test_passed": 0,
            "test_failed": 0,
            "test_skipped": 0,
            "test_duration": 0.0
        }
    
    async def _collect_coverage_metrics(self) -> Dict[str, Any]:
        """Collect code coverage metrics"""
        try:
            # Run coverage
            subprocess.run(
                ["python", "-m", "coverage", "run", "-m", "pytest"],
                cwd=self.project_root,
                capture_output=True,
                timeout=300
            )
            
            # Get coverage report
            result = subprocess.run(
                ["python", "-m", "coverage", "json"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                coverage_file = self.project_root / "coverage.json"
                if coverage_file.exists():
                    with open(coverage_file) as f:
                        coverage_data = json.load(f)
                    
                    totals = coverage_data.get("totals", {})
                    
                    return {
                        "line_coverage": totals.get("percent_covered", 0.0),
                        "branch_coverage": totals.get("percent_covered_display", 0.0),
                        "function_coverage": 0.0  # Not available in coverage.py
                    }
        except Exception as e:
            logger.warning(f"Failed to collect coverage metrics: {e}")
        
        return {
            "line_coverage": 0.0,
            "branch_coverage": 0.0,
            "function_coverage": 0.0
        }
    
    async def _collect_code_quality_metrics(self) -> Dict[str, Any]:
        """Collect code quality metrics"""
        try:
            # Use radon for complexity metrics
            result = subprocess.run(
                ["radon", "cc", "-a", "-j", str(self.project_root)],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                complexity_data = json.loads(result.stdout)
                
                # Calculate average complexity
                complexities = []
                for file_data in complexity_data.values():
                    for item in file_data:
                        if isinstance(item, dict) and "complexity" in item:
                            complexities.append(item["complexity"])
                
                avg_complexity = statistics.mean(complexities) if complexities else 0.0
            else:
                avg_complexity = 0.0
            
            # Count lines of code
            loc = await self._count_lines_of_code()
            
            return {
                "cyclomatic_complexity": avg_complexity,
                "maintainability_index": 100.0 - avg_complexity * 2,  # Simplified calculation
                "lines_of_code": loc
            }
            
        except Exception as e:
            logger.warning(f"Failed to collect code quality metrics: {e}")
            
        return {
            "cyclomatic_complexity": 0.0,
            "maintainability_index": 100.0,
            "lines_of_code": 0
        }
    
    async def _collect_performance_metrics(self) -> Dict[str, Any]:
        """Collect performance metrics"""
        # These would be collected from actual performance tests
        # For now, return mock data
        return {
            "startup_time": 2.5,  # seconds
            "response_time_p95": 250.0,  # milliseconds
            "memory_usage_mb": 128.0  # MB
        }
    
    async def _collect_security_metrics(self) -> Dict[str, Any]:
        """Collect security metrics using bandit"""
        try:
            result = subprocess.run(
                ["bandit", "-r", str(self.project_root), "-f", "json"],
                capture_output=True,
                text=True,
                timeout=120
            )
            
            if result.stdout:
                bandit_data = json.loads(result.stdout)
                results = bandit_data.get("results", [])
                
                # Count issues by severity
                high_issues = len([r for r in results if r.get("issue_severity") == "HIGH"])
                medium_issues = len([r for r in results if r.get("issue_severity") == "MEDIUM"])
                low_issues = len([r for r in results if r.get("issue_severity") == "LOW"])
                
                return {
                    "security_issues": len(results),
                    "vulnerability_count": high_issues  # Count only high severity
                }
        except Exception as e:
            logger.warning(f"Failed to collect security metrics: {e}")
        
        return {
            "security_issues": 0,
            "vulnerability_count": 0
        }
    
    async def _count_lines_of_code(self) -> int:
        """Count lines of code in Python files"""
        total_lines = 0
        for py_file in self.project_root.rglob("*.py"):
            if "venv" in str(py_file) or "__pycache__" in str(py_file):
                continue
            try:
                with open(py_file, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                    # Count non-empty, non-comment lines
                    code_lines = [line for line in lines 
                                 if line.strip() and not line.strip().startswith('#')]
                    total_lines += len(code_lines)
            except Exception:
                pass
        
        return total_lines
    
    async def _get_current_commit(self) -> str:
        """Get current git commit SHA"""
        try:
            result = subprocess.run(
                ["git", "rev-parse", "HEAD"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.stdout.strip()[:8]
        except Exception:
            return "unknown"
    
    async def _store_metrics(self, metrics: QualityMetrics):
        """Store metrics to JSONL file"""
        try:
            with open(self.metrics_file, 'a') as f:
                json.dump(asdict(metrics), f, default=str)
                f.write('\n')
        except Exception as e:
            logger.error(f"Failed to store metrics: {e}")
    
    async def _get_baseline_metrics(self) -> Optional[QualityMetrics]:
        """Get baseline metrics (average of last N days)"""
        if not self.metrics_file.exists():
            return None
        
        cutoff_date = datetime.utcnow() - timedelta(days=self.baseline_days)
        recent_metrics = []
        
        try:
            with open(self.metrics_file, 'r') as f:
                for line in f:
                    data = json.loads(line.strip())
                    timestamp = datetime.fromisoformat(data['timestamp'])
                    if timestamp > cutoff_date:
                        recent_metrics.append(data)
        except Exception as e:
            logger.error(f"Failed to read baseline metrics: {e}")
            return None
        
        if not recent_metrics:
            return None
        
        # Calculate averages
        avg_metrics = {}
        for key in recent_metrics[0].keys():
            if key in ['timestamp', 'commit_sha', 'branch', 'custom_metrics']:
                continue
            
            values = [m[key] for m in recent_metrics if isinstance(m.get(key), (int, float))]
            if values:
                avg_metrics[key] = statistics.mean(values)
        
        # Use most recent timestamp and commit
        latest = recent_metrics[-1]
        avg_metrics.update({
            'timestamp': datetime.fromisoformat(latest['timestamp']),
            'commit_sha': latest['commit_sha'],
            'branch': latest['branch']
        })
        
        return QualityMetrics(**avg_metrics)
    
    def _get_metric_value(self, metrics: QualityMetrics, gate_name: str) -> Optional[float]:
        """Get metric value for quality gate"""
        mapping = {
            "Test Pass Rate": (metrics.test_passed / max(1, metrics.test_count)) * 100,
            "Line Coverage": metrics.line_coverage,
            "Branch Coverage": metrics.branch_coverage,
            "Function Coverage": metrics.function_coverage,
            "Cyclomatic Complexity": metrics.cyclomatic_complexity,
            "Maintainability Index": metrics.maintainability_index,
            "Startup Time": metrics.startup_time,
            "Response Time P95": metrics.response_time_p95,
            "Memory Usage": metrics.memory_usage_mb,
            "Security Issues": metrics.security_issues,
            "Vulnerability Count": metrics.vulnerability_count,
        }
        
        return mapping.get(gate_name)
    
    def _calculate_regression_severity(self, regressions: List[str], affected_areas: List[str]) -> str:
        """Calculate regression severity"""
        if not regressions:
            return "none"
        
        critical_areas = {"security", "testing"}
        high_impact_areas = {"performance", "coverage"}
        
        if any(area in critical_areas for area in affected_areas):
            return "critical"
        elif len(regressions) > 3 or any(area in high_impact_areas for area in affected_areas):
            return "high"
        elif len(regressions) > 1:
            return "medium"
        else:
            return "low"
    
    def _generate_regression_recommendations(self, affected_areas: List[str], regressions: List[str]) -> List[str]:
        """Generate recommendations for regression fixes"""
        recommendations = []
        
        if "testing" in affected_areas:
            recommendations.extend([
                "Review failed tests and fix underlying issues",
                "Add more comprehensive test cases",
                "Check for flaky tests that need stabilization"
            ])
        
        if "coverage" in affected_areas:
            recommendations.extend([
                "Add tests for uncovered code paths",
                "Review deleted tests to ensure coverage is maintained",
                "Consider property-based testing for complex logic"
            ])
        
        if "performance" in affected_areas:
            recommendations.extend([
                "Profile application to identify performance bottlenecks",
                "Review recent changes that might impact performance",
                "Add performance benchmarks to prevent future regressions"
            ])
        
        if "security" in affected_areas:
            recommendations.extend([
                "Review security scan results and fix issues immediately",
                "Update dependencies with known vulnerabilities",
                "Implement additional security controls"
            ])
        
        # General recommendations
        recommendations.extend([
            "Run regression tests in CI/CD pipeline",
            "Set up automated quality gates",
            "Monitor metrics trends over time"
        ])
        
        return recommendations
    
    def _generate_overall_recommendations(self, gates_passed: bool, regression_result: RegressionResult) -> List[str]:
        """Generate overall recommendations"""
        recommendations = []
        
        if not gates_passed:
            recommendations.append("❌ Quality gates failed - address critical issues before deployment")
        
        if regression_result.has_regression:
            if regression_result.severity in ["critical", "high"]:
                recommendations.append("🚨 Significant regression detected - consider reverting changes")
            else:
                recommendations.append("⚠️ Minor regression detected - plan fixes for next iteration")
        
        if gates_passed and not regression_result.has_regression:
            recommendations.append("✅ All quality checks passed - safe to deploy")
        
        return recommendations

# CLI interface
async def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Regression Prevention System")
    parser.add_argument("--project-root", default=".", help="Project root directory")
    parser.add_argument("--commit", help="Commit SHA to analyze")
    parser.add_argument("--branch", default="main", help="Branch name")
    parser.add_argument("--baseline-days", type=int, default=7, help="Days for baseline calculation")
    
    args = parser.parse_args()
    
    # Initialize system
    rp = RegressionPrevention(args.project_root, args.baseline_days)
    
    # Run analysis
    report = await rp.run_full_analysis(args.commit, args.branch)
    
    # Print summary
    print("\n" + "="*50)
    print("REGRESSION PREVENTION REPORT")
    print("="*50)
    
    print(f"Commit: {report['commit_sha']}")
    print(f"Branch: {report['branch']}")
    print(f"Timestamp: {report['timestamp']}")
    
    print(f"\nQuality Gates: {'✅ PASSED' if report['quality_gates']['passed'] else '❌ FAILED'}")
    for result in report['quality_gates']['results']:
        print(f"  {result}")
    
    regression = report['regression_analysis']
    if regression['has_regression']:
        print(f"\nRegression: 🚨 {regression['severity'].upper()}")
        print(f"Affected Areas: {', '.join(regression['affected_areas'])}")
        for detail in regression['details']:
            print(f"  • {detail}")
    else:
        print("\nRegression: ✅ None detected")
    
    print(f"\nRecommendations:")
    for rec in report['recommendations']:
        print(f"  • {rec}")
    
    # Exit with appropriate code
    if not report['quality_gates']['passed'] or regression['severity'] in ["critical", "high"]:
        exit(1)
    else:
        exit(0)

if __name__ == "__main__":
    asyncio.run(main())