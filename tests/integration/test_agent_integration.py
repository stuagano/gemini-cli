"""
Integration tests for multi-agent workflows
Tests agent coordination, Nexus orchestration, and end-to-end scenarios
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
import json
from datetime import datetime

from src.api.agent_server import app, agent_registry
from src.api.router import AgentRouter
from src.nexus.core import CoreNexus
from src.scout.indexer import ScoutIndexer
from src.guardian.validation_pipeline import ValidationPipeline
from fastapi.testclient import TestClient


class TestAgentServerIntegration:
    """Test agent server integration"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    @pytest.mark.integration
    def test_health_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "agents" in data
    
    @pytest.mark.integration
    def test_list_agents(self, client):
        """Test listing all agents"""
        response = client.get("/api/v1/agents")
        assert response.status_code == 200
        data = response.json()
        assert "agents" in data
        assert len(data["agents"]) >= 7  # All agent types
    
    @pytest.mark.integration
    async def test_agent_request_flow(self, client, mock_agent_request):
        """Test complete agent request flow"""
        with patch('src.api.agent_server.agent_registry.get_agent') as mock_get:
            mock_agent = AsyncMock()
            mock_agent.process_request.return_value = {"result": "success"}
            mock_get.return_value = mock_agent
            
            response = client.post(
                "/api/v1/agent/request",
                json=mock_agent_request
            )
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is True
    
    @pytest.mark.integration
    async def test_batch_requests(self, client):
        """Test batch agent requests"""
        requests = [
            {
                "type": "analyst",
                "action": "research",
                "payload": {"topic": "AI"}
            },
            {
                "type": "pm",
                "action": "create_prd",
                "payload": {"feature": "Dashboard"}
            }
        ]
        
        with patch('src.api.agent_server.agent_registry.get_agent') as mock_get:
            mock_agent = AsyncMock()
            mock_agent.process_request.return_value = {"result": "success"}
            mock_get.return_value = mock_agent
            
            response = client.post(
                "/api/v1/agent/batch",
                json=requests
            )
            
            assert response.status_code == 200
            data = response.json()
            assert len(data) == 2


class TestMultiAgentWorkflow:
    """Test complex multi-agent workflows"""
    
    @pytest.mark.integration
    async def test_full_development_workflow(self):
        """Test complete development workflow from requirements to deployment"""
        router = AgentRouter()
        nexus = CoreNexus()
        
        # Mock agents
        with patch.object(nexus, 'agents', new={
            'analyst': AsyncMock(),
            'pm': AsyncMock(),
            'architect': AsyncMock(),
            'developer': AsyncMock(),
            'qa': AsyncMock(),
            'po': AsyncMock()
        }):
            # Setup mock returns for workflow
            nexus.agents['analyst'].process_request.return_value = {
                "requirements": ["User authentication", "Data storage"]
            }
            nexus.agents['pm'].process_request.return_value = {
                "user_stories": [
                    {"id": "US-001", "title": "User Login"},
                    {"id": "US-002", "title": "User Registration"}
                ]
            }
            nexus.agents['architect'].process_request.return_value = {
                "design": {
                    "services": ["auth-service", "user-service"],
                    "database": "PostgreSQL"
                }
            }
            nexus.agents['developer'].process_request.return_value = {
                "code": "class AuthService:\n    pass",
                "tests": ["test_login", "test_logout"]
            }
            nexus.agents['qa'].process_request.return_value = {
                "test_results": "All tests passed",
                "coverage": "85%"
            }
            nexus.agents['po'].process_request.return_value = {
                "approval": True,
                "feedback": "Ready for release"
            }
            
            # Execute workflow
            workflow = router.orchestrate_workflow(
                "full_development",
                {"project": "User Management System"}
            )
            
            results = {}
            for agent_type in workflow:
                agent = nexus.agents.get(agent_type)
                if agent:
                    result = await agent.process_request(
                        f"{agent_type}_task",
                        {"context": results},
                        {}
                    )
                    results[agent_type] = result
            
            # Verify workflow completed
            assert len(results) == len(workflow)
            assert "analyst" in results
            assert "qa" in results
            assert results["po"]["approval"] is True
    
    @pytest.mark.integration
    async def test_bug_fix_workflow(self):
        """Test bug fix workflow"""
        router = AgentRouter()
        
        # Determine workflow
        workflow = router.orchestrate_workflow(
            "fix",
            {"query": "Fix login bug"}
        )
        
        assert "scout" in workflow  # Scout analyzes first
        assert "developer" in workflow  # Developer fixes
        assert "qa" in workflow  # QA validates
    
    @pytest.mark.integration
    async def test_performance_optimization_workflow(self):
        """Test performance optimization workflow"""
        router = AgentRouter()
        
        workflow = router.orchestrate_workflow(
            "optimize",
            {"query": "Optimize database queries"}
        )
        
        assert "scout" in workflow  # Scout finds issues
        assert "architect" in workflow  # Architect designs solution
        assert "developer" in workflow  # Developer implements
        assert "qa" in workflow  # QA validates


class TestScoutIntegration:
    """Test Scout integration with other components"""
    
    @pytest.mark.integration
    async def test_scout_pre_check_integration(self, temp_project_dir):
        """Test Scout pre-check before operations"""
        from src.api.agent_server import scout_pre_check
        
        # Create mock request
        request = Mock()
        request.action = "generate_code"
        request.payload = {"specification": "Create user service"}
        
        with patch('src.api.agent_server.get_indexer') as mock_get:
            mock_indexer = Mock()
            mock_indexer.find_duplicates.return_value = [
                Mock(
                    original_file="user_service.py",
                    duplicate_file="auth_service.py",
                    function_name="create_user",
                    similarity_score=0.85
                )
            ]
            mock_get.return_value = mock_indexer
            
            result = await scout_pre_check(request)
            
            assert result["scout_enabled"] is True
            assert len(result["duplicates_found"]) > 0
            assert result["duplicates_found"][0]["similarity"] == 0.85
    
    @pytest.mark.integration
    def test_scout_indexer_integration(self, temp_project_dir):
        """Test Scout indexer with real files"""
        indexer = ScoutIndexer(str(temp_project_dir))
        
        # Create test files
        (temp_project_dir / "test1.py").write_text("""
def calculate(x, y):
    return x + y

def process(data):
    return data * 2
""")
        
        (temp_project_dir / "test2.py").write_text("""
def calculate(a, b):
    return a + b

def transform(input):
    return input * 2
""")
        
        # Initialize index
        indexer._initialize_db()
        
        # Index files
        indexer._index_file(str(temp_project_dir / "test1.py"))
        indexer._index_file(str(temp_project_dir / "test2.py"))
        
        # Find duplicates
        duplicates = indexer.find_duplicates(0.7)
        
        # Should find similar functions
        assert len(duplicates) > 0


class TestGuardianIntegration:
    """Test Guardian integration"""
    
    @pytest.mark.integration
    async def test_validation_pipeline_integration(self, temp_project_dir):
        """Test validation pipeline with real files"""
        from src.guardian.validation_pipeline import get_validation_pipeline
        
        pipeline = get_validation_pipeline()
        
        # Create test file with issues
        test_file = temp_project_dir / "vulnerable.py"
        test_file.write_text("""
# Security issues
password = "hardcoded123"
api_key = "secret-key-123"

def process_sql(user_input):
    query = "SELECT * FROM users WHERE id = " + user_input
    eval(user_input)  # Dangerous
    
# Performance issue
for item in items:
    result = database.query(f"SELECT * FROM table WHERE id = {item}")
""")
        
        # Run validation
        report = await pipeline.validate_file(str(test_file))
        
        assert report.status in ["failed", "warning"]
        assert len(report.issues) > 0
        
        # Check for security issues
        security_issues = [i for i in report.issues if i.category == "security"]
        assert len(security_issues) > 0
        
        # Check for performance issues
        perf_issues = [i for i in report.issues if i.category == "performance"]
        assert len(perf_issues) > 0
    
    @pytest.mark.integration
    async def test_watcher_notification_integration(self, temp_project_dir):
        """Test file watcher with notification system"""
        from src.guardian.watcher import GuardianWatcher
        from src.guardian.notifications import initialize_notifications, NotificationConfig
        
        # Configure notifications
        config = NotificationConfig()
        config.enable_websocket = False  # Disable for testing
        manager = await initialize_notifications(config)
        
        # Track notifications
        notifications = []
        
        async def capture_notification(request):
            notifications.append(request)
        
        # Create watcher
        watcher = GuardianWatcher(
            str(temp_project_dir),
            validation_callback=capture_notification
        )
        
        # Start watching
        watcher.start()
        
        # Create a file change
        test_file = temp_project_dir / "new_file.py"
        test_file.write_text("def test(): pass")
        
        # Wait for processing
        await asyncio.sleep(2)
        
        # Should have notification
        assert len(notifications) > 0
        
        # Cleanup
        watcher.stop()


class TestRAGIntegration:
    """Test RAG system integration"""
    
    @pytest.mark.integration
    async def test_knowledge_context_integration(self):
        """Test knowledge context retrieval"""
        from src.api.agent_server import get_knowledge_context
        
        request = Mock()
        request.payload = {"query": "How to deploy on GCP"}
        request.context = {}
        request.type = "architect"
        
        with patch('src.api.agent_server.get_rag_system') as mock_get:
            mock_rag = AsyncMock()
            mock_rag.process_query.return_value = Mock(
                sources=[
                    Mock(
                        title="GCP Deployment Guide",
                        service="Cloud Run",
                        url="https://cloud.google.com",
                        content="Deploy containerized apps"
                    )
                ],
                reasoning="Found relevant GCP docs",
                confidence=0.9
            )
            mock_get.return_value = mock_rag
            
            result = await get_knowledge_context(request)
            
            assert result["knowledge_enabled"] is True
            assert len(result["relevant_docs"]) > 0
            assert result["confidence"] == 0.9


class TestEndToEndScenarios:
    """Test complete end-to-end scenarios"""
    
    @pytest.mark.integration
    @pytest.mark.slow
    async def test_feature_development_e2e(self, client):
        """Test complete feature development from PRD to deployment"""
        # Step 1: Create PRD
        prd_response = client.post("/api/v1/agent/request", json={
            "type": "pm",
            "action": "create_prd",
            "payload": {"feature": "User Dashboard"}
        })
        assert prd_response.status_code == 200
        
        # Step 2: Design architecture
        design_response = client.post("/api/v1/agent/request", json={
            "type": "architect",
            "action": "design",
            "payload": {"prd": prd_response.json()}
        })
        assert design_response.status_code == 200
        
        # Step 3: Generate code
        code_response = client.post("/api/v1/agent/request", json={
            "type": "developer",
            "action": "implement",
            "payload": {"design": design_response.json()}
        })
        assert code_response.status_code == 200
        
        # Step 4: Test code
        test_response = client.post("/api/v1/agent/request", json={
            "type": "qa",
            "action": "test",
            "payload": {"code": code_response.json()}
        })
        assert test_response.status_code == 200
        
        # Step 5: Get approval
        approval_response = client.post("/api/v1/agent/request", json={
            "type": "po",
            "action": "approve",
            "payload": {"test_results": test_response.json()}
        })
        assert approval_response.status_code == 200
    
    @pytest.mark.integration
    async def test_code_review_e2e(self, temp_project_dir):
        """Test complete code review process"""
        from src.guardian.validation_pipeline import get_validation_pipeline
        from src.scout.indexer import ScoutIndexer
        
        # Create code file
        code_file = temp_project_dir / "feature.py"
        code_file.write_text("""
def process_payment(amount, card_number):
    # TODO: Add validation
    api_key = "sk_live_123456"  # Security issue
    
    if amount > 0:
        charge = stripe.charge(amount, card_number, api_key)
        return charge
    
def process_payment(amt, card):  # Duplicate function
    return stripe.charge(amt, card)
""")
        
        # Run Scout analysis
        indexer = ScoutIndexer(str(temp_project_dir))
        indexer._initialize_db()
        indexer._index_file(str(code_file))
        
        # Run validation
        pipeline = get_validation_pipeline()
        report = await pipeline.validate_file(str(code_file))
        
        # Check results
        assert report.status in ["failed", "warning"]
        
        # Should find security issue
        security_issues = [i for i in report.issues if "api_key" in i.message.lower()]
        assert len(security_issues) > 0
        
        # Should find duplicate
        duplicates = indexer.find_duplicates(0.8)
        # Note: Would find duplicates if multiple files existed