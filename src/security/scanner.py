"""
Security Scanner for Gemini Enterprise Architect
Comprehensive security assessment and vulnerability detection
"""

import asyncio
import json
import logging
import os
import re
import subprocess
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

import aiohttp
import aiofiles
import bandit
from safety import check as safety_check

logger = logging.getLogger(__name__)

@dataclass
class SecurityFinding:
    """Security finding/vulnerability"""
    id: str
    severity: str  # critical, high, medium, low, info
    category: str
    title: str
    description: str
    file_path: Optional[str] = None
    line_number: Optional[int] = None
    code_snippet: Optional[str] = None
    recommendation: str = ""
    cve_id: Optional[str] = None
    reference_urls: List[str] = None

@dataclass
class SecurityReport:
    """Complete security assessment report"""
    scan_id: str
    timestamp: datetime
    target: str
    findings: List[SecurityFinding]
    summary: Dict[str, int]
    risk_score: int  # 0-100
    recommendations: List[str]
    scan_duration: float

class SecurityScanner:
    """Comprehensive security scanner"""
    
    def __init__(self, project_root: str):
        self.project_root = Path(project_root)
        self.findings = []
        self.scan_id = hashlib.md5(f"{datetime.utcnow().isoformat()}".encode()).hexdigest()[:8]
    
    async def run_full_scan(self) -> SecurityReport:
        """Run complete security scan"""
        start_time = datetime.utcnow()
        logger.info(f"Starting security scan {self.scan_id}")
        
        # Run all scan categories
        await asyncio.gather(
            self._scan_dependencies(),
            self._scan_code_security(),
            self._scan_configuration(),
            self._scan_secrets(),
            self._scan_docker_security(),
            self._scan_api_security(),
            return_exceptions=True
        )
        
        end_time = datetime.utcnow()
        duration = (end_time - start_time).total_seconds()
        
        # Generate report
        report = SecurityReport(
            scan_id=self.scan_id,
            timestamp=start_time,
            target=str(self.project_root),
            findings=self.findings,
            summary=self._calculate_summary(),
            risk_score=self._calculate_risk_score(),
            recommendations=self._generate_recommendations(),
            scan_duration=duration
        )
        
        logger.info(f"Security scan {self.scan_id} completed in {duration:.2f}s")
        return report
    
    async def _scan_dependencies(self):
        """Scan for vulnerable dependencies"""
        logger.info("Scanning dependencies for vulnerabilities...")
        
        # Python dependencies
        await self._scan_python_dependencies()
        
        # Node.js dependencies
        await self._scan_nodejs_dependencies()
        
        # Docker dependencies
        await self._scan_docker_dependencies()
    
    async def _scan_python_dependencies(self):
        """Scan Python dependencies with Safety"""
        requirements_files = [
            self.project_root / "requirements.txt",
            self.project_root / "requirements-test.txt"
        ]
        
        for req_file in requirements_files:
            if not req_file.exists():
                continue
            
            try:
                # Run safety check
                result = subprocess.run(
                    ["safety", "check", "-r", str(req_file), "--json"],
                    capture_output=True,
                    text=True,
                    timeout=60
                )
                
                if result.returncode == 0:
                    continue
                
                # Parse safety output
                try:
                    vulnerabilities = json.loads(result.stdout)
                    for vuln in vulnerabilities:
                        self.findings.append(SecurityFinding(
                            id=f"dep-{vuln.get('id', 'unknown')}",
                            severity=self._map_safety_severity(vuln.get('severity', 'medium')),
                            category="dependency",
                            title=f"Vulnerable dependency: {vuln.get('package_name')}",
                            description=vuln.get('advisory', ''),
                            file_path=str(req_file),
                            recommendation=f"Update {vuln.get('package_name')} to version {vuln.get('safe_versions', ['latest'])[0]}",
                            cve_id=vuln.get('cve'),
                            reference_urls=[vuln.get('more_info_url')] if vuln.get('more_info_url') else []
                        ))
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse safety output for {req_file}")
            
            except (subprocess.TimeoutExpired, FileNotFoundError):
                logger.warning(f"Safety check failed for {req_file}")
    
    async def _scan_nodejs_dependencies(self):
        """Scan Node.js dependencies with npm audit"""
        package_json = self.project_root / "package.json"
        if not package_json.exists():
            return
        
        try:
            result = subprocess.run(
                ["npm", "audit", "--json"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return
            
            # Parse npm audit output
            try:
                audit_data = json.loads(result.stdout)
                vulnerabilities = audit_data.get("vulnerabilities", {})
                
                for package, vuln_data in vulnerabilities.items():
                    severity = vuln_data.get("severity", "medium")
                    self.findings.append(SecurityFinding(
                        id=f"npm-{package}",
                        severity=severity,
                        category="dependency",
                        title=f"Vulnerable npm package: {package}",
                        description=vuln_data.get("title", ""),
                        file_path="package.json",
                        recommendation=f"Update {package} to fix vulnerability",
                        reference_urls=vuln_data.get("url", []) if isinstance(vuln_data.get("url"), list) else [vuln_data.get("url")] if vuln_data.get("url") else []
                    ))
            
            except json.JSONDecodeError:
                logger.warning("Could not parse npm audit output")
        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning("npm audit failed")
    
    async def _scan_docker_dependencies(self):
        """Scan Docker images for vulnerabilities"""
        dockerfiles = list(self.project_root.rglob("Dockerfile*"))
        
        for dockerfile in dockerfiles:
            await self._scan_dockerfile(dockerfile)
    
    async def _scan_dockerfile(self, dockerfile: Path):
        """Scan individual Dockerfile"""
        try:
            async with aiofiles.open(dockerfile, 'r') as f:
                content = await f.read()
            
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                line = line.strip()
                
                # Check for common security issues
                if line.startswith('FROM') and ':latest' in line:
                    self.findings.append(SecurityFinding(
                        id=f"docker-latest-{dockerfile.name}-{i}",
                        severity="medium",
                        category="docker",
                        title="Docker image uses 'latest' tag",
                        description="Using 'latest' tag can lead to unpredictable builds",
                        file_path=str(dockerfile),
                        line_number=i,
                        code_snippet=line,
                        recommendation="Pin to specific version tag"
                    ))
                
                if line.startswith('RUN') and 'curl' in line and 'bash' in line:
                    self.findings.append(SecurityFinding(
                        id=f"docker-curl-bash-{dockerfile.name}-{i}",
                        severity="high",
                        category="docker",
                        title="Potential remote code execution via curl | bash",
                        description="Downloading and executing scripts from the internet is dangerous",
                        file_path=str(dockerfile),
                        line_number=i,
                        code_snippet=line,
                        recommendation="Download files and verify integrity before execution"
                    ))
                
                if 'ADD' in line and ('http://' in line or 'https://' in line):
                    self.findings.append(SecurityFinding(
                        id=f"docker-add-url-{dockerfile.name}-{i}",
                        severity="medium",
                        category="docker",
                        title="ADD command with URL",
                        description="ADD with URLs can be security risk",
                        file_path=str(dockerfile),
                        line_number=i,
                        code_snippet=line,
                        recommendation="Use COPY for local files or RUN with wget/curl for verification"
                    ))
        
        except Exception as e:
            logger.warning(f"Could not scan Dockerfile {dockerfile}: {e}")
    
    async def _scan_code_security(self):
        """Scan code for security issues using Bandit"""
        logger.info("Scanning Python code for security issues...")
        
        python_files = list(self.project_root.rglob("*.py"))
        
        for py_file in python_files:
            if "venv" in str(py_file) or "node_modules" in str(py_file):
                continue
            
            await self._scan_python_file(py_file)
    
    async def _scan_python_file(self, py_file: Path):
        """Scan individual Python file with Bandit"""
        try:
            result = subprocess.run(
                ["bandit", "-f", "json", str(py_file)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.stdout:
                try:
                    bandit_data = json.loads(result.stdout)
                    results = bandit_data.get("results", [])
                    
                    for issue in results:
                        self.findings.append(SecurityFinding(
                            id=f"bandit-{issue.get('test_id', 'unknown')}",
                            severity=issue.get("issue_severity", "medium").lower(),
                            category="code",
                            title=issue.get("test_name", "Security issue"),
                            description=issue.get("issue_text", ""),
                            file_path=issue.get("filename"),
                            line_number=issue.get("line_number"),
                            code_snippet=issue.get("code", ""),
                            recommendation="Review and fix the security issue",
                            reference_urls=[issue.get("more_info")] if issue.get("more_info") else []
                        ))
                
                except json.JSONDecodeError:
                    logger.warning(f"Could not parse Bandit output for {py_file}")
        
        except (subprocess.TimeoutExpired, FileNotFoundError):
            logger.warning(f"Bandit scan failed for {py_file}")
    
    async def _scan_configuration(self):
        """Scan configuration files for security issues"""
        logger.info("Scanning configuration files...")
        
        # Scan YAML files
        yaml_files = list(self.project_root.rglob("*.yaml")) + list(self.project_root.rglob("*.yml"))
        for yaml_file in yaml_files:
            await self._scan_yaml_config(yaml_file)
        
        # Scan environment files
        env_files = list(self.project_root.rglob(".env*"))
        for env_file in env_files:
            await self._scan_env_file(env_file)
    
    async def _scan_yaml_config(self, yaml_file: Path):
        """Scan YAML configuration files"""
        try:
            async with aiofiles.open(yaml_file, 'r') as f:
                content = await f.read()
            
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                line_lower = line.lower().strip()
                
                # Check for weak configurations
                if 'password:' in line_lower and ('password123' in line_lower or 
                                                  'admin' in line_lower or 
                                                  'root' in line_lower):
                    self.findings.append(SecurityFinding(
                        id=f"config-weak-password-{yaml_file.name}-{i}",
                        severity="high",
                        category="configuration",
                        title="Weak password in configuration",
                        description="Default or weak password found in configuration",
                        file_path=str(yaml_file),
                        line_number=i,
                        code_snippet=line,
                        recommendation="Use strong passwords and store in secrets"
                    ))
                
                if 'debug:' in line_lower and 'true' in line_lower:
                    self.findings.append(SecurityFinding(
                        id=f"config-debug-enabled-{yaml_file.name}-{i}",
                        severity="medium",
                        category="configuration",
                        title="Debug mode enabled",
                        description="Debug mode should not be enabled in production",
                        file_path=str(yaml_file),
                        line_number=i,
                        code_snippet=line,
                        recommendation="Disable debug mode in production"
                    ))
        
        except Exception as e:
            logger.warning(f"Could not scan YAML file {yaml_file}: {e}")
    
    async def _scan_env_file(self, env_file: Path):
        """Scan environment files for secrets"""
        if env_file.name.endswith('.example'):
            return  # Skip example files
        
        try:
            async with aiofiles.open(env_file, 'r') as f:
                content = await f.read()
            
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                if '=' in line and not line.strip().startswith('#'):
                    key, value = line.split('=', 1)
                    
                    # Check for potential secrets
                    if self._is_potential_secret(key, value):
                        self.findings.append(SecurityFinding(
                            id=f"secret-in-env-{env_file.name}-{i}",
                            severity="high",
                            category="secrets",
                            title="Potential secret in environment file",
                            description=f"Environment variable {key} may contain sensitive data",
                            file_path=str(env_file),
                            line_number=i,
                            recommendation="Use secure secret management instead of plain text"
                        ))
        
        except Exception as e:
            logger.warning(f"Could not scan env file {env_file}: {e}")
    
    async def _scan_secrets(self):
        """Scan for hardcoded secrets and credentials"""
        logger.info("Scanning for hardcoded secrets...")
        
        # Patterns for common secrets
        secret_patterns = [
            (r'password\s*=\s*["\'][^"\']+["\']', "password"),
            (r'api_key\s*=\s*["\'][^"\']+["\']', "api_key"),
            (r'secret_key\s*=\s*["\'][^"\']+["\']', "secret_key"),
            (r'private_key\s*=\s*["\'][^"\']+["\']', "private_key"),
            (r'token\s*=\s*["\'][^"\']+["\']', "token"),
            (r'aws_access_key_id\s*=\s*["\'][^"\']+["\']', "aws_key"),
            (r'-----BEGIN\s+PRIVATE\s+KEY-----', "private_key"),
            (r'[a-f0-9]{32,}', "potential_hash"),
        ]
        
        # Scan source files
        source_files = (list(self.project_root.rglob("*.py")) + 
                       list(self.project_root.rglob("*.js")) + 
                       list(self.project_root.rglob("*.ts")) + 
                       list(self.project_root.rglob("*.jsx")) + 
                       list(self.project_root.rglob("*.tsx")))
        
        for source_file in source_files:
            if "venv" in str(source_file) or "node_modules" in str(source_file):
                continue
            
            await self._scan_file_for_secrets(source_file, secret_patterns)
    
    async def _scan_file_for_secrets(self, file_path: Path, patterns: List[tuple]):
        """Scan individual file for secret patterns"""
        try:
            async with aiofiles.open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = await f.read()
            
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                for pattern, secret_type in patterns:
                    if re.search(pattern, line, re.IGNORECASE):
                        # Skip comments and documentation
                        if line.strip().startswith('#') or line.strip().startswith('//'):
                            continue
                        
                        self.findings.append(SecurityFinding(
                            id=f"secret-{secret_type}-{file_path.name}-{i}",
                            severity="high",
                            category="secrets",
                            title=f"Potential {secret_type} in source code",
                            description=f"Found potential {secret_type} hardcoded in source",
                            file_path=str(file_path),
                            line_number=i,
                            code_snippet=line.strip(),
                            recommendation="Move secrets to environment variables or secret management"
                        ))
        
        except Exception as e:
            logger.warning(f"Could not scan file {file_path} for secrets: {e}")
    
    async def _scan_api_security(self):
        """Scan API endpoints for security issues"""
        logger.info("Scanning API security...")
        
        # Look for FastAPI/Flask apps
        api_files = []
        for pattern in ["**/api*.py", "**/app*.py", "**/main*.py", "**/server*.py"]:
            api_files.extend(self.project_root.rglob(pattern))
        
        for api_file in api_files:
            await self._scan_api_file(api_file)
    
    async def _scan_api_file(self, api_file: Path):
        """Scan API file for security issues"""
        try:
            async with aiofiles.open(api_file, 'r') as f:
                content = await f.read()
            
            lines = content.split('\n')
            
            for i, line in enumerate(lines, 1):
                line_lower = line.lower().strip()
                
                # Check for missing authentication
                if any(decorator in line_lower for decorator in ['@app.route', '@router.get', '@router.post']):
                    # Look ahead for authentication
                    next_lines = lines[i:i+5] if i < len(lines) - 5 else lines[i:]
                    has_auth = any('auth' in next_line.lower() or 'token' in next_line.lower() 
                                 for next_line in next_lines)
                    
                    if not has_auth and 'health' not in line_lower and 'docs' not in line_lower:
                        self.findings.append(SecurityFinding(
                            id=f"api-no-auth-{api_file.name}-{i}",
                            severity="medium",
                            category="api",
                            title="API endpoint without authentication",
                            description="API endpoint may be missing authentication",
                            file_path=str(api_file),
                            line_number=i,
                            code_snippet=line,
                            recommendation="Add authentication to sensitive endpoints"
                        ))
                
                # Check for SQL injection risks
                if 'execute(' in line_lower and any(param in line_lower for param in ['%s', 'format', '+']):
                    self.findings.append(SecurityFinding(
                        id=f"api-sql-injection-{api_file.name}-{i}",
                        severity="high",
                        category="api",
                        title="Potential SQL injection vulnerability",
                        description="SQL query construction may be vulnerable to injection",
                        file_path=str(api_file),
                        line_number=i,
                        code_snippet=line,
                        recommendation="Use parameterized queries"
                    ))
        
        except Exception as e:
            logger.warning(f"Could not scan API file {api_file}: {e}")
    
    def _is_potential_secret(self, key: str, value: str) -> bool:
        """Check if key-value pair is potential secret"""
        secret_keywords = ['password', 'key', 'secret', 'token', 'auth', 'credential']
        
        key_lower = key.lower()
        if any(keyword in key_lower for keyword in secret_keywords):
            # Skip if it's clearly a placeholder
            value_lower = value.lower().strip('"\'')
            if value_lower in ['placeholder', 'changeme', 'your-key-here', '', 'none', 'null']:
                return False
            
            # Check for actual values
            if len(value_lower) > 8:  # Minimum length for actual secrets
                return True
        
        return False
    
    def _map_safety_severity(self, safety_severity: str) -> str:
        """Map Safety severity to our scale"""
        mapping = {
            'low': 'low',
            'medium': 'medium',
            'high': 'high',
            'critical': 'critical'
        }
        return mapping.get(safety_severity.lower(), 'medium')
    
    def _calculate_summary(self) -> Dict[str, int]:
        """Calculate summary statistics"""
        summary = {
            'total': len(self.findings),
            'critical': 0,
            'high': 0,
            'medium': 0,
            'low': 0,
            'info': 0
        }
        
        for finding in self.findings:
            severity = finding.severity.lower()
            if severity in summary:
                summary[severity] += 1
        
        return summary
    
    def _calculate_risk_score(self) -> int:
        """Calculate overall risk score (0-100)"""
        if not self.findings:
            return 0
        
        # Weight by severity
        weights = {
            'critical': 10,
            'high': 7,
            'medium': 4,
            'low': 2,
            'info': 1
        }
        
        weighted_score = 0
        for finding in self.findings:
            weighted_score += weights.get(finding.severity.lower(), 1)
        
        # Normalize to 0-100 scale
        max_possible = len(self.findings) * 10
        risk_score = min(100, int((weighted_score / max_possible) * 100))
        
        return risk_score
    
    def _generate_recommendations(self) -> List[str]:
        """Generate security recommendations"""
        recommendations = []
        summary = self._calculate_summary()
        
        if summary['critical'] > 0:
            recommendations.append("Address critical vulnerabilities immediately")
        
        if summary['high'] > 0:
            recommendations.append("Review and fix high-severity issues within 7 days")
        
        # Category-specific recommendations
        categories = set(finding.category for finding in self.findings)
        
        if 'dependency' in categories:
            recommendations.append("Update vulnerable dependencies regularly")
        
        if 'secrets' in categories:
            recommendations.append("Implement proper secret management")
        
        if 'docker' in categories:
            recommendations.append("Follow Docker security best practices")
        
        if 'api' in categories:
            recommendations.append("Implement proper API authentication and authorization")
        
        if 'configuration' in categories:
            recommendations.append("Review and harden configuration files")
        
        # General recommendations
        recommendations.extend([
            "Implement automated security scanning in CI/CD pipeline",
            "Conduct regular security training for development team",
            "Establish incident response procedures",
            "Monitor security advisories for used technologies"
        ])
        
        return recommendations

async def generate_security_report(project_root: str, output_file: str = None) -> SecurityReport:
    """Generate comprehensive security report"""
    scanner = SecurityScanner(project_root)
    report = await scanner.run_full_scan()
    
    if output_file:
        # Save report to file
        with open(output_file, 'w') as f:
            json.dump(asdict(report), f, default=str, indent=2)
        
        logger.info(f"Security report saved to {output_file}")
    
    return report

if __name__ == "__main__":
    import sys
    
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    output_file = sys.argv[2] if len(sys.argv) > 2 else "security_report.json"
    
    asyncio.run(generate_security_report(project_root, output_file))