"""
Enhanced Developer Agent
BMAD Developer enhanced with Guardian functionality and continuous validation
Combines code generation with real-time testing and breaking change prevention
"""

import ast
import re
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path
import tempfile
import os

from ..unified_agent_base import UnifiedAgent, AgentConfig

# Import killer demo functionality to integrate
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
try:
    from killer_demo.scaling_detector import ScalingIssueDetector
except ImportError:
    ScalingIssueDetector = None


class GuardianSystem:
    """Continuous validation and breaking change prevention"""
    
    def __init__(self):
        self.baseline_tests = {}
        self.dependency_map = {}
        self.critical_paths = set()
        
    def establish_baseline(self, codebase_path: str) -> Dict[str, Any]:
        """Establish baseline for regression detection"""
        baseline = {
            'test_results': self._run_existing_tests(codebase_path),
            'api_contracts': self._extract_api_contracts(codebase_path),
            'performance_metrics': self._measure_performance(codebase_path),
            'dependency_graph': self._build_dependency_graph(codebase_path),
            'timestamp': datetime.now().isoformat()
        }
        
        self.baseline_tests = baseline
        return baseline
    
    def validate_changes(self, changes: Dict[str, Any], 
                        codebase_path: str) -> Dict[str, Any]:
        """Validate changes against baseline"""
        validation = {
            'breaking_changes': [],
            'test_failures': [],
            'performance_regressions': [],
            'api_contract_violations': [],
            'dependency_violations': [],
            'overall_safe': True
        }
        
        # Check for breaking changes
        breaking_changes = self._detect_breaking_changes(changes)
        if breaking_changes:
            validation['breaking_changes'] = breaking_changes
            validation['overall_safe'] = False
        
        # Run tests with changes
        test_results = self._run_tests_with_changes(changes, codebase_path)
        if test_results.get('failures'):
            validation['test_failures'] = test_results['failures']
            validation['overall_safe'] = False
        
        # Check API contracts
        contract_violations = self._check_api_contracts(changes)
        if contract_violations:
            validation['api_contract_violations'] = contract_violations
            validation['overall_safe'] = False
        
        # Check performance
        perf_issues = self._check_performance_regression(changes)
        if perf_issues:
            validation['performance_regressions'] = perf_issues
            validation['overall_safe'] = False
        
        return validation
    
    def _run_existing_tests(self, path: str) -> Dict[str, Any]:
        """Run existing test suite"""
        try:
            # Try to detect test framework
            if Path(path + '/pytest.ini').exists() or Path(path + '/setup.cfg').exists():
                return self._run_pytest(path)
            elif Path(path + '/package.json').exists():
                return self._run_jest(path)
            else:
                return {'status': 'no_tests_detected', 'results': []}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _run_pytest(self, path: str) -> Dict[str, Any]:
        """Run pytest"""
        try:
            result = subprocess.run(
                ['python', '-m', 'pytest', '--json-report', '--json-report-file=/tmp/test_results.json'],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            return {
                'status': 'success' if result.returncode == 0 else 'failures',
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        except subprocess.TimeoutExpired:
            return {'status': 'timeout', 'error': 'Tests took longer than 5 minutes'}
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _run_jest(self, path: str) -> Dict[str, Any]:
        """Run Jest tests"""
        try:
            result = subprocess.run(
                ['npm', 'test', '--', '--json', '--outputFile=/tmp/test_results.json'],
                cwd=path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            return {
                'status': 'success' if result.returncode == 0 else 'failures',
                'return_code': result.returncode,
                'stdout': result.stdout,
                'stderr': result.stderr
            }
        except Exception as e:
            return {'status': 'error', 'error': str(e)}
    
    def _extract_api_contracts(self, path: str) -> List[Dict[str, Any]]:
        """Extract API contracts from codebase"""
        contracts = []
        
        # Look for FastAPI/Flask routes
        for py_file in Path(path).rglob('*.py'):
            try:
                with open(py_file, 'r') as f:
                    content = f.read()
                    
                # FastAPI routes
                fastapi_routes = re.findall(r'@app\.(get|post|put|delete|patch)\("([^"]+)".*?\)\s*def\s+(\w+)', content, re.DOTALL)
                for method, route, func_name in fastapi_routes:
                    contracts.append({
                        'type': 'fastapi_route',
                        'method': method.upper(),
                        'path': route,
                        'function': func_name,
                        'file': str(py_file)
                    })
                    
                # Flask routes
                flask_routes = re.findall(r'@app\.route\("([^"]+)".*?methods=\[([^\]]+)\].*?\)\s*def\s+(\w+)', content, re.DOTALL)
                for route, methods, func_name in flask_routes:
                    contracts.append({
                        'type': 'flask_route',
                        'path': route,
                        'methods': methods.replace('"', '').replace("'", '').split(','),
                        'function': func_name,
                        'file': str(py_file)
                    })
                    
            except Exception:
                continue
                
        return contracts
    
    def _measure_performance(self, path: str) -> Dict[str, Any]:
        """Measure baseline performance metrics"""
        # This would integrate with actual performance testing
        # For now, return simulated metrics
        return {
            'response_time_p50': 45,  # ms
            'response_time_p99': 120,  # ms
            'throughput': 500,  # requests/sec
            'memory_usage': 256,  # MB
            'cpu_usage': 15  # %
        }
    
    def _build_dependency_graph(self, path: str) -> Dict[str, List[str]]:
        """Build dependency graph"""
        graph = {}
        
        # Analyze Python imports
        for py_file in Path(path).rglob('*.py'):
            try:
                with open(py_file, 'r') as f:
                    tree = ast.parse(f.read())
                    
                file_deps = []
                for node in ast.walk(tree):
                    if isinstance(node, ast.Import):
                        for alias in node.names:
                            file_deps.append(alias.name)
                    elif isinstance(node, ast.ImportFrom):
                        if node.module:
                            file_deps.append(node.module)
                
                graph[str(py_file)] = file_deps
                
            except Exception:
                continue
                
        return graph
    
    def _detect_breaking_changes(self, changes: Dict[str, Any]) -> List[Dict[str, str]]:
        """Detect breaking changes in code"""
        breaking_changes = []
        
        code = changes.get('code', '')
        
        # Check for removed functions
        if 'def ' in code and 'REMOVED' in changes.get('change_type', ''):
            breaking_changes.append({
                'type': 'function_removal',
                'description': 'Function removed without deprecation',
                'impact': 'High - Will break dependent code',
                'suggestion': 'Add deprecation warning first'
            })
        
        # Check for changed API signatures
        if '@app.' in code:
            # Check for route signature changes
            old_signature = changes.get('old_signature')
            new_signature = changes.get('new_signature')
            
            if old_signature and new_signature and old_signature != new_signature:
                breaking_changes.append({
                    'type': 'api_signature_change',
                    'description': 'API endpoint signature changed',
                    'impact': 'High - Will break API clients',
                    'suggestion': 'Version the API or maintain backward compatibility'
                })
        
        # Check for database schema changes
        if any(keyword in code.lower() for keyword in ['drop table', 'alter table', 'drop column']):
            breaking_changes.append({
                'type': 'schema_change',
                'description': 'Destructive database schema change detected',
                'impact': 'Critical - Data loss possible',
                'suggestion': 'Use migrations with rollback capability'
            })
        
        return breaking_changes
    
    def _run_tests_with_changes(self, changes: Dict[str, Any], 
                               path: str) -> Dict[str, Any]:
        """Run tests with proposed changes"""
        # Create temporary directory with changes
        with tempfile.TemporaryDirectory() as temp_dir:
            # Copy codebase to temp directory
            subprocess.run(['cp', '-r', path, temp_dir], check=True)
            
            # Apply changes
            temp_path = Path(temp_dir) / Path(path).name
            self._apply_changes(changes, str(temp_path))
            
            # Run tests
            return self._run_existing_tests(str(temp_path))
    
    def _apply_changes(self, changes: Dict[str, Any], path: str):
        """Apply changes to temporary codebase"""
        if 'file_path' in changes and 'code' in changes:
            file_path = Path(path) / changes['file_path']
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            with open(file_path, 'w') as f:
                f.write(changes['code'])
    
    def _check_api_contracts(self, changes: Dict[str, Any]) -> List[Dict[str, str]]:
        """Check for API contract violations"""
        violations = []
        
        code = changes.get('code', '')
        
        # Check for removed endpoints
        if '@app.' in code and 'REMOVED' in changes.get('change_type', ''):
            violations.append({
                'type': 'endpoint_removal',
                'description': 'API endpoint removed',
                'contract': 'REST API contract',
                'suggestion': 'Deprecate endpoint first, then remove in next version'
            })
        
        # Check for response format changes
        if 'return' in code and changes.get('old_response_format'):
            violations.append({
                'type': 'response_format_change',
                'description': 'API response format changed',
                'contract': 'Response schema contract',
                'suggestion': 'Add new fields while keeping old ones for compatibility'
            })
        
        return violations
    
    def _check_performance_regression(self, changes: Dict[str, Any]) -> List[Dict[str, str]]:
        """Check for performance regressions"""
        regressions = []
        
        code = changes.get('code', '')
        
        # Check for O(n²) patterns
        if 'for ' in code and code.count('for ') > 1:
            # Simple heuristic for nested loops
            regressions.append({
                'type': 'algorithmic_complexity',
                'description': 'Potential O(n²) algorithm detected',
                'impact': 'Performance will degrade with data size',
                'suggestion': 'Consider using hash maps or more efficient algorithms'
            })
        
        # Check for missing caching
        if 'db.query' in code and 'cache' not in code.lower():
            regressions.append({
                'type': 'missing_cache',
                'description': 'Database query without caching',
                'impact': 'Increased latency and database load',
                'suggestion': 'Add caching layer for frequently accessed data'
            })
        
        # Check for synchronous operations in async code
        if 'async def' in code and 'requests.get' in code:
            regressions.append({
                'type': 'blocking_operation',
                'description': 'Synchronous HTTP call in async function',
                'impact': 'Blocks event loop, reduces concurrency',
                'suggestion': 'Use aiohttp or httpx for async HTTP calls'
            })
        
        return regressions


class CodeGenerator:
    """Intelligent code generation with best practices"""
    
    def __init__(self, standards_enforcer, service_advisor):
        self.standards_enforcer = standards_enforcer
        self.service_advisor = service_advisor
        
    def generate_code(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code following best practices"""
        
        code_type = requirements.get('type', 'general')
        
        if code_type == 'api_endpoint':
            return self._generate_api_endpoint(requirements)
        elif code_type == 'data_model':
            return self._generate_data_model(requirements)
        elif code_type == 'service_class':
            return self._generate_service_class(requirements)
        elif code_type == 'test':
            return self._generate_test(requirements)
        else:
            return self._generate_general_code(requirements)
    
    def _generate_api_endpoint(self, req: Dict[str, Any]) -> Dict[str, Any]:
        """Generate FastAPI endpoint with best practices"""
        
        endpoint_name = req.get('name', 'example')
        method = req.get('method', 'GET').lower()
        path = req.get('path', f'/{endpoint_name}')
        
        # Generate code with pagination, validation, error handling
        code = f'''from fastapi import FastAPI, HTTPException, Depends, Query
from pydantic import BaseModel
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class {endpoint_name.title()}Response(BaseModel):
    """Response model for {endpoint_name} endpoint"""
    data: List[dict]
    total: int
    cursor: Optional[str] = None
    has_more: bool = False

@app.{method}("{path}")
async def {endpoint_name}(
    limit: int = Query(default=100, le=1000, ge=1),
    cursor: Optional[str] = Query(default=None),
    # Add authentication dependency
    current_user = Depends(get_current_user)
) -> {endpoint_name.title()}Response:
    """
    {req.get('description', f'Get {endpoint_name} data')}
    
    - **limit**: Number of items to return (max 1000)
    - **cursor**: Pagination cursor for next page
    """
    try:
        # Input validation
        if limit <= 0:
            raise HTTPException(status_code=400, detail="Limit must be positive")
        
        # Build query with pagination
        query = "SELECT * FROM {endpoint_name}"
        params = []
        
        if cursor:
            query += " WHERE id > %s"
            params.append(cursor)
            
        query += " ORDER BY id LIMIT %s"
        params.append(limit + 1)  # Fetch one extra to check if more exists
        
        # Execute query (with connection pooling)
        results = await db.fetch_all(query, params)
        
        # Check if more data exists
        has_more = len(results) > limit
        if has_more:
            results = results[:limit]
        
        # Generate next cursor
        next_cursor = results[-1]['id'] if results and has_more else None
        
        # Log for monitoring
        logger.info(f"{{endpoint_name}} endpoint called by {{current_user.id}}, returned {{len(results)}} items")
        
        return {endpoint_name.title()}Response(
            data=results,
            total=len(results),
            cursor=next_cursor,
            has_more=has_more
        )
        
    except Exception as e:
        logger.error(f"Error in {endpoint_name} endpoint: {{e}}")
        raise HTTPException(status_code=500, detail="Internal server error")
'''
        
        return {
            'code': code,
            'file_path': f'app/api/{endpoint_name}.py',
            'tests': self._generate_endpoint_tests(endpoint_name, method, path),
            'best_practices_applied': [
                'Pagination with cursor-based approach',
                'Input validation with Pydantic',
                'Error handling with proper HTTP status codes',
                'Authentication dependency',
                'Logging for observability',
                'Response model for consistent API shape',
                'SQL injection prevention with parameterized queries'
            ]
        }
    
    def _generate_data_model(self, req: Dict[str, Any]) -> Dict[str, Any]:
        """Generate Pydantic data model"""
        
        model_name = req.get('name', 'ExampleModel')
        fields = req.get('fields', [])
        
        code = f'''from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class {model_name}(BaseModel):
    """
    {req.get('description', f'{model_name} data model')}
    """
'''
        
        # Add fields
        for field in fields:
            field_name = field.get('name', 'field')
            field_type = field.get('type', 'str')
            required = field.get('required', True)
            description = field.get('description', '')
            
            if not required:
                field_type = f"Optional[{field_type}] = None"
            
            if description:
                code += f'    {field_name}: {field_type} = Field(..., description="{description}")\n'
            else:
                code += f'    {field_name}: {field_type}\n'
        
        # Add common fields
        code += '''    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: Optional[datetime] = None
    
    class Config:
        """Pydantic configuration"""
        # Enable ORM mode for SQLAlchemy integration
        from_attributes = True
        # Use enum values in JSON serialization
        use_enum_values = True
        # Validate assignment
        validate_assignment = True
        # Example values for OpenAPI docs
        json_schema_extra = {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "created_at": "2023-01-01T00:00:00Z"
            }
        }
    
    @validator('updated_at', pre=True, always=True)
    def set_updated_at(cls, v):
        """Auto-set updated_at on modification"""
        return datetime.utcnow() if v is None else v
'''
        
        return {
            'code': code,
            'file_path': f'app/models/{model_name.lower()}.py',
            'best_practices_applied': [
                'Pydantic validation',
                'Type hints for all fields',
                'Automatic timestamp management',
                'ORM mode for database integration',
                'Example values for API documentation',
                'Custom validators for business logic'
            ]
        }
    
    def _generate_service_class(self, req: Dict[str, Any]) -> Dict[str, Any]:
        """Generate service class with dependency injection"""
        
        service_name = req.get('name', 'ExampleService')
        
        code = f'''from typing import List, Optional, Dict, Any
import logging
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.models import {service_name.replace('Service', '')}
from app.core.cache import cache_manager
from app.core.metrics import metrics

logger = logging.getLogger(__name__)

class {service_name}:
    """
    {req.get('description', f'{service_name} business logic')}
    """
    
    def __init__(self, db: Session):
        self.db = db
        
    async def get_items(
        self, 
        limit: int = 100, 
        cursor: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Get items with caching and metrics"""
        
        # Generate cache key
        cache_key = f"{service_name.lower()}:items:{{limit}}:{{cursor}}:{{hash(str(filters))}}"
        
        # Try cache first
        cached_result = await cache_manager.get(cache_key)
        if cached_result:
            metrics.increment(f"{service_name.lower()}.cache.hit")
            return cached_result
            
        metrics.increment(f"{service_name.lower()}.cache.miss")
        
        try:
            # Build query
            query = self.db.query({service_name.replace('Service', '')})
            
            # Apply filters
            if filters:
                for key, value in filters.items():
                    if hasattr({service_name.replace('Service', '')}, key):
                        query = query.filter(getattr({service_name.replace('Service', '')}, key) == value)
            
            # Apply pagination
            if cursor:
                query = query.filter({service_name.replace('Service', '')}.id > cursor)
                
            query = query.order_by({service_name.replace('Service', '')}.id).limit(limit + 1)
            
            # Execute query
            results = query.all()
            
            # Process results
            has_more = len(results) > limit
            if has_more:
                results = results[:limit]
                
            next_cursor = results[-1].id if results and has_more else None
            
            result = {{
                'data': [item.dict() for item in results],
                'cursor': next_cursor,
                'has_more': has_more,
                'total': len(results)
            }}
            
            # Cache result
            await cache_manager.set(cache_key, result, ttl=300)  # 5 minute TTL
            
            # Record metrics
            metrics.histogram(f"{service_name.lower()}.query.duration", 
                             tags={'filter_count': len(filters or [])})
            
            return result
            
        except Exception as e:
            logger.error(f"Error in {{service_name}}.get_items: {{e}}")
            metrics.increment(f"{service_name.lower()}.errors")
            raise HTTPException(status_code=500, detail="Failed to retrieve items")
    
    async def create_item(self, item_data: Dict[str, Any]) -> {service_name.replace('Service', '')}:
        """Create new item with validation"""
        
        try:
            # Validate business rules
            await self._validate_create(item_data)
            
            # Create item
            new_item = {service_name.replace('Service', '')}(**item_data)
            self.db.add(new_item)
            self.db.commit()
            self.db.refresh(new_item)
            
            # Invalidate related cache
            await cache_manager.delete_pattern(f"{service_name.lower()}:*")
            
            # Record metrics
            metrics.increment(f"{service_name.lower()}.created")
            
            logger.info(f"Created new {{service_name.lower()}} with id: {{new_item.id}}")
            
            return new_item
            
        except ValueError as e:
            logger.warning(f"Validation error in create_item: {{e}}")
            raise HTTPException(status_code=400, detail=str(e))
        except Exception as e:
            logger.error(f"Error creating {{service_name.lower()}}: {{e}}")
            self.db.rollback()
            metrics.increment(f"{service_name.lower()}.create.errors")
            raise HTTPException(status_code=500, detail="Failed to create item")
    
    async def _validate_create(self, item_data: Dict[str, Any]):
        """Validate business rules for creation"""
        
        # Example validation
        if not item_data.get('name'):
            raise ValueError("Name is required")
            
        # Check for duplicates
        existing = self.db.query({service_name.replace('Service', '')}).filter(
            {service_name.replace('Service', '')}.name == item_data['name']
        ).first()
        
        if existing:
            raise ValueError(f"Item with name '{{item_data['name']}}' already exists")
'''
        
        return {
            'code': code,
            'file_path': f'app/services/{service_name.lower()}.py',
            'best_practices_applied': [
                'Dependency injection with database session',
                'Caching layer for performance',
                'Metrics and observability',
                'Business logic validation',
                'Proper error handling and logging',
                'Transaction management',
                'Cache invalidation on updates'
            ]
        }
    
    def _generate_test(self, req: Dict[str, Any]) -> Dict[str, Any]:
        """Generate comprehensive test suite"""
        
        test_subject = req.get('subject', 'example_function')
        test_type = req.get('test_type', 'unit')
        
        if test_type == 'unit':
            return self._generate_unit_tests(test_subject, req)
        elif test_type == 'integration':
            return self._generate_integration_tests(test_subject, req)
        else:
            return self._generate_e2e_tests(test_subject, req)
    
    def _generate_unit_tests(self, subject: str, req: Dict[str, Any]) -> Dict[str, Any]:
        """Generate unit tests"""
        
        code = f'''import pytest
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from app.services.{subject} import {subject.title()}Service
from app.models.{subject} import {subject.title()}

class Test{subject.title()}Service:
    """Test suite for {subject.title()}Service"""
    
    @pytest.fixture
    def mock_db(self):
        """Mock database session"""
        return Mock()
    
    @pytest.fixture
    def service(self, mock_db):
        """Service instance with mocked dependencies"""
        return {subject.title()}Service(db=mock_db)
    
    @pytest.mark.asyncio
    async def test_get_items_success(self, service, mock_db):
        """Test successful item retrieval"""
        # Arrange
        mock_items = [
            {subject.title()}(id="1", name="Test Item 1"),
            {subject.title()}(id="2", name="Test Item 2")
        ]
        mock_db.query.return_value.filter.return_value.order_by.return_value.limit.return_value.all.return_value = mock_items
        
        with patch('app.core.cache.cache_manager.get', return_value=None):
            with patch('app.core.cache.cache_manager.set') as mock_cache_set:
                # Act
                result = await service.get_items(limit=10)
                
                # Assert
                assert result['total'] == 2
                assert len(result['data']) == 2
                assert result['has_more'] is False
                mock_cache_set.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_get_items_with_cache(self, service):
        """Test cached item retrieval"""
        # Arrange
        cached_data = {{'data': [], 'total': 0, 'has_more': False}}
        
        with patch('app.core.cache.cache_manager.get', return_value=cached_data):
            # Act
            result = await service.get_items()
            
            # Assert
            assert result == cached_data
    
    @pytest.mark.asyncio
    async def test_create_item_success(self, service, mock_db):
        """Test successful item creation"""
        # Arrange
        item_data = {{'name': 'New Item', 'description': 'Test description'}}
        mock_item = {subject.title()}(id="new-id", **item_data)
        mock_db.add = Mock()
        mock_db.commit = Mock()
        mock_db.refresh = Mock()
        
        with patch('app.core.cache.cache_manager.delete_pattern') as mock_cache_delete:
            with patch.object(service, '_validate_create', return_value=None):
                with patch('{subject.title()}', return_value=mock_item):
                    # Act
                    result = await service.create_item(item_data)
                    
                    # Assert
                    assert result == mock_item
                    mock_db.add.assert_called_once()
                    mock_db.commit.assert_called_once()
                    mock_cache_delete.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_item_validation_error(self, service):
        """Test item creation with validation error"""
        # Arrange
        invalid_data = {{'description': 'Missing name'}}
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.create_item(invalid_data)
        
        assert exc_info.value.status_code == 400
        assert "Name is required" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_create_item_duplicate_name(self, service, mock_db):
        """Test item creation with duplicate name"""
        # Arrange
        item_data = {{'name': 'Existing Item'}}
        existing_item = {subject.title()}(id="existing", name="Existing Item")
        mock_db.query.return_value.filter.return_value.first.return_value = existing_item
        
        # Act & Assert
        with pytest.raises(HTTPException) as exc_info:
            await service.create_item(item_data)
        
        assert exc_info.value.status_code == 400
        assert "already exists" in str(exc_info.value.detail)

@pytest.mark.integration
class Test{subject.title()}Integration:
    """Integration tests for {subject.title()}"""
    
    @pytest.fixture
    def client(self):
        """Test client"""
        from app.main import app
        return TestClient(app)
    
    def test_endpoint_integration(self, client):
        """Test API endpoint integration"""
        # Test GET endpoint
        response = client.get("/{subject}?limit=10")
        assert response.status_code == 200
        
        data = response.json()
        assert 'data' in data
        assert 'total' in data
        assert 'has_more' in data
    
    def test_endpoint_pagination(self, client):
        """Test pagination functionality"""
        # Get first page
        response = client.get("/{subject}?limit=5")
        first_page = response.json()
        
        if first_page['has_more']:
            # Get second page
            cursor = first_page['cursor']
            response = client.get(f"/{subject}?limit=5&cursor={{cursor}}")
            second_page = response.json()
            
            # Verify no overlap
            first_ids = [item['id'] for item in first_page['data']]
            second_ids = [item['id'] for item in second_page['data']]
            assert not set(first_ids).intersection(set(second_ids))
'''
        
        return {
            'code': code,
            'file_path': f'tests/test_{subject}_service.py',
            'best_practices_applied': [
                'Comprehensive test coverage',
                'Mock external dependencies',
                'Test both success and failure cases',
                'Integration tests for end-to-end flows',
                'Async test support',
                'Clear test structure and naming',
                'Fixtures for reusable test data'
            ]
        }
    
    def _generate_general_code(self, req: Dict[str, Any]) -> Dict[str, Any]:
        """Generate general purpose code"""
        
        return {
            'code': '# Generated code placeholder',
            'file_path': 'app/generated.py',
            'best_practices_applied': ['To be implemented']
        }
    
    def _generate_endpoint_tests(self, name: str, method: str, path: str) -> str:
        """Generate tests for API endpoint"""
        
        return f'''import pytest
from fastapi.testclient import TestClient

def test_{name}_endpoint_success(client: TestClient):
    """Test {name} endpoint success case"""
    response = client.{method}("{path}?limit=10")
    assert response.status_code == 200
    
    data = response.json()
    assert 'data' in data
    assert 'total' in data

def test_{name}_endpoint_pagination(client: TestClient):
    """Test {name} endpoint pagination"""
    response = client.{method}("{path}?limit=1")
    data = response.json()
    
    if data['has_more']:
        cursor_response = client.{method}("{path}?limit=1&cursor={{data['cursor']}}")
        assert cursor_response.status_code == 200

def test_{name}_endpoint_validation(client: TestClient):
    """Test {name} endpoint input validation"""
    response = client.{method}("{path}?limit=0")
    assert response.status_code == 400
'''


class EnhancedDeveloper(UnifiedAgent):
    """
    BMAD Developer enhanced with Guardian functionality
    Dev - Senior Developer focused on code generation and continuous validation
    """
    
    def __init__(self, developer_level: str = "intermediate"):
        config = self._load_bmad_config()
        super().__init__(config, developer_level)
        
        # Enhanced capabilities
        self.guardian = GuardianSystem()
        self.code_generator = CodeGenerator(self.standards_enforcer, self.service_advisor)
        
        # Development state
        self.current_task = None
        self.validation_history = []
        
    def _load_bmad_config(self) -> AgentConfig:
        """Load BMAD developer configuration"""
        return AgentConfig(
            id="developer",
            name="Dev",
            title="Senior Developer",
            icon="💻",
            when_to_use="Use for code implementation, testing, debugging, continuous validation",
            persona={
                'role': 'Senior Full-Stack Developer & Code Guardian',
                'style': 'Pragmatic, detail-oriented, quality-focused, test-driven',
                'identity': 'Expert developer ensuring code quality and system reliability',
                'focus': 'Clean code, testing, performance, security, maintainability',
                'core_principles': [
                    'Test-driven development',
                    'Continuous validation',
                    'Security by design',
                    'Performance-first mindset',
                    'Breaking change prevention'
                ]
            },
            commands=[
                {'name': 'implement-story', 'description': 'Implement user story with tests'},
                {'name': 'generate-code', 'description': 'Generate code following best practices'},
                {'name': 'validate-changes', 'description': 'Validate changes for breaking issues'},
                {'name': 'refactor-code', 'description': 'Refactor code while maintaining functionality'},
                {'name': 'debug-issue', 'description': 'Debug and fix code issues'}
            ],
            dependencies={
                'templates': ['code-tmpl.py', 'test-tmpl.py'],
                'data': ['coding-standards.md', 'best-practices.md'],
                'checklists': ['code-review-checklist.md']
            }
        )
    
    def execute_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute developer-specific tasks"""
        
        if task == "implement_story":
            return self.implement_story(context)
        elif task == "generate_code":
            return self.generate_code(context)
        elif task == "validate_changes":
            return self.validate_changes(context)
        elif task == "refactor_code":
            return self.refactor_code(context)
        elif task == "debug_issue":
            return self.debug_issue(context)
        else:
            return {'error': f'Unknown task: {task}'}
    
    def implement_story(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Implement user story with TDD approach"""
        
        story = context.get('story', {})
        reuse_map = context.get('reuse_map', {})
        
        implementation = {
            'story_id': story.get('id'),
            'implementation_plan': self._create_implementation_plan(story),
            'reuse_analysis': self._analyze_reuse_opportunities(story, reuse_map),
            'generated_code': {},
            'tests': {},
            'validation_results': {},
            'deployment_ready': False
        }
        
        # Step 1: Generate tests first (TDD)
        tests = self._generate_story_tests(story)
        implementation['tests'] = tests
        
        # Step 2: Generate implementation
        code = self._generate_story_implementation(story, reuse_map)
        implementation['generated_code'] = code
        
        # Step 3: Validate against Guardian
        validation = self.guardian.validate_changes(
            {'code': code.get('main_code', ''), 'story': story},
            context.get('codebase_path', '.')
        )
        implementation['validation_results'] = validation
        
        # Step 4: Check for scaling issues (Killer demo!)
        scaling_issues = self._detect_scaling_issues(code)
        if scaling_issues:
            implementation['scaling_issues'] = scaling_issues
            self._teach_scaling_prevention(scaling_issues)
        
        # Step 5: Standards compliance
        violations = self.standards_enforcer.check({
            'type': 'story_implementation',
            'code': code.get('main_code', ''),
            'story': story
        })
        
        if violations:
            implementation['standards_violations'] = violations
            self.teach_and_correct(violations, context)
            
        # Step 6: Mark as deployment ready if all checks pass
        implementation['deployment_ready'] = (
            validation['overall_safe'] and 
            not scaling_issues and 
            not violations
        )
        
        # Record metrics
        self._record_implementation_metrics(implementation)
        
        return implementation
    
    def generate_code(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Generate code following best practices"""
        
        requirements = context.get('requirements', {})
        
        # Generate code using intelligent generator
        generated = self.code_generator.generate_code(requirements)
        
        # Validate generated code
        validation = self.guardian.validate_changes(
            {'code': generated['code']},
            context.get('codebase_path', '.')
        )
        
        # Check for scaling issues
        scaling_issues = self._detect_scaling_issues({'main_code': generated['code']})
        
        # Teach about best practices applied
        self.teaching_engine.teach(
            "Code Generation Best Practices",
            {
                'what': f"Generated {requirements.get('type', 'code')} with best practices",
                'why': "Following patterns prevents future issues",
                'how': f"Applied: {', '.join(generated.get('best_practices_applied', []))}",
                'example': "Pagination prevents memory overflow at scale"
            }
        )
        
        return {
            **generated,
            'validation_results': validation,
            'scaling_issues': scaling_issues,
            'production_ready': validation['overall_safe'] and not scaling_issues
        }
    
    def validate_changes(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate changes for breaking issues and regressions"""
        
        changes = context.get('changes', {})
        codebase_path = context.get('codebase_path', '.')
        
        # Establish baseline if not exists
        if not self.guardian.baseline_tests:
            baseline = self.guardian.establish_baseline(codebase_path)
            self.teaching_engine.teach(
                "Guardian Baseline Established",
                {
                    'what': "Established testing and performance baseline",
                    'why': "Baseline enables detection of regressions",
                    'how': f"Captured {len(baseline.get('api_contracts', []))} API contracts",
                    'example': "Now can detect breaking API changes automatically"
                }
            )
        
        # Validate changes
        validation = self.guardian.validate_changes(changes, codebase_path)
        
        # Add to validation history
        self.validation_history.append({
            'timestamp': datetime.now().isoformat(),
            'changes': changes,
            'validation': validation
        })
        
        # Teach about issues found
        if not validation['overall_safe']:
            self._teach_validation_issues(validation)
        
        return validation
    
    def refactor_code(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Refactor code while maintaining functionality"""
        
        target_code = context.get('code', '')
        refactor_goals = context.get('goals', ['improve_readability'])
        
        refactor_result = {
            'original_code': target_code,
            'refactored_code': '',
            'improvements': [],
            'validation': {},
            'safe_to_deploy': False
        }
        
        # Apply refactoring patterns
        refactored = self._apply_refactoring_patterns(target_code, refactor_goals)
        refactor_result['refactored_code'] = refactored['code']
        refactor_result['improvements'] = refactored['improvements']
        
        # Validate refactored code
        validation = self.guardian.validate_changes(
            {'code': refactored['code'], 'old_code': target_code},
            context.get('codebase_path', '.')
        )
        refactor_result['validation'] = validation
        refactor_result['safe_to_deploy'] = validation['overall_safe']
        
        # Teach about refactoring
        self.teaching_engine.teach(
            "Safe Refactoring",
            {
                'what': f"Refactored code with {len(refactored['improvements'])} improvements",
                'why': "Refactoring improves maintainability without changing behavior",
                'how': "Used Guardian system to validate no breaking changes",
                'example': f"Applied: {refactored['improvements'][0] if refactored['improvements'] else 'None'}"
            }
        )
        
        return refactor_result
    
    def debug_issue(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Debug and fix code issues"""
        
        issue = context.get('issue', {})
        code = context.get('code', '')
        
        debug_result = {
            'issue_analysis': self._analyze_issue(issue, code),
            'root_cause': '',
            'fix_suggestions': [],
            'implemented_fix': '',
            'validation': {}
        }
        
        # Analyze the issue
        analysis = debug_result['issue_analysis']
        debug_result['root_cause'] = analysis.get('root_cause', 'Unknown')
        debug_result['fix_suggestions'] = analysis.get('suggestions', [])
        
        # Implement fix if possible
        if analysis.get('auto_fixable'):
            fix = self._implement_fix(issue, code, analysis)
            debug_result['implemented_fix'] = fix['code']
            
            # Validate fix
            validation = self.guardian.validate_changes(
                {'code': fix['code'], 'old_code': code},
                context.get('codebase_path', '.')
            )
            debug_result['validation'] = validation
        
        return debug_result
    
    def _create_implementation_plan(self, story: Dict[str, Any]) -> List[Dict[str, str]]:
        """Create implementation plan for story"""
        
        return [
            {
                'step': 1,
                'description': 'Write failing tests (TDD)',
                'estimated_time': '30 minutes',
                'deliverable': 'Test suite'
            },
            {
                'step': 2,
                'description': 'Implement core functionality',
                'estimated_time': '2 hours',
                'deliverable': 'Working code'
            },
            {
                'step': 3,
                'description': 'Add error handling and validation',
                'estimated_time': '1 hour',
                'deliverable': 'Robust code'
            },
            {
                'step': 4,
                'description': 'Optimize for performance and scale',
                'estimated_time': '1 hour',
                'deliverable': 'Production-ready code'
            },
            {
                'step': 5,
                'description': 'Guardian validation and testing',
                'estimated_time': '30 minutes',
                'deliverable': 'Validated implementation'
            }
        ]
    
    def _analyze_reuse_opportunities(self, story: Dict[str, Any], 
                                   reuse_map: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze opportunities to reuse existing code"""
        
        opportunities = []
        story_text = str(story).lower()
        
        # Check for reusable components
        for component, usage in reuse_map.items():
            if any(keyword in story_text for keyword in component.lower().split('_')):
                opportunities.append({
                    'component': component,
                    'usage_count': len(usage),
                    'reuse_potential': 'high' if len(usage) > 3 else 'medium',
                    'integration_effort': 'low'
                })
        
        # Teach about DRY principle
        if opportunities:
            self.teaching_engine.teach(
                "DRY Principle Application",
                {
                    'what': f"Found {len(opportunities)} reusable components",
                    'why': "Reusing code reduces bugs and maintenance",
                    'how': f"Integrate {opportunities[0]['component']} instead of recreating",
                    'example': "LoginForm component used in 5 places already"
                }
            )
        
        return {
            'opportunities': opportunities,
            'reuse_score': len(opportunities) / max(len(reuse_map), 1) * 100,
            'recommendations': [
                f"Reuse {opp['component']} to save development time"
                for opp in opportunities[:3]
            ]
        }
    
    def _generate_story_tests(self, story: Dict[str, Any]) -> Dict[str, str]:
        """Generate tests for user story"""
        
        story_title = story.get('title', 'story')
        acceptance_criteria = story.get('acceptance_criteria', [])
        
        # Generate different types of tests
        tests = {}
        
        # Unit tests
        tests['unit_tests'] = self.code_generator._generate_unit_tests(
            story_title.lower().replace(' ', '_'), 
            {'story': story}
        )['code']
        
        # Integration tests if API involved
        if 'api' in story_title.lower():
            tests['integration_tests'] = f'''
import pytest
from fastapi.testclient import TestClient

def test_{story_title.lower().replace(" ", "_")}_integration(client: TestClient):
    """Integration test for {story_title}"""
    # Test based on acceptance criteria
    {"".join([f"    # {criterion}" for criterion in acceptance_criteria[:3]])}
    
    response = client.get("/test-endpoint")
    assert response.status_code == 200
'''
        
        return tests
    
    def _generate_story_implementation(self, story: Dict[str, Any], 
                                     reuse_map: Dict[str, Any]) -> Dict[str, str]:
        """Generate implementation for user story"""
        
        story_type = self._identify_story_type(story)
        
        if story_type == 'api_endpoint':
            return self._generate_api_story(story)
        elif story_type == 'data_processing':
            return self._generate_data_processing_story(story)
        elif story_type == 'ui_component':
            return self._generate_ui_story(story)
        else:
            return self._generate_generic_story(story)
    
    def _identify_story_type(self, story: Dict[str, Any]) -> str:
        """Identify the type of user story"""
        
        story_text = str(story).lower()
        
        if any(keyword in story_text for keyword in ['api', 'endpoint', 'rest']):
            return 'api_endpoint'
        elif any(keyword in story_text for keyword in ['process', 'transform', 'data']):
            return 'data_processing'
        elif any(keyword in story_text for keyword in ['ui', 'component', 'interface']):
            return 'ui_component'
        else:
            return 'generic'
    
    def _generate_api_story(self, story: Dict[str, Any]) -> Dict[str, str]:
        """Generate API endpoint implementation"""
        
        requirements = {
            'type': 'api_endpoint',
            'name': story.get('title', 'example').lower().replace(' ', '_'),
            'description': story.get('user_story', ''),
            'method': 'GET'  # Default, would be inferred from story
        }
        
        generated = self.code_generator.generate_code(requirements)
        
        return {
            'main_code': generated['code'],
            'file_path': generated['file_path'],
            'tests': generated.get('tests', ''),
            'type': 'api_endpoint'
        }
    
    def _generate_data_processing_story(self, story: Dict[str, Any]) -> Dict[str, str]:
        """Generate data processing implementation"""
        
        code = f'''import logging
from typing import List, Dict, Any
import asyncio
from app.core.metrics import metrics

logger = logging.getLogger(__name__)

async def process_data(input_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Process data for: {story.get('title', 'story')}
    {story.get('user_story', '')}
    """
    
    try:
        # Process in batches to handle large datasets
        batch_size = 100
        processed_data = []
        
        for i in range(0, len(input_data), batch_size):
            batch = input_data[i:i + batch_size]
            
            # Process batch
            batch_result = await _process_batch(batch)
            processed_data.extend(batch_result)
            
            # Record metrics
            metrics.histogram('data.processing.batch_size', len(batch))
            
        logger.info(f"Processed {{len(input_data)}} records")
        return processed_data
        
    except Exception as e:
        logger.error(f"Error processing data: {{e}}")
        metrics.increment('data.processing.errors')
        raise

async def _process_batch(batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Process a single batch of data"""
    
    # Add your processing logic here
    processed_batch = []
    
    for item in batch:
        # Transform item
        processed_item = {{
            **item,
            'processed_at': datetime.utcnow().isoformat(),
            'status': 'processed'
        }}
        processed_batch.append(processed_item)
    
    return processed_batch
'''
        
        return {
            'main_code': code,
            'file_path': f'app/processors/{story.get("title", "processor").lower().replace(" ", "_")}.py',
            'type': 'data_processing'
        }
    
    def _generate_ui_story(self, story: Dict[str, Any]) -> Dict[str, str]:
        """Generate UI component implementation"""
        
        component_name = story.get('title', 'Component').replace(' ', '')
        
        code = f'''import React, {{ useState, useEffect }} from 'react';
import {{ Alert, Button, Card }} from '@/components/ui';
import {{ useMetrics }} from '@/hooks/useMetrics';

interface {component_name}Props {{
    // Add props based on story requirements
    data?: any[];
    onAction?: (item: any) => void;
}}

export const {component_name}: React.FC<{component_name}Props> = ({{
    data = [],
    onAction
}}) => {{
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const {{ trackEvent }} = useMetrics();
    
    useEffect(() => {{
        // Track component render
        trackEvent('{component_name.lower()}_rendered');
    }}, []);
    
    const handleAction = async (item: any) => {{
        try {{
            setLoading(true);
            setError(null);
            
            await onAction?.(item);
            trackEvent('{component_name.lower()}_action_success');
            
        }} catch (err) {{
            setError('Action failed. Please try again.');
            trackEvent('{component_name.lower()}_action_error');
        }} finally {{
            setLoading(false);
        }}
    }};
    
    if (error) {{
        return <Alert variant="destructive">{{error}}</Alert>;
    }}
    
    return (
        <Card className="p-4">
            <h2 className="text-lg font-semibold mb-4">
                {story.get('title', 'Component')}
            </h2>
            
            {{data.length === 0 ? (
                <p className="text-gray-500">No data available</p>
            ) : (
                <div className="space-y-2">
                    {{data.map((item, index) => (
                        <div key={{index}} className="flex justify-between items-center p-2 border rounded">
                            <span>{{item.name || `Item ${{index + 1}}`}}</span>
                            <Button
                                onClick={{() => handleAction(item)}}
                                disabled={{loading}}
                                size="sm"
                            >
                                {{loading ? 'Loading...' : 'Action'}}
                            </Button>
                        </div>
                    ))}}
                </div>
            )}}
        </Card>
    );
}};

export default {component_name};
'''
        
        return {
            'main_code': code,
            'file_path': f'src/components/{component_name}.tsx',
            'type': 'ui_component'
        }
    
    def _generate_generic_story(self, story: Dict[str, Any]) -> Dict[str, str]:
        """Generate generic implementation"""
        
        return {
            'main_code': f'# Implementation for: {story.get("title", "Story")}\n# TODO: Implement based on acceptance criteria',
            'file_path': 'app/implementation.py',
            'type': 'generic'
        }
    
    def _detect_scaling_issues(self, code: Dict[str, str]) -> List[Dict[str, str]]:
        """Detect scaling issues in generated code - THE KILLER DEMO"""
        
        issues = []
        main_code = code.get('main_code', '')
        
        # Check for unbounded queries (the classic scaling killer)
        if self._has_unbounded_query(main_code):
            issues.append({
                'severity': 'CRITICAL',
                'type': 'unbounded_query',
                'title': '🚨 SCALING DISASTER DETECTED',
                'description': 'This query will cause memory overflow at 10K+ users',
                'current_impact': 'Works fine with 100 test users',
                'scale_impact': 'Server crashes with OutOfMemory at 10K users',
                'cost_impact': '$100K+ in downtime and emergency fixes',
                'fix': 'Add LIMIT and pagination',
                'example': self._get_pagination_fix_example()
            })
        
        # Check for N+1 query problems
        if self._has_n_plus_one_query(main_code):
            issues.append({
                'severity': 'HIGH',
                'type': 'n_plus_one_query',
                'title': 'N+1 Query Problem Detected',
                'description': 'This will make 1000+ database calls for 1000 users',
                'current_impact': '10ms response time with 10 users',
                'scale_impact': '30+ second response time with 1000 users',
                'fix': 'Use JOIN or batch loading',
                'example': 'Use SELECT with JOIN instead of loop with individual queries'
            })
        
        # Check for missing caching
        if self._missing_caching(main_code):
            issues.append({
                'severity': 'MEDIUM',
                'type': 'missing_cache',
                'title': 'Missing Caching Layer',
                'description': 'Database will be overwhelmed without caching',
                'current_impact': 'Extra database load',
                'scale_impact': 'Database becomes bottleneck at scale',
                'fix': 'Add Redis caching with appropriate TTL',
                'example': 'Cache frequently accessed data for 5 minutes'
            })
        
        # Check for synchronous operations in async code
        if self._has_sync_in_async(main_code):
            issues.append({
                'severity': 'HIGH',
                'type': 'blocking_operation',
                'title': 'Blocking Operation in Async Code',
                'description': 'Synchronous operations will block the event loop',
                'current_impact': 'Reduced concurrency',
                'scale_impact': 'Server becomes unresponsive under load',
                'fix': 'Use async/await for all I/O operations',
                'example': 'Use aiohttp instead of requests.get()'
            })
        
        return issues
    
    def _has_unbounded_query(self, code: str) -> bool:
        """Check for unbounded database queries"""
        
        # Look for SQL SELECT without LIMIT
        patterns = [
            r'SELECT\s+.*FROM\s+\w+(?!\s+.*LIMIT)',
            r'db\.query\([^)]*\)(?!\s*\.limit)',
            r'\.all\(\)(?!\s*\[:)',  # .all() without slicing
            r'SELECT \* FROM \w+(?!\s+LIMIT)'
        ]
        
        code_upper = code.upper()
        for pattern in patterns:
            if re.search(pattern, code_upper, re.IGNORECASE):
                return True
                
        return False
    
    def _has_n_plus_one_query(self, code: str) -> bool:
        """Check for N+1 query problems"""
        
        # Look for queries inside loops
        patterns = [
            r'for\s+\w+\s+in\s+.*:\s*.*db\.query',
            r'for\s+.*:\s*.*SELECT.*FROM',
            r'\[.*db\.query.*for.*in.*\]'  # List comprehension with queries
        ]
        
        for pattern in patterns:
            if re.search(pattern, code, re.IGNORECASE | re.DOTALL):
                return True
                
        return False
    
    def _missing_caching(self, code: str) -> bool:
        """Check for missing caching"""
        
        # Has database queries but no caching
        has_db_query = bool(re.search(r'db\.query|SELECT.*FROM', code, re.IGNORECASE))
        has_cache = bool(re.search(r'cache|redis|memcache', code, re.IGNORECASE))
        
        return has_db_query and not has_cache
    
    def _has_sync_in_async(self, code: str) -> bool:
        """Check for synchronous operations in async functions"""
        
        # Has async function with synchronous HTTP calls
        has_async_func = bool(re.search(r'async\s+def', code))
        has_sync_http = bool(re.search(r'requests\.(get|post|put|delete)', code))
        
        return has_async_func and has_sync_http
    
    def _get_pagination_fix_example(self) -> str:
        """Get example of pagination fix"""
        return '''
# ❌ BEFORE (fails at scale):
@app.get("/users")
def get_users():
    return db.query("SELECT * FROM users")  # 💥 OOM at 10K users

# ✅ AFTER (handles millions):
@app.get("/users")
def get_users(cursor: str = None, limit: int = 100):
    query = "SELECT * FROM users"
    if cursor:
        query += f" WHERE id > '{cursor}'"
    query += f" ORDER BY id LIMIT {limit}"
    
    results = db.query(query)
    return {
        'data': results,
        'cursor': results[-1]['id'] if len(results) == limit else None
    }
'''
    
    def _teach_scaling_prevention(self, issues: List[Dict[str, str]]):
        """Teach about scaling issues and prevention"""
        
        for issue in issues:
            if issue['severity'] == 'CRITICAL':
                self.teaching_engine.teach(
                    issue['title'],
                    {
                        'what': issue['description'],
                        'why': f"{issue['current_impact']} → {issue['scale_impact']}",
                        'how': issue['fix'],
                        'example': issue.get('example', ''),
                        'cost_impact': issue.get('cost_impact', 'High cost of failure')
                    }
                )
    
    def _record_implementation_metrics(self, implementation: Dict[str, Any]):
        """Record metrics about implementation"""
        
        # This would integrate with actual metrics system
        metrics_data = {
            'story_implemented': 1,
            'tests_generated': len(implementation.get('tests', {})),
            'scaling_issues_detected': len(implementation.get('scaling_issues', [])),
            'standards_violations': len(implementation.get('standards_violations', [])),
            'deployment_ready': 1 if implementation.get('deployment_ready') else 0
        }
        
        # In production, would send to monitoring system
        # metrics.record(metrics_data)
    
    def _teach_validation_issues(self, validation: Dict[str, Any]):
        """Teach about validation issues found"""
        
        if validation.get('breaking_changes'):
            self.teaching_engine.teach(
                "Breaking Changes Detected",
                {
                    'what': f"Found {len(validation['breaking_changes'])} breaking changes",
                    'why': "Breaking changes cause production issues",
                    'how': "Use versioning and backward compatibility",
                    'example': validation['breaking_changes'][0]['description']
                }
            )
        
        if validation.get('performance_regressions'):
            self.teaching_engine.teach(
                "Performance Regression Alert",
                {
                    'what': "Code changes will slow down the system",
                    'why': "Performance regressions hurt user experience",
                    'how': "Optimize algorithms and add caching",
                    'example': validation['performance_regressions'][0]['description']
                }
            )
    
    def _apply_refactoring_patterns(self, code: str, goals: List[str]) -> Dict[str, Any]:
        """Apply refactoring patterns"""
        
        refactored_code = code
        improvements = []
        
        # Extract method refactoring
        if 'improve_readability' in goals:
            if len(code.split('\n')) > 20:  # Long function
                improvements.append('Suggested extracting smaller methods from long function')
        
        # Remove code duplication
        if 'reduce_duplication' in goals:
            # Simple duplicate detection
            lines = code.split('\n')
            seen_lines = set()
            for line in lines:
                if line.strip() and line in seen_lines:
                    improvements.append('Detected duplicate code that could be extracted')
                seen_lines.add(line)
        
        return {
            'code': refactored_code,
            'improvements': improvements
        }
    
    def _analyze_issue(self, issue: Dict[str, Any], code: str) -> Dict[str, Any]:
        """Analyze code issue"""
        
        issue_type = issue.get('type', 'unknown')
        
        analysis = {
            'issue_type': issue_type,
            'root_cause': 'To be analyzed',
            'suggestions': [],
            'auto_fixable': False
        }
        
        if issue_type == 'performance':
            analysis['root_cause'] = 'Inefficient algorithm or missing optimization'
            analysis['suggestions'] = [
                'Add caching layer',
                'Optimize database queries',
                'Use asynchronous processing'
            ]
            
        elif issue_type == 'error':
            analysis['root_cause'] = 'Missing error handling or validation'
            analysis['suggestions'] = [
                'Add try-catch blocks',
                'Validate input parameters',
                'Add logging for debugging'
            ]
            analysis['auto_fixable'] = True
            
        return analysis
    
    def _implement_fix(self, issue: Dict[str, Any], code: str, 
                      analysis: Dict[str, Any]) -> Dict[str, str]:
        """Implement automatic fix for issue"""
        
        fixed_code = code
        
        # Simple error handling fix
        if issue.get('type') == 'error' and 'try:' not in code:
            # Wrap main logic in try-catch
            lines = code.split('\n')
            indented_lines = ['    ' + line for line in lines[1:]]  # Skip function def
            
            fixed_code = f'''{lines[0]}
    try:
{"".join(indented_lines)}
    except Exception as e:
        logger.error(f"Error in function: {{e}}")
        raise HTTPException(status_code=500, detail="Internal server error")
'''
        
        return {'code': fixed_code}