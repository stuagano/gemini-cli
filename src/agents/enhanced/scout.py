"""
Enhanced Scout Agent
Dedicated codebase analysis agent focused on DRY enforcement and dependency mapping
The key innovation: Scout-First Architecture that prevents AI from reinventing the wheel
"""

import ast
import os
import re
import json
import hashlib
from typing import Dict, List, Any, Optional, Set, Tuple
from datetime import datetime
from pathlib import Path
from collections import defaultdict, Counter
import subprocess

from ..unified_agent_base import UnifiedAgent, AgentConfig


class CodeAnalyzer:
    """Deep code analysis for patterns and structure"""
    
    def __init__(self):
        self.function_signatures = {}
        self.class_definitions = {}
        self.import_graph = defaultdict(set)
        self.api_endpoints = []
        
    def analyze_file(self, file_path: Path) -> Dict[str, Any]:
        """Analyze a single file for patterns and structure"""
        
        if not file_path.exists():
            return {'error': 'File not found'}
            
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
        except Exception as e:
            return {'error': f'Could not read file: {e}'}
        
        analysis = {
            'file_path': str(file_path),
            'language': self._detect_language(file_path),
            'size_lines': len(content.split('\n')),
            'size_bytes': len(content.encode('utf-8')),
            'functions': [],
            'classes': [],
            'imports': [],
            'api_endpoints': [],
            'patterns': [],
            'complexity': 0,
            'test_coverage_hints': [],
            'potential_issues': []
        }
        
        if analysis['language'] == 'python':
            analysis.update(self._analyze_python_file(content, file_path))
        elif analysis['language'] == 'javascript':
            analysis.update(self._analyze_javascript_file(content, file_path))
        elif analysis['language'] == 'typescript':
            analysis.update(self._analyze_typescript_file(content, file_path))
        
        return analysis
    
    def _detect_language(self, file_path: Path) -> str:
        """Detect programming language from file extension"""
        
        extension_map = {
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
            '.rb': 'ruby'
        }
        
        return extension_map.get(file_path.suffix.lower(), 'unknown')
    
    def _analyze_python_file(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Analyze Python file using AST"""
        
        try:
            tree = ast.parse(content)
        except SyntaxError as e:
            return {'error': f'Syntax error: {e}'}
        
        analysis = {
            'functions': [],
            'classes': [],
            'imports': [],
            'api_endpoints': [],
            'patterns': [],
            'complexity': 0
        }
        
        # Analyze AST nodes
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                func_analysis = self._analyze_function(node, content)
                analysis['functions'].append(func_analysis)
                analysis['complexity'] += func_analysis['complexity']
                
                # Check for API endpoint patterns
                if self._is_api_endpoint(node, content):
                    endpoint = self._extract_api_endpoint(node, content)
                    if endpoint:
                        analysis['api_endpoints'].append(endpoint)
                        
            elif isinstance(node, ast.ClassDef):
                class_analysis = self._analyze_class(node, content)
                analysis['classes'].append(class_analysis)
                
            elif isinstance(node, (ast.Import, ast.ImportFrom)):
                import_info = self._analyze_import(node)
                analysis['imports'].extend(import_info)
        
        # Detect common patterns
        analysis['patterns'] = self._detect_python_patterns(content, tree)
        
        # Detect potential issues
        analysis['potential_issues'] = self._detect_python_issues(content, tree)
        
        return analysis
    
    def _analyze_function(self, node: ast.FunctionDef, content: str) -> Dict[str, Any]:
        """Analyze a function definition"""
        
        # Calculate complexity
        complexity = self._calculate_complexity(node)
        
        # Extract docstring
        docstring = ast.get_docstring(node)
        
        # Get function signature
        args = [arg.arg for arg in node.args.args]
        
        # Check for decorators
        decorators = [self._get_decorator_name(dec) for dec in node.decorator_list]
        
        # Analyze return statements
        returns = []
        for child in ast.walk(node):
            if isinstance(child, ast.Return) and child.value:
                returns.append(ast.unparse(child.value) if hasattr(ast, 'unparse') else 'return_value')
        
        return {
            'name': node.name,
            'line_start': node.lineno,
            'line_end': node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
            'args': args,
            'decorators': decorators,
            'docstring': docstring,
            'complexity': complexity,
            'returns': returns,
            'is_async': isinstance(node, ast.AsyncFunctionDef),
            'has_type_hints': bool(node.returns or any(arg.annotation for arg in node.args.args))
        }
    
    def _analyze_class(self, node: ast.ClassDef, content: str) -> Dict[str, Any]:
        """Analyze a class definition"""
        
        methods = []
        properties = []
        
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                methods.append({
                    'name': item.name,
                    'type': 'method',
                    'is_property': any(isinstance(dec, ast.Name) and dec.id == 'property' 
                                     for dec in item.decorator_list),
                    'is_static': any(isinstance(dec, ast.Name) and dec.id == 'staticmethod'
                                   for dec in item.decorator_list),
                    'is_class_method': any(isinstance(dec, ast.Name) and dec.id == 'classmethod'
                                         for dec in item.decorator_list)
                })
                
        base_classes = []
        for base in node.bases:
            if isinstance(base, ast.Name):
                base_classes.append(base.id)
            elif isinstance(base, ast.Attribute):
                base_classes.append(f"{base.value.id}.{base.attr}")
        
        return {
            'name': node.name,
            'line_start': node.lineno,
            'line_end': node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
            'base_classes': base_classes,
            'methods': methods,
            'docstring': ast.get_docstring(node),
            'decorators': [self._get_decorator_name(dec) for dec in node.decorator_list]
        }
    
    def _analyze_import(self, node) -> List[Dict[str, str]]:
        """Analyze import statements"""
        
        imports = []
        
        if isinstance(node, ast.Import):
            for alias in node.names:
                imports.append({
                    'type': 'import',
                    'module': alias.name,
                    'alias': alias.asname,
                    'line': node.lineno
                })
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            for alias in node.names:
                imports.append({
                    'type': 'from_import',
                    'module': module,
                    'name': alias.name,
                    'alias': alias.asname,
                    'line': node.lineno
                })
        
        return imports
    
    def _is_api_endpoint(self, node: ast.FunctionDef, content: str) -> bool:
        """Check if function is an API endpoint"""
        
        # Check for FastAPI decorators
        fastapi_decorators = ['app.get', 'app.post', 'app.put', 'app.delete', 'app.patch']
        
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Attribute):
                decorator_name = f"{decorator.value.id}.{decorator.attr}"
                if decorator_name in fastapi_decorators:
                    return True
            elif isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                decorator_name = f"{decorator.func.value.id}.{decorator.func.attr}"
                if decorator_name in fastapi_decorators:
                    return True
        
        # Check for Flask decorators
        if any('app.route' in self._get_decorator_name(dec) for dec in node.decorator_list):
            return True
        
        return False
    
    def _extract_api_endpoint(self, node: ast.FunctionDef, content: str) -> Optional[Dict[str, Any]]:
        """Extract API endpoint information"""
        
        endpoint_info = {
            'function_name': node.name,
            'methods': [],
            'path': '',
            'line': node.lineno
        }
        
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and isinstance(decorator.func, ast.Attribute):
                method = decorator.func.attr.upper()
                if method in ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']:
                    endpoint_info['methods'] = [method]
                    
                    # Extract path from first argument
                    if decorator.args and isinstance(decorator.args[0], ast.Constant):
                        endpoint_info['path'] = decorator.args[0].value
                        
        return endpoint_info if endpoint_info['methods'] else None
    
    def _get_name(self, node: ast.AST) -> str:
        """Recursively get the full name from a node."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            # Recursively build the name for attribute access like "app.get"
            return f"{self._get_name(node.value)}.{node.attr}"
        elif isinstance(node, ast.Call):
             # Handle cases where the decorator is a call, e.g., @app.route("/")
            return self._get_name(node.func)
        return 'unknown'

    def _get_decorator_name(self, decorator) -> str:
        """Get decorator name as string"""
        return self._get_name(decorator)
    
    def _calculate_complexity(self, node: ast.FunctionDef) -> int:
        """Calculate cyclomatic complexity"""
        
        complexity = 1  # Base complexity
        
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                complexity += 1
            elif isinstance(child, ast.ExceptHandler):
                complexity += 1
            elif isinstance(child, ast.With):
                complexity += 1
            elif isinstance(child, ast.Assert):
                complexity += 1
            elif isinstance(child, ast.BoolOp):
                complexity += len(child.values) - 1
        
        return complexity
    
    def _detect_python_patterns(self, content: str, tree: ast.AST) -> List[Dict[str, str]]:
        """Detect common Python patterns"""
        
        patterns = []
        
        # Singleton pattern
        if 'def __new__' in content and '_instance' in content:
            patterns.append({
                'pattern': 'Singleton',
                'description': 'Singleton pattern implementation detected',
                'confidence': 'high'
            })
        
        # Factory pattern
        if 'def create_' in content or 'def make_' in content:
            patterns.append({
                'pattern': 'Factory',
                'description': 'Factory pattern methods detected',
                'confidence': 'medium'
            })
        
        # Observer pattern
        if 'def notify' in content and 'observers' in content.lower():
            patterns.append({
                'pattern': 'Observer',
                'description': 'Observer pattern implementation detected',
                'confidence': 'high'
            })
        
        # Repository pattern
        if 'Repository' in content and ('def find' in content or 'def save' in content):
            patterns.append({
                'pattern': 'Repository',
                'description': 'Repository pattern detected',
                'confidence': 'high'
            })
        
        return patterns
    
    def _detect_python_issues(self, content: str, tree: ast.AST) -> List[Dict[str, str]]:
        """Detect potential issues in Python code"""
        
        issues = []
        
        # Unbounded queries (THE SCALING KILLER)
        if re.search(r'\.all\(\)|SELECT \* FROM \w+(?!\s+LIMIT)', content, re.IGNORECASE):
            issues.append({
                'type': 'scaling_risk',
                'severity': 'critical',
                'description': 'Unbounded query detected - will cause memory overflow at scale',
                'fix': 'Add LIMIT clause or pagination'
            })
        
        # Missing exception handling
        functions_without_try = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                has_try = any(isinstance(child, ast.Try) for child in ast.walk(node))
                if not has_try and len(node.body) > 3:  # Non-trivial function
                    functions_without_try.append(node.name)
        
        if functions_without_try:
            issues.append({
                'type': 'error_handling',
                'severity': 'medium',
                'description': f'Functions without exception handling: {functions_without_try[:3]}',
                'fix': 'Add try-except blocks for error handling'
            })
        
        # SQL injection risks
        if re.search(r'f".*{.*}.*".*execute|".*%.*".*execute', content):
            issues.append({
                'type': 'security_risk',
                'severity': 'high',
                'description': 'Potential SQL injection vulnerability',
                'fix': 'Use parameterized queries'
            })
        
        return issues
    
    def _analyze_javascript_file(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Analyze JavaScript/TypeScript file"""
        
        # Basic regex-based analysis for JavaScript
        functions = []
        classes = []
        imports = []
        api_endpoints = []
        
        # Find function declarations
        func_pattern = r'(?:function\s+(\w+)|(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s+)?(?:\([^)]*\)\s*=>|\([^)]*\)\s*{\s*|function))'
        for match in re.finditer(func_pattern, content):
            func_name = match.group(1) or match.group(2)
            if func_name:
                functions.append({
                    'name': func_name,
                    'line': content[:match.start()].count('\n') + 1,
                    'type': 'function'
                })
        
        # Find class declarations
        class_pattern = r'class\s+(\w+)'
        for match in re.finditer(class_pattern, content):
            classes.append({
                'name': match.group(1),
                'line': content[:match.start()].count('\n') + 1
            })
        
        # Find import statements
        import_pattern = r'import\s+(?:{[^}]+}|\w+)\s+from\s+[\'"]([^\'"]+)[\'"]'
        for match in re.finditer(import_pattern, content):
            imports.append({
                'type': 'import',
                'module': match.group(1),
                'line': content[:match.start()].count('\n') + 1
            })
        
        # Find API routes (Express.js style)
        route_pattern = r'app\.(get|post|put|delete|patch)\s*\(\s*[\'"]([^\'"]+)[\'"]'
        for match in re.finditer(route_pattern, content):
            api_endpoints.append({
                'method': match.group(1).upper(),
                'path': match.group(2),
                'line': content[:match.start()].count('\n') + 1
            })
        
        return {
            'functions': functions,
            'classes': classes,
            'imports': imports,
            'api_endpoints': api_endpoints,
            'patterns': self._detect_javascript_patterns(content),
            'potential_issues': self._detect_javascript_issues(content)
        }
    
    def _analyze_typescript_file(self, content: str, file_path: Path) -> Dict[str, Any]:
        """Analyze TypeScript file (similar to JavaScript with type info)"""
        
        # Use JavaScript analysis as base
        analysis = self._analyze_javascript_file(content, file_path)
        
        # Add TypeScript-specific analysis
        interfaces = []
        types = []
        
        # Find interface declarations
        interface_pattern = r'interface\s+(\w+)'
        for match in re.finditer(interface_pattern, content):
            interfaces.append({
                'name': match.group(1),
                'line': content[:match.start()].count('\n') + 1
            })
        
        # Find type declarations
        type_pattern = r'type\s+(\w+)\s*='
        for match in re.finditer(type_pattern, content):
            types.append({
                'name': match.group(1),
                'line': content[:match.start()].count('\n') + 1
            })
        
        analysis['interfaces'] = interfaces
        analysis['types'] = types
        
        return analysis
    
    def _detect_javascript_patterns(self, content: str) -> List[Dict[str, str]]:
        """Detect JavaScript/React patterns"""
        
        patterns = []
        
        # React component
        if 'React' in content and ('function' in content or 'const' in content) and 'return' in content:
            patterns.append({
                'pattern': 'React Component',
                'description': 'React functional or class component',
                'confidence': 'high'
            })
        
        # Promise pattern
        if '.then(' in content or 'await' in content:
            patterns.append({
                'pattern': 'Async/Promise',
                'description': 'Asynchronous operation handling',
                'confidence': 'high'
            })
        
        return patterns
    
    def _detect_javascript_issues(self, content: str) -> List[Dict[str, str]]:
        """Detect JavaScript issues"""
        
        issues = []
        
        # Console.log in production code
        if 'console.log' in content:
            issues.append({
                'type': 'debug_code',
                'severity': 'low',
                'description': 'console.log statements found',
                'fix': 'Remove debug statements before production'
            })
        
        # Potential XSS with innerHTML
        if 'innerHTML' in content and ('user' in content.lower() or 'input' in content.lower()):
            issues.append({
                'type': 'security_risk',
                'severity': 'high',
                'description': 'Potential XSS vulnerability with innerHTML',
                'fix': 'Use textContent or sanitize input'
            })
        
        return issues


class DuplicationDetector:
    """Detect code duplication and enforce DRY principles"""
    
    def __init__(self):
        self.function_hashes = {}
        self.code_blocks = {}
        self.similarities = []
        
    def find_duplicates(self, file_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Find duplicate code across files"""
        
        duplicates = {
            'exact_duplicates': [],
            'similar_functions': [],
            'similar_blocks': [],
            'reuse_opportunities': []
        }
        
        # Group functions by similarity
        function_groups = defaultdict(list)
        
        for analysis in file_analyses:
            for func in analysis.get('functions', []):
                # Create a simplified signature for comparison
                signature = self._create_function_signature(func)
                function_groups[signature].append({
                    'function': func,
                    'file': analysis['file_path']
                })
        
        # Find similar functions
        for signature, functions in function_groups.items():
            if len(functions) > 1:
                duplicates['similar_functions'].append({
                    'signature': signature,
                    'occurrences': functions,
                    'count': len(functions),
                    'reuse_potential': 'high' if len(functions) > 2 else 'medium'
                })
        
        # Analyze function content for duplicates
        duplicates['exact_duplicates'] = self._find_exact_duplicates(file_analyses)
        duplicates['reuse_opportunities'] = self._identify_reuse_opportunities(duplicates)
        
        return duplicates
    
    def _create_function_signature(self, func: Dict[str, Any]) -> str:
        """Create a normalized signature for function comparison"""
        
        name_parts = func['name'].lower().split('_')
        args = sorted(func.get('args', []))
        
        # Create signature based on name pattern and arguments
        signature = f"{len(name_parts)}:{len(args)}:{':'.join(name_parts[:3])}"
        
        return signature
    
    def _find_exact_duplicates(self, file_analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Find exact code duplicates"""
        
        exact_duplicates = []
        seen_hashes = {}
        
        for analysis in file_analyses:
            for func in analysis.get('functions', []):
                # Create hash of function structure (simplified)
                func_hash = self._hash_function_structure(func)
                
                if func_hash in seen_hashes:
                    exact_duplicates.append({
                        'original': seen_hashes[func_hash],
                        'duplicate': {
                            'function': func['name'],
                            'file': analysis['file_path'],
                            'line': func.get('line_start', 0)
                        },
                        'hash': func_hash
                    })
                else:
                    seen_hashes[func_hash] = {
                        'function': func['name'],
                        'file': analysis['file_path'],
                        'line': func.get('line_start', 0)
                    }
        
        return exact_duplicates
    
    def _hash_function_structure(self, func: Dict[str, Any]) -> str:
        """Create hash of function structure"""
        
        # Hash based on function characteristics
        characteristics = [
            str(len(func.get('args', []))),
            str(func.get('complexity', 0)),
            str(len(func.get('returns', []))),
            func['name'].lower()
        ]
        
        return hashlib.md5('|'.join(characteristics).encode()).hexdigest()[:8]
    
    def _identify_reuse_opportunities(self, duplicates: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Identify opportunities for code reuse"""
        
        opportunities = []
        
        # High-frequency similar functions
        for similar in duplicates['similar_functions']:
            if similar['count'] >= 3:
                opportunities.append({
                    'type': 'extract_common_function',
                    'description': f"Extract common function for {similar['signature']}",
                    'impact': 'high',
                    'files_affected': len(similar['occurrences']),
                    'suggestion': f"Create reusable function for pattern: {similar['signature']}"
                })
        
        # Exact duplicates
        for exact in duplicates['exact_duplicates']:
            opportunities.append({
                'type': 'remove_duplicate',
                'description': f"Remove duplicate function {exact['duplicate']['function']}",
                'impact': 'medium',
                'files_affected': 2,
                'suggestion': f"Import {exact['original']['function']} from {exact['original']['file']}"
            })
        
        return opportunities


class DependencyMapper:
    """Map and analyze code dependencies"""
    
    def __init__(self):
        self.dependency_graph = defaultdict(set)
        self.reverse_dependencies = defaultdict(set)
        self.circular_dependencies = []
        
    def build_dependency_map(self, file_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Build comprehensive dependency map"""
        
        # Build import graph
        for analysis in file_analyses:
            file_path = analysis['file_path']
            
            for import_info in analysis.get('imports', []):
                module = import_info.get('module', '')
                if module:
                    self.dependency_graph[file_path].add(module)
                    self.reverse_dependencies[module].add(file_path)
        
        # Find circular dependencies
        self.circular_dependencies = self._find_circular_dependencies()
        
        # Calculate dependency metrics
        dependency_metrics = self._calculate_dependency_metrics()
        
        # Identify critical paths
        critical_paths = self._identify_critical_paths()
        
        return {
            'dependency_graph': dict(self.dependency_graph),
            'reverse_dependencies': dict(self.reverse_dependencies),
            'circular_dependencies': self.circular_dependencies,
            'metrics': dependency_metrics,
            'critical_paths': critical_paths,
            'refactoring_suggestions': self._suggest_refactoring()
        }
    
    def _find_circular_dependencies(self) -> List[List[str]]:
        """Find circular dependency chains"""
        
        visited = set()
        rec_stack = set()
        cycles = []
        
        def dfs(node, path):
            if node in rec_stack:
                # Found cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
                
            visited.add(node)
            rec_stack.add(node)
            
            for neighbor in self.dependency_graph.get(node, []):
                dfs(neighbor, path + [node])
            
            rec_stack.remove(node)
        
        for node in self.dependency_graph:
            if node not in visited:
                dfs(node, [])
        
        return cycles
    
    def _calculate_dependency_metrics(self) -> Dict[str, Any]:
        """Calculate dependency metrics"""
        
        total_files = len(self.dependency_graph)
        total_dependencies = sum(len(deps) for deps in self.dependency_graph.values())
        
        # Fan-out (files this file depends on)
        fan_out = {file: len(deps) for file, deps in self.dependency_graph.items()}
        
        # Fan-in (files that depend on this file)
        fan_in = {file: len(deps) for file, deps in self.reverse_dependencies.items()}
        
        # Instability metric (Fan-out / (Fan-in + Fan-out))
        instability = {}
        for file in set(list(self.dependency_graph.keys()) + list(self.reverse_dependencies.keys())):
            fo = fan_out.get(file, 0)
            fi = fan_in.get(file, 0)
            if fo + fi > 0:
                instability[file] = fo / (fo + fi)
            else:
                instability[file] = 0
        
        return {
            'total_files': total_files,
            'total_dependencies': total_dependencies,
            'average_dependencies_per_file': total_dependencies / total_files if total_files > 0 else 0,
            'max_fan_out': max(fan_out.values()) if fan_out else 0,
            'max_fan_in': max(fan_in.values()) if fan_in else 0,
            'fan_out': fan_out,
            'fan_in': fan_in,
            'instability': instability,
            'circular_dependency_count': len(self.circular_dependencies)
        }
    
    def _identify_critical_paths(self) -> List[Dict[str, Any]]:
        """Identify critical dependency paths"""
        
        critical_paths = []
        
        # Files with high fan-in (many dependents)
        fan_in_counts = {file: len(deps) for file, deps in self.reverse_dependencies.items()}
        
        for file, count in sorted(fan_in_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
            if count > 3:  # Threshold for "critical"
                critical_paths.append({
                    'file': file,
                    'dependents': list(self.reverse_dependencies[file]),
                    'dependent_count': count,
                    'risk_level': 'high' if count > 10 else 'medium',
                    'impact': 'Changes to this file affect many other files'
                })
        
        return critical_paths
    
    def _suggest_refactoring(self) -> List[Dict[str, str]]:
        """Suggest dependency refactoring"""
        
        suggestions = []
        
        # Circular dependencies
        if self.circular_dependencies:
            suggestions.append({
                'type': 'break_circular_dependencies',
                'description': f'Break {len(self.circular_dependencies)} circular dependencies',
                'priority': 'high',
                'impact': 'Reduces coupling and improves maintainability'
            })
        
        # High fan-out files
        metrics = self._calculate_dependency_metrics()
        high_fan_out = {f: fo for f, fo in metrics['fan_out'].items() if fo > 10}
        
        if high_fan_out:
            suggestions.append({
                'type': 'reduce_fan_out',
                'description': f'Reduce dependencies in {len(high_fan_out)} files',
                'priority': 'medium',
                'impact': 'Improves modularity and testability'
            })
        
        return suggestions


class TechDebtAnalyzer:
    """Analyze technical debt and code quality issues"""
    
    def __init__(self):
        self.debt_items = []
        self.code_smells = []
        self.quality_metrics = {}
        
    def analyze_technical_debt(self, file_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Comprehensive technical debt analysis"""
        
        debt_analysis = {
            'debt_items': [],
            'code_smells': [],
            'quality_score': 0,
            'priority_fixes': [],
            'refactoring_opportunities': [],
            'maintainability_index': 0
        }
        
        total_complexity = 0
        total_functions = 0
        high_complexity_functions = []
        
        for analysis in file_analyses:
            file_debt = self._analyze_file_debt(analysis)
            debt_analysis['debt_items'].extend(file_debt['debt_items'])
            debt_analysis['code_smells'].extend(file_debt['code_smells'])
            
            # Calculate complexity metrics
            for func in analysis.get('functions', []):
                complexity = func.get('complexity', 1)
                total_complexity += complexity
                total_functions += 1
                
                if complexity > 10:
                    high_complexity_functions.append({
                        'function': func['name'],
                        'file': analysis['file_path'],
                        'complexity': complexity,
                        'line': func.get('line_start', 0)
                    })
        
        # Calculate overall metrics
        avg_complexity = total_complexity / total_functions if total_functions > 0 else 0
        debt_analysis['average_complexity'] = avg_complexity
        debt_analysis['high_complexity_functions'] = high_complexity_functions
        
        # Calculate quality score
        debt_analysis['quality_score'] = self._calculate_quality_score(debt_analysis)
        
        # Prioritize fixes
        debt_analysis['priority_fixes'] = self._prioritize_fixes(debt_analysis)
        
        # Suggest refactoring
        debt_analysis['refactoring_opportunities'] = self._suggest_refactoring_opportunities(debt_analysis)
        
        return debt_analysis
    
    def _analyze_file_debt(self, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze technical debt in a single file"""
        
        debt_items = []
        code_smells = []
        
        # Check for potential issues from code analysis
        for issue in analysis.get('potential_issues', []):
            if issue.get('severity') in ['critical', 'high']:
                debt_items.append({
                    'type': issue['type'],
                    'severity': issue['severity'],
                    'description': issue['description'],
                    'file': analysis['file_path'],
                    'fix': issue.get('fix', 'Manual fix required'),
                    'effort': self._estimate_fix_effort(issue)
                })
        
        # Detect code smells
        functions = analysis.get('functions', [])
        
        # Long functions (code smell)
        long_functions = [f for f in functions if f.get('line_end', 0) - f.get('line_start', 0) > 50]
        for func in long_functions:
            code_smells.append({
                'smell': 'long_function',
                'description': f"Function '{func['name']}' is too long ({func.get('line_end', 0) - func.get('line_start', 0)} lines)",
                'file': analysis['file_path'],
                'function': func['name'],
                'severity': 'medium'
            })
        
        # Functions with too many parameters
        complex_params = [f for f in functions if len(f.get('args', [])) > 5]
        for func in complex_params:
            code_smells.append({
                'smell': 'too_many_parameters',
                'description': f"Function '{func['name']}' has too many parameters ({len(func['args'])})",
                'file': analysis['file_path'],
                'function': func['name'],
                'severity': 'low'
            })
        
        # Missing documentation
        undocumented = [f for f in functions if not f.get('docstring') and len(f.get('args', [])) > 2]
        for func in undocumented:
            code_smells.append({
                'smell': 'missing_documentation',
                'description': f"Function '{func['name']}' lacks documentation",
                'file': analysis['file_path'],
                'function': func['name'],
                'severity': 'low'
            })
        
        return {
            'debt_items': debt_items,
            'code_smells': code_smells
        }
    
    def _estimate_fix_effort(self, issue: Dict[str, Any]) -> str:
        """Estimate effort required to fix issue"""
        
        effort_map = {
            'scaling_risk': 'high',
            'security_risk': 'high',
            'error_handling': 'medium',
            'debug_code': 'low'
        }
        
        return effort_map.get(issue.get('type'), 'medium')
    
    def _calculate_quality_score(self, debt_analysis: Dict[str, Any]) -> float:
        """Calculate overall code quality score (0-100)"""
        
        # Start with perfect score
        score = 100.0
        
        # Deduct for debt items
        critical_debt = len([d for d in debt_analysis['debt_items'] if d.get('severity') == 'critical'])
        high_debt = len([d for d in debt_analysis['debt_items'] if d.get('severity') == 'high'])
        medium_debt = len([d for d in debt_analysis['debt_items'] if d.get('severity') == 'medium'])
        
        score -= critical_debt * 15  # -15 points per critical issue
        score -= high_debt * 10      # -10 points per high severity issue
        score -= medium_debt * 5     # -5 points per medium severity issue
        
        # Deduct for complexity
        avg_complexity = debt_analysis.get('average_complexity', 0)
        if avg_complexity > 5:
            score -= (avg_complexity - 5) * 2
        
        # Deduct for code smells
        score -= len(debt_analysis['code_smells']) * 1
        
        return max(0, min(100, score))
    
    def _prioritize_fixes(self, debt_analysis: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Prioritize technical debt fixes"""
        
        all_issues = debt_analysis['debt_items'] + [
            {
                'type': 'code_smell',
                'severity': smell['severity'],
                'description': smell['description'],
                'file': smell['file']
            }
            for smell in debt_analysis['code_smells']
        ]
        
        # Sort by severity and impact
        severity_order = {'critical': 0, 'high': 1, 'medium': 2, 'low': 3}
        
        prioritized = sorted(all_issues, key=lambda x: (
            severity_order.get(x.get('severity'), 4),
            -len(x.get('description', ''))  # Longer descriptions suggest more complex issues
        ))
        
        return prioritized[:10]  # Top 10 priority fixes
    
    def _suggest_refactoring_opportunities(self, debt_analysis: Dict[str, Any]) -> List[Dict[str, str]]:
        """Suggest refactoring opportunities"""
        
        opportunities = []
        
        # High complexity functions
        high_complexity = debt_analysis.get('high_complexity_functions', [])
        if high_complexity:
            opportunities.append({
                'type': 'reduce_complexity',
                'description': f'Refactor {len(high_complexity)} high-complexity functions',
                'benefit': 'Improves maintainability and testability',
                'effort': 'medium'
            })
        
        # Files with many code smells
        smell_files = {}
        for smell in debt_analysis['code_smells']:
            file_path = smell['file']
            smell_files[file_path] = smell_files.get(file_path, 0) + 1
        
        problematic_files = {f: count for f, count in smell_files.items() if count >= 3}
        if problematic_files:
            opportunities.append({
                'type': 'refactor_files',
                'description': f'Refactor {len(problematic_files)} files with multiple code smells',
                'benefit': 'Significant quality improvement',
                'effort': 'high'
            })
        
        return opportunities


class EnhancedScout(UnifiedAgent):
    """
    Enhanced Scout Agent - The DRY Enforcer and Codebase Intelligence
    Sam - Senior Scout focused on codebase analysis and preventing code duplication
    """
    
    def __init__(self, developer_level: str = "intermediate"):
        config = self._load_bmad_config()
        super().__init__(config, developer_level)
        
        # Enhanced capabilities
        self.code_analyzer = CodeAnalyzer()
        self.duplication_detector = DuplicationDetector()
        self.dependency_mapper = DependencyMapper()
        self.tech_debt_analyzer = TechDebtAnalyzer()
        
        # Scout state
        self.codebase_map = {}
        self.reuse_opportunities = {}
        self.analysis_history = []
        
    def _load_bmad_config(self) -> AgentConfig:
        """Load BMAD scout configuration"""
        return AgentConfig(
            id="scout",
            name="Sam",
            title="Senior Scout & DRY Enforcer",
            icon="🕵️",
            when_to_use="Use before any development work to analyze codebase, find reusable components, prevent duplication",
            persona={
                'role': 'Senior Scout & Codebase Intelligence Officer',
                'style': 'Analytical, thorough, pattern-focused, preventive',
                'identity': 'Expert at finding existing solutions and preventing code duplication',
                'focus': 'Code reuse, DRY principles, dependency analysis, tech debt prevention',
                'core_principles': [
                    'Scout before you build',
                    'DRY principles are sacred',
                    'Reuse beats recreation',
                    'Map before you code',
                    'Prevent technical debt'
                ]
            },
            commands=[
                {'name': 'analyze-codebase', 'description': 'Comprehensive codebase analysis'},
                {'name': 'find-reuse-opportunities', 'description': 'Find reusable components'},
                {'name': 'detect-duplicates', 'description': 'Detect code duplication'},
                {'name': 'map-dependencies', 'description': 'Map and analyze dependencies'},
                {'name': 'assess-tech-debt', 'description': 'Analyze technical debt'}
            ],
            dependencies={
                'templates': ['analysis-report-tmpl.yaml'],
                'data': ['code-patterns.md', 'reuse-guidelines.md'],
                'checklists': ['scout-checklist.md']
            }
        )
    
    def execute_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute scout-specific tasks"""
        
        if task == "analyze_codebase":
            return self.analyze_codebase(context)
        elif task == "find_reuse_opportunities":
            return self.find_reuse_opportunities(context)
        elif task == "detect_duplicates":
            return self.detect_duplicates(context)
        elif task == "map_dependencies":
            return self.map_dependencies(context)
        elif task == "assess_tech_debt":
            return self.assess_tech_debt(context)
        else:
            return {'error': f'Unknown task: {task}'}
    
    def analyze_codebase(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Comprehensive codebase analysis - THE CORE SCOUT FUNCTION"""
        
        codebase_path = context.get('codebase_path', '.')
        target_files = context.get('target_files', None)
        
        # Discover all relevant files
        files_to_analyze = self._discover_files(codebase_path, target_files)
        
        # Analyze each file
        file_analyses = []
        for file_path in files_to_analyze:
            analysis = self.code_analyzer.analyze_file(Path(file_path))
            if 'error' not in analysis:
                file_analyses.append(analysis)
        
        # Create comprehensive codebase map
        codebase_map = {
            'summary': {
                'total_files': len(file_analyses),
                'languages': self._get_language_distribution(file_analyses),
                'total_functions': sum(len(a.get('functions', [])) for a in file_analyses),
                'total_classes': sum(len(a.get('classes', [])) for a in file_analyses),
                'total_api_endpoints': sum(len(a.get('api_endpoints', [])) for a in file_analyses),
                'analysis_timestamp': datetime.now().isoformat()
            },
            'files': file_analyses,
            'patterns': self._extract_patterns(file_analyses),
            'architecture_insights': self._analyze_architecture(file_analyses),
            'quality_overview': self._assess_quality(file_analyses)
        }
        
        # Find duplicates and reuse opportunities
        duplicates = self.duplication_detector.find_duplicates(file_analyses)
        codebase_map['duplicates'] = duplicates
        
        # Map dependencies
        dependencies = self.dependency_mapper.build_dependency_map(file_analyses)
        codebase_map['dependencies'] = dependencies
        
        # Analyze technical debt
        tech_debt = self.tech_debt_analyzer.analyze_technical_debt(file_analyses)
        codebase_map['tech_debt'] = tech_debt
        
        # Generate reuse recommendations
        reuse_recommendations = self._generate_reuse_recommendations(codebase_map)
        codebase_map['reuse_recommendations'] = reuse_recommendations
        
        # Store analysis
        self.codebase_map = codebase_map
        self.analysis_history.append({
            'timestamp': datetime.now().isoformat(),
            'path': codebase_path,
            'file_count': len(file_analyses)
        })
        
        # Teach about findings
        self._teach_analysis_insights(codebase_map)
        
        return codebase_map
    
    def find_reuse_opportunities(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Find specific reuse opportunities for a new requirement"""
        
        requirement = context.get('requirement', {})
        story = context.get('story', {})
        
        if not self.codebase_map:
            # Need to analyze codebase first
            return {
                'error': 'Codebase not analyzed yet',
                'suggestion': 'Run analyze_codebase first'
            }
        
        # Extract requirement characteristics
        req_characteristics = self._extract_requirement_characteristics(requirement, story)
        
        # Find matching components
        matches = self._find_matching_components(req_characteristics)
        
        # Score and rank opportunities
        opportunities = self._rank_reuse_opportunities(matches, req_characteristics)
        
        # Generate reuse plan
        reuse_plan = self._create_reuse_plan(opportunities)
        
        # Teach about DRY principles
        if opportunities:
            self.teaching_engine.teach(
                "DRY Principle Application",
                {
                    'what': f"Found {len(opportunities)} reuse opportunities",
                    'why': "Reusing existing code reduces bugs and development time",
                    'how': f"Reuse {opportunities[0]['component']} instead of recreating",
                    'example': f"Save ~{opportunities[0].get('estimated_time_saved', 'N/A')} development time"
                }
            )
        else:
            self.teaching_engine.teach(
                "New Component Needed",
                {
                    'what': "No existing components match this requirement",
                    'why': "This is genuinely new functionality",
                    'how': "Design for reusability from the start",
                    'example': "Make it generic so future requirements can reuse it"
                }
            )
        
        return {
            'requirement_analysis': req_characteristics,
            'reuse_opportunities': opportunities,
            'reuse_plan': reuse_plan,
            'dry_score': len(opportunities) / max(1, len(req_characteristics.get('features', []))),
            'recommendations': self._generate_dry_recommendations(opportunities)
        }
    
    def detect_duplicates(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Detect code duplication across codebase"""
        
        if not self.codebase_map:
            return {'error': 'Codebase not analyzed yet'}
        
        file_analyses = self.codebase_map.get('files', [])
        duplicates = self.duplication_detector.find_duplicates(file_analyses)
        
        # Enhanced duplicate analysis
        enhanced_duplicates = {
            **duplicates,
            'duplicate_metrics': self._calculate_duplicate_metrics(duplicates),
            'refactoring_plan': self._create_refactoring_plan(duplicates),
            'effort_estimation': self._estimate_refactoring_effort(duplicates)
        }
        
        # Teach about duplication issues
        if duplicates['exact_duplicates'] or duplicates['similar_functions']:
            self.teaching_engine.teach(
                "Code Duplication Detected",
                {
                    'what': f"Found {len(duplicates['exact_duplicates'])} exact duplicates",
                    'why': "Code duplication violates DRY principle and increases maintenance burden",
                    'how': "Extract common functionality into reusable components",
                    'example': f"Consolidate {duplicates['similar_functions'][0]['count']} similar functions" if duplicates['similar_functions'] else "Use imports instead of copying code"
                }
            )
        
        return enhanced_duplicates
    
    def map_dependencies(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Map and analyze codebase dependencies"""
        
        if not self.codebase_map:
            return {'error': 'Codebase not analyzed yet'}
        
        dependencies = self.codebase_map.get('dependencies', {})
        
        # Enhanced dependency analysis
        enhanced_dependencies = {
            **dependencies,
            'dependency_health': self._assess_dependency_health(dependencies),
            'refactoring_suggestions': self._suggest_dependency_refactoring(dependencies),
            'impact_analysis': self._analyze_change_impact(dependencies)
        }
        
        # Teach about dependency management
        if dependencies.get('circular_dependencies'):
            self.teaching_engine.teach(
                "Circular Dependencies Detected",
                {
                    'what': f"Found {len(dependencies['circular_dependencies'])} circular dependencies",
                    'why': "Circular dependencies make code hard to test and maintain",
                    'how': "Break cycles using dependency injection or interface abstraction",
                    'example': "Move shared code to a common module"
                }
            )
        
        return enhanced_dependencies
    
    def assess_tech_debt(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess technical debt across codebase"""
        
        if not self.codebase_map:
            return {'error': 'Codebase not analyzed yet'}
        
        tech_debt = self.codebase_map.get('tech_debt', {})
        
        # Enhanced tech debt analysis
        enhanced_debt = {
            **tech_debt,
            'debt_trends': self._analyze_debt_trends(),
            'payoff_analysis': self._calculate_debt_payoff(tech_debt),
            'remediation_roadmap': self._create_remediation_roadmap(tech_debt)
        }
        
        # Teach about technical debt
        quality_score = tech_debt.get('quality_score', 100)
        if quality_score < 70:
            self.teaching_engine.teach(
                "Technical Debt Alert",
                {
                    'what': f"Quality score: {quality_score}/100",
                    'why': "High technical debt slows development and increases bugs",
                    'how': f"Focus on {tech_debt.get('priority_fixes', [{}])[0].get('description', 'code quality')}",
                    'example': "Refactoring pays off in reduced maintenance time"
                }
            )
        
        return enhanced_debt
    
    def _discover_files(self, codebase_path: str, target_files: Optional[List[str]]) -> List[str]:
        """Discover files to analyze"""
        
        if target_files:
            return target_files
        
        # Auto-discover relevant files
        relevant_extensions = {'.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.go', '.rs', '.cpp', '.c'}
        exclude_patterns = {'node_modules', '__pycache__', '.git', 'venv', 'env', 'dist', 'build'}
        
        files = []
        base_path = Path(codebase_path)
        
        if not base_path.exists():
            return []
        
        for file_path in base_path.rglob('*'):
            if (file_path.is_file() and 
                file_path.suffix in relevant_extensions and
                not any(pattern in str(file_path) for pattern in exclude_patterns)):
                files.append(str(file_path))
        
        return files
    
    def _get_language_distribution(self, file_analyses: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of programming languages"""
        
        language_counts = Counter(analysis.get('language', 'unknown') for analysis in file_analyses)
        return dict(language_counts)
    
    def _extract_patterns(self, file_analyses: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Extract common patterns across files"""
        
        all_patterns = []
        for analysis in file_analyses:
            for pattern in analysis.get('patterns', []):
                pattern['file'] = analysis['file_path']
                all_patterns.append(pattern)
        
        # Group similar patterns
        pattern_groups = defaultdict(list)
        for pattern in all_patterns:
            pattern_groups[pattern['pattern']].append(pattern)
        
        # Return pattern summary
        pattern_summary = []
        for pattern_type, occurrences in pattern_groups.items():
            pattern_summary.append({
                'pattern': pattern_type,
                'occurrences': len(occurrences),
                'files': list(set(p['file'] for p in occurrences)),
                'consistency': len(set(p.get('confidence', 'medium') for p in occurrences)) == 1
            })
        
        return sorted(pattern_summary, key=lambda x: x['occurrences'], reverse=True)
    
    def _analyze_architecture(self, file_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze overall architecture from code structure"""
        
        # Analyze API structure
        all_endpoints = []
        for analysis in file_analyses:
            all_endpoints.extend(analysis.get('api_endpoints', []))
        
        # Group by path patterns
        path_patterns = defaultdict(list)
        for endpoint in all_endpoints:
            path = endpoint.get('path', '')
            # Extract base path (first segment)
            base_path = path.split('/')[1] if path.startswith('/') and len(path.split('/')) > 1 else 'root'
            path_patterns[base_path].append(endpoint)
        
        # Analyze class hierarchies
        all_classes = []
        for analysis in file_analyses:
            all_classes.extend(analysis.get('classes', []))
        
        inheritance_tree = defaultdict(list)
        for cls in all_classes:
            for base in cls.get('base_classes', []):
                inheritance_tree[base].append(cls['name'])
        
        return {
            'api_structure': {
                'total_endpoints': len(all_endpoints),
                'path_groups': dict(path_patterns),
                'methods_used': list(set(ep.get('method', 'GET') for ep in all_endpoints))
            },
            'class_structure': {
                'total_classes': len(all_classes),
                'inheritance_tree': dict(inheritance_tree),
                'common_base_classes': [base for base, derived in inheritance_tree.items() if len(derived) > 1]
            },
            'architectural_style': self._infer_architectural_style(file_analyses)
        }
    
    def _infer_architectural_style(self, file_analyses: List[Dict[str, Any]]) -> str:
        """Infer architectural style from code patterns"""
        
        has_controllers = any('controller' in str(analysis).lower() for analysis in file_analyses)
        has_services = any('service' in str(analysis).lower() for analysis in file_analyses)
        has_repositories = any('repository' in str(analysis).lower() for analysis in file_analyses)
        has_models = any('model' in str(analysis).lower() for analysis in file_analyses)
        
        if has_controllers and has_services and has_repositories:
            return 'layered_architecture'
        elif any('component' in str(analysis).lower() for analysis in file_analyses):
            return 'component_based'
        elif len([a for a in file_analyses if a.get('api_endpoints')]) > 5:
            return 'api_first'
        else:
            return 'monolithic'
    
    def _assess_quality(self, file_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Assess overall code quality"""
        
        total_functions = 0
        documented_functions = 0
        high_complexity_count = 0
        total_issues = 0
        
        for analysis in file_analyses:
            functions = analysis.get('functions', [])
            total_functions += len(functions)
            
            documented_functions += len([f for f in functions if f.get('docstring')])
            high_complexity_count += len([f for f in functions if f.get('complexity', 0) > 10])
            total_issues += len(analysis.get('potential_issues', []))
        
        return {
            'documentation_coverage': (documented_functions / total_functions * 100) if total_functions > 0 else 0,
            'complexity_issues': high_complexity_count,
            'potential_issues': total_issues,
            'overall_quality': self._calculate_overall_quality(file_analyses)
        }
    
    def _calculate_overall_quality(self, file_analyses: List[Dict[str, Any]]) -> float:
        """Calculate overall quality score"""
        
        score = 100.0
        
        # Deduct for issues
        total_critical = sum(len([i for i in analysis.get('potential_issues', []) 
                                if i.get('severity') == 'critical']) 
                           for analysis in file_analyses)
        total_high = sum(len([i for i in analysis.get('potential_issues', []) 
                            if i.get('severity') == 'high']) 
                       for analysis in file_analyses)
        
        score -= total_critical * 20
        score -= total_high * 10
        
        # Factor in documentation
        total_functions = sum(len(analysis.get('functions', [])) for analysis in file_analyses)
        documented = sum(len([f for f in analysis.get('functions', []) if f.get('docstring')]) 
                        for analysis in file_analyses)
        
        if total_functions > 0:
            doc_score = documented / total_functions * 100
            score = score * 0.7 + doc_score * 0.3
        
        return max(0, min(100, score))
    
    def _generate_reuse_recommendations(self, codebase_map: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Generate reuse recommendations from analysis"""
        
        recommendations = []
        
        # Recommendations from duplicates
        duplicates = codebase_map.get('duplicates', {})
        for opportunity in duplicates.get('reuse_opportunities', []):
            recommendations.append({
                'type': 'remove_duplication',
                'priority': 'high',
                'description': opportunity['suggestion'],
                'impact': opportunity['impact'],
                'files_affected': opportunity['files_affected']
            })
        
        # Recommendations from patterns
        patterns = codebase_map.get('patterns', [])
        common_patterns = [p for p in patterns if p['occurrences'] > 2]
        for pattern in common_patterns:
            recommendations.append({
                'type': 'standardize_pattern',
                'priority': 'medium',
                'description': f"Standardize {pattern['pattern']} implementation across {len(pattern['files'])} files",
                'impact': 'medium',
                'files_affected': len(pattern['files'])
            })
        
        return recommendations
    
    def _teach_analysis_insights(self, codebase_map: Dict[str, Any]):
        """Teach insights from codebase analysis"""
        
        summary = codebase_map['summary']
        duplicates = codebase_map.get('duplicates', {})
        tech_debt = codebase_map.get('tech_debt', {})
        
        # Teach about codebase size and structure
        self.teaching_engine.teach(
            "Codebase Analysis Complete",
            {
                'what': f"Analyzed {summary['total_files']} files with {summary['total_functions']} functions",
                'why': "Scout analysis prevents code duplication and identifies reuse opportunities",
                'how': f"Found {len(duplicates.get('reuse_opportunities', []))} reuse opportunities",
                'example': f"Quality score: {tech_debt.get('quality_score', 'N/A')}/100"
            }
        )
        
        # Teach about DRY violations if found
        if duplicates.get('similar_functions'):
            similar_count = len(duplicates['similar_functions'])
            self.teaching_engine.teach(
                "DRY Principle Violations",
                {
                    'what': f"Found {similar_count} groups of similar functions",
                    'why': "Similar functions suggest missing abstractions",
                    'how': "Extract common functionality into reusable utilities",
                    'example': "One well-designed function is better than three similar ones"
                }
            )
    
    def _extract_requirement_characteristics(self, requirement: Dict[str, Any], 
                                           story: Dict[str, Any]) -> Dict[str, Any]:
        """Extract characteristics from requirement/story for matching"""
        
        # Combine text from requirement and story
        text_content = ' '.join([
            str(requirement.get('description', '')),
            str(story.get('title', '')),
            str(story.get('user_story', '')),
            ' '.join(story.get('acceptance_criteria', []))
        ]).lower()
        
        # Extract feature keywords
        feature_keywords = set()
        
        # Common feature patterns
        patterns = {
            'authentication': ['login', 'auth', 'signin', 'signup', 'register', 'logout'],
            'crud': ['create', 'read', 'update', 'delete', 'add', 'edit', 'remove'],
            'search': ['search', 'find', 'filter', 'query', 'lookup'],
            'validation': ['validate', 'check', 'verify', 'confirm'],
            'notification': ['notify', 'alert', 'message', 'email', 'send'],
            'reporting': ['report', 'analytics', 'dashboard', 'chart', 'graph'],
            'file_handling': ['upload', 'download', 'file', 'document', 'attachment'],
            'user_management': ['user', 'profile', 'account', 'role', 'permission'],
            'payment': ['payment', 'billing', 'invoice', 'charge', 'subscription'],
            'api': ['api', 'endpoint', 'rest', 'json', 'request', 'response']
        }
        
        for feature, keywords in patterns.items():
            if any(keyword in text_content for keyword in keywords):
                feature_keywords.add(feature)
        
        # Extract technical requirements
        tech_requirements = set()
        if 'database' in text_content or 'data' in text_content:
            tech_requirements.add('database')
        if 'api' in text_content or 'endpoint' in text_content:
            tech_requirements.add('api')
        if 'ui' in text_content or 'interface' in text_content:
            tech_requirements.add('ui')
        
        return {
            'features': list(feature_keywords),
            'technical_requirements': list(tech_requirements),
            'complexity': self._estimate_requirement_complexity(text_content),
            'text_content': text_content
        }
    
    def _estimate_requirement_complexity(self, text: str) -> str:
        """Estimate complexity of requirement"""
        
        complex_keywords = ['integrate', 'algorithm', 'complex', 'multiple', 'advanced']
        simple_keywords = ['display', 'show', 'list', 'basic', 'simple']
        
        complex_count = sum(1 for keyword in complex_keywords if keyword in text)
        simple_count = sum(1 for keyword in simple_keywords if keyword in text)
        
        if complex_count > simple_count:
            return 'high'
        elif simple_count > complex_count:
            return 'low'
        else:
            return 'medium'
    
    def _find_matching_components(self, characteristics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Find existing components that match requirement characteristics"""
        
        matches = []
        
        if not self.codebase_map:
            return matches
        
        # Search functions
        for file_analysis in self.codebase_map.get('files', []):
            for func in file_analysis.get('functions', []):
                match_score = self._calculate_function_match_score(func, characteristics, file_analysis)
                
                if match_score > 0.3:  # Threshold for potential match
                    matches.append({
                        'type': 'function',
                        'name': func['name'],
                        'file': file_analysis['file_path'],
                        'match_score': match_score,
                        'details': func,
                        'reuse_type': 'direct' if match_score > 0.7 else 'adaptation'
                    })
        
        # Search classes
        for file_analysis in self.codebase_map.get('files', []):
            for cls in file_analysis.get('classes', []):
                match_score = self._calculate_class_match_score(cls, characteristics, file_analysis)
                
                if match_score > 0.3:
                    matches.append({
                        'type': 'class',
                        'name': cls['name'],
                        'file': file_analysis['file_path'],
                        'match_score': match_score,
                        'details': cls,
                        'reuse_type': 'inheritance' if match_score > 0.6 else 'composition'
                    })
        
        # Search API endpoints
        for file_analysis in self.codebase_map.get('files', []):
            for endpoint in file_analysis.get('api_endpoints', []):
                match_score = self._calculate_endpoint_match_score(endpoint, characteristics)
                
                if match_score > 0.4:
                    matches.append({
                        'type': 'api_endpoint',
                        'name': f"{endpoint.get('method', 'GET')} {endpoint.get('path', '')}",
                        'file': file_analysis['file_path'],
                        'match_score': match_score,
                        'details': endpoint,
                        'reuse_type': 'template'
                    })
        
        return matches
    
    def _calculate_function_match_score(self, func: Dict[str, Any], 
                                       characteristics: Dict[str, Any],
                                       file_analysis: Dict[str, Any]) -> float:
        """Calculate how well a function matches requirement characteristics"""
        
        score = 0.0
        
        func_name = func['name'].lower()
        func_file = file_analysis['file_path'].lower()
        
        # Check feature keywords
        for feature in characteristics.get('features', []):
            if feature in func_name or feature in func_file:
                score += 0.3
        
        # Check function name patterns
        name_keywords = func_name.replace('_', ' ').split()
        req_keywords = set(characteristics.get('text_content', '').split())
        
        common_keywords = set(name_keywords) & req_keywords
        if common_keywords:
            score += len(common_keywords) * 0.1
        
        # Bonus for common patterns
        if any(pattern in func_name for pattern in ['create', 'get', 'update', 'delete']):
            if 'crud' in characteristics.get('features', []):
                score += 0.2
        
        return min(1.0, score)
    
    def _calculate_class_match_score(self, cls: Dict[str, Any], 
                                    characteristics: Dict[str, Any],
                                    file_analysis: Dict[str, Any]) -> float:
        """Calculate how well a class matches requirement characteristics"""
        
        score = 0.0
        
        class_name = cls['name'].lower()
        class_file = file_analysis['file_path'].lower()
        
        # Check feature keywords
        for feature in characteristics.get('features', []):
            if feature in class_name or feature in class_file:
                score += 0.4
        
        # Check methods for relevant functionality
        method_names = [m['name'].lower() for m in cls.get('methods', [])]
        req_keywords = characteristics.get('text_content', '').split()
        
        for method_name in method_names:
            for keyword in req_keywords:
                if keyword in method_name:
                    score += 0.1
        
        return min(1.0, score)
    
    def _calculate_endpoint_match_score(self, endpoint: Dict[str, Any], 
                                       characteristics: Dict[str, Any]) -> float:
        """Calculate how well an API endpoint matches requirements"""
        
        if 'api' not in characteristics.get('technical_requirements', []):
            return 0.0
        
        score = 0.4  # Base score for being an API endpoint
        
        path = endpoint.get('path', '').lower()
        method = endpoint.get('method', 'GET').lower()
        
        # Check if path matches feature keywords
        for feature in characteristics.get('features', []):
            if feature in path:
                score += 0.3
        
        # Check method alignment
        if method == 'post' and any(kw in characteristics.get('text_content', '') 
                                   for kw in ['create', 'add', 'submit']):
            score += 0.2
        elif method == 'get' and any(kw in characteristics.get('text_content', '') 
                                    for kw in ['get', 'fetch', 'retrieve', 'list']):
            score += 0.2
        
        return min(1.0, score)
    
    def _rank_reuse_opportunities(self, matches: List[Dict[str, Any]], 
                                 characteristics: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Rank and enhance reuse opportunities"""
        
        # Sort by match score
        sorted_matches = sorted(matches, key=lambda x: x['match_score'], reverse=True)
        
        # Enhance with additional information
        for match in sorted_matches:
            match['estimated_time_saved'] = self._estimate_time_saved(match, characteristics)
            match['adaptation_effort'] = self._estimate_adaptation_effort(match, characteristics)
            match['confidence'] = self._calculate_confidence(match)
        
        return sorted_matches[:10]  # Top 10 opportunities
    
    def _estimate_time_saved(self, match: Dict[str, Any], characteristics: Dict[str, Any]) -> str:
        """Estimate time saved by reusing component"""
        
        complexity = characteristics.get('complexity', 'medium')
        match_score = match['match_score']
        component_type = match['type']
        
        # Base time estimates (in hours)
        base_times = {
            'function': {'low': 2, 'medium': 8, 'high': 16},
            'class': {'low': 4, 'medium': 16, 'high': 40},
            'api_endpoint': {'low': 3, 'medium': 12, 'high': 24}
        }
        
        base_time = base_times.get(component_type, base_times['function'])[complexity]
        time_saved = int(base_time * match_score)
        
        return f"{time_saved} hours"
    
    def _estimate_adaptation_effort(self, match: Dict[str, Any], characteristics: Dict[str, Any]) -> str:
        """Estimate effort required to adapt component"""
        
        match_score = match['match_score']
        
        if match_score > 0.8:
            return 'minimal'
        elif match_score > 0.6:
            return 'low'
        elif match_score > 0.4:
            return 'medium'
        else:
            return 'high'
    
    def _calculate_confidence(self, match: Dict[str, Any]) -> str:
        """Calculate confidence in reuse recommendation"""
        
        match_score = match['match_score']
        
        if match_score > 0.7:
            return 'high'
        elif match_score > 0.5:
            return 'medium'
        else:
            return 'low'
    
    def _create_reuse_plan(self, opportunities: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create actionable reuse plan"""
        
        if not opportunities:
            return {
                'strategy': 'create_new',
                'reason': 'No suitable existing components found',
                'recommendations': [
                    'Design new component with reusability in mind',
                    'Follow established patterns from codebase',
                    'Document well for future reuse'
                ]
            }
        
        top_opportunity = opportunities[0]
        
        plan = {
            'strategy': 'reuse_and_adapt',
            'primary_component': {
                'name': top_opportunity['name'],
                'file': top_opportunity['file'],
                'type': top_opportunity['type'],
                'confidence': top_opportunity['confidence']
            },
            'adaptation_steps': self._generate_adaptation_steps(top_opportunity),
            'fallback_options': opportunities[1:3],  # Next 2 best options
            'estimated_effort': top_opportunity['adaptation_effort'],
            'time_savings': top_opportunity['estimated_time_saved']
        }
        
        return plan
    
    def _generate_adaptation_steps(self, opportunity: Dict[str, Any]) -> List[str]:
        """Generate steps to adapt component for reuse"""
        
        steps = []
        
        reuse_type = opportunity.get('reuse_type', 'adaptation')
        component_type = opportunity['type']
        
        if reuse_type == 'direct':
            steps = [
                f"Import {opportunity['name']} from {opportunity['file']}",
                "Use component directly with minimal configuration",
                "Test integration with your requirements"
            ]
        elif reuse_type == 'adaptation':
            if component_type == 'function':
                steps = [
                    f"Copy {opportunity['name']} from {opportunity['file']}",
                    "Modify function parameters to match your needs",
                    "Update function logic for specific requirements",
                    "Add error handling if missing",
                    "Write tests for adapted function"
                ]
            elif component_type == 'class':
                steps = [
                    f"Import or copy {opportunity['name']} from {opportunity['file']}",
                    "Create subclass or extend existing class",
                    "Override methods that need customization",
                    "Add new methods for additional requirements",
                    "Update constructor if needed"
                ]
        elif reuse_type == 'template':
            steps = [
                f"Use {opportunity['name']} as template",
                "Copy structure and patterns",
                "Adapt to your specific requirements",
                "Follow same naming and organization conventions"
            ]
        
        return steps
    
    def _generate_dry_recommendations(self, opportunities: List[Dict[str, Any]]) -> List[str]:
        """Generate DRY principle recommendations"""
        
        recommendations = []
        
        if opportunities:
            recommendations.extend([
                f"Reuse existing {opportunities[0]['type']} instead of creating new one",
                "Follow DRY principle to reduce code duplication",
                "Document reused components for future reference"
            ])
        else:
            recommendations.extend([
                "Design new component for maximum reusability",
                "Make component generic and configurable",
                "Add to reusable component library"
            ])
        
        # Add general DRY recommendations
        recommendations.extend([
            "Extract common patterns into utility functions",
            "Create shared constants and configuration",
            "Use composition over inheritance where possible"
        ])
        
        return recommendations
    
    # Additional helper methods for enhanced analysis
    
    def _calculate_duplicate_metrics(self, duplicates: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate metrics about code duplication"""
        
        return {
            'duplication_ratio': len(duplicates.get('exact_duplicates', [])) / max(1, len(duplicates.get('similar_functions', []))),
            'most_duplicated_pattern': duplicates.get('similar_functions', [{}])[0].get('signature', 'None') if duplicates.get('similar_functions') else 'None',
            'total_duplicate_files': len(set(d['duplicate']['file'] for d in duplicates.get('exact_duplicates', [])))
        }
    
    def _create_refactoring_plan(self, duplicates: Dict[str, Any]) -> List[Dict[str, str]]:
        """Create plan for refactoring duplicates"""
        
        plan = []
        
        for exact_dup in duplicates.get('exact_duplicates', []):
            plan.append({
                'action': 'remove_duplicate',
                'target': exact_dup['duplicate']['function'],
                'file': exact_dup['duplicate']['file'],
                'replace_with': f"Import from {exact_dup['original']['file']}",
                'priority': 'high'
            })
        
        for similar in duplicates.get('similar_functions', []):
            if similar['count'] >= 3:
                plan.append({
                    'action': 'extract_common_function',
                    'target': similar['signature'],
                    'occurrences': similar['count'],
                    'suggestion': 'Create utility function',
                    'priority': 'medium'
                })
        
        return plan
    
    def _estimate_refactoring_effort(self, duplicates: Dict[str, Any]) -> Dict[str, str]:
        """Estimate effort for refactoring duplicates"""
        
        exact_count = len(duplicates.get('exact_duplicates', []))
        similar_count = len(duplicates.get('similar_functions', []))
        
        return {
            'exact_duplicates': f"{exact_count * 0.5} hours",
            'similar_functions': f"{similar_count * 2} hours",
            'total_estimated': f"{exact_count * 0.5 + similar_count * 2} hours"
        }
    
    def _assess_dependency_health(self, dependencies: Dict[str, Any]) -> Dict[str, str]:
        """Assess health of dependency structure"""
        
        circular_count = len(dependencies.get('circular_dependencies', []))
        metrics = dependencies.get('metrics', {})
        max_fan_out = metrics.get('max_fan_out', 0)
        
        health_score = 'good'
        if circular_count > 0:
            health_score = 'poor'
        elif max_fan_out > 20:
            health_score = 'moderate'
        
        return {
            'overall_health': health_score,
            'circular_deps': 'present' if circular_count > 0 else 'none',
            'coupling_level': 'high' if max_fan_out > 15 else 'moderate' if max_fan_out > 10 else 'low'
        }
    
    def _suggest_dependency_refactoring(self, dependencies: Dict[str, Any]) -> List[str]:
        """Suggest dependency refactoring improvements"""
        
        suggestions = []
        
        if dependencies.get('circular_dependencies'):
            suggestions.append("Break circular dependencies using dependency injection")
        
        metrics = dependencies.get('metrics', {})
        if metrics.get('max_fan_out', 0) > 15:
            suggestions.append("Reduce high coupling by extracting shared utilities")
        
        critical_paths = dependencies.get('critical_paths', [])
        if critical_paths:
            suggestions.append(f"Carefully manage {len(critical_paths)} critical dependency paths")
        
        return suggestions
    
    def _analyze_change_impact(self, dependencies: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze impact of potential changes"""
        
        critical_files = dependencies.get('critical_paths', [])
        
        impact_analysis = {
            'high_impact_files': [cp['file'] for cp in critical_files if cp.get('dependent_count', 0) > 5],
            'change_ripple_risk': 'high' if len(critical_files) > 3 else 'medium' if critical_files else 'low',
            'testing_priority': [cp['file'] for cp in critical_files[:5]]  # Top 5 files that need thorough testing
        }
        
        return impact_analysis
    
    def _analyze_debt_trends(self) -> Dict[str, str]:
        """Analyze technical debt trends"""
        
        # This would analyze historical data
        # For now, return current state indicators
        return {
            'trend': 'stable',
            'risk_level': 'medium',
            'action_needed': 'monitor'
        }
    
    def _calculate_debt_payoff(self, tech_debt: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate payoff of addressing technical debt"""
        
        high_priority_fixes = len([f for f in tech_debt.get('priority_fixes', []) if f.get('severity') in ['critical', 'high']])
        
        return {
            'estimated_payoff_time': f"{high_priority_fixes * 4} hours",
            'maintenance_reduction': f"{high_priority_fixes * 10}%",
            'bug_reduction_estimate': f"{high_priority_fixes * 15}%"
        }
    
    def _create_remediation_roadmap(self, tech_debt: Dict[str, Any]) -> List[Dict[str, str]]:
        """Create roadmap for technical debt remediation"""
        
        roadmap = []
        
        priority_fixes = tech_debt.get('priority_fixes', [])[:5]  # Top 5 fixes
        
        for i, fix in enumerate(priority_fixes):
            roadmap.append({
                'phase': f"Phase {i+1}",
                'focus': fix.get('type', 'quality_improvement'),
                'description': fix.get('description', 'Improve code quality'),
                'estimated_effort': '1-2 weeks',
                'priority': fix.get('severity', 'medium')
            })
        
        return roadmap