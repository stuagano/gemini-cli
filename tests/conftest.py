"""
Pytest configuration and fixtures for Gemini Enterprise Architect tests
"""

import pytest
import asyncio
import tempfile
import shutil
from pathlib import Path
from typing import Generator, Any
from unittest.mock import Mock, AsyncMock, patch
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.agents.unified_agent_base import UnifiedAgent, AgentConfig
from src.api.router import AgentRouter
from src.knowledge.rag_system import RAGSystem
from src.scout.indexer import ScoutIndexer
from src.guardian.validation_pipeline import ValidationPipeline
from src.guardian.notifications import NotificationManager

# Configure asyncio for tests
pytest_plugins = ('pytest_asyncio',)

@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture
def temp_project_dir() -> Generator[Path, None, None]:
    """Create a temporary project directory for testing"""
    temp_dir = tempfile.mkdtemp(prefix="gemini_test_")
    project_path = Path(temp_dir)
    
    # Create basic project structure
    (project_path / "src").mkdir()
    (project_path / "tests").mkdir()
    (project_path / ".git").mkdir()
    
    # Create sample files
    (project_path / "src" / "main.py").write_text("""
def hello_world():
    return "Hello, World!"

def add(a, b):
    return a + b
""")
    
    (project_path / "src" / "utils.py").write_text("""
import os

def get_env(key, default=None):
    return os.environ.get(key, default)

def validate_input(data):
    if not data:
        raise ValueError("Data cannot be empty")
    return True
""")
    
    yield project_path
    
    # Cleanup
    shutil.rmtree(temp_dir)

@pytest.fixture
def mock_agent_config() -> AgentConfig:
    """Create a mock agent configuration"""
    return AgentConfig(
        name="TestAgent",
        agent_type="test",
        model="test-model",
        temperature=0.7,
        max_tokens=1000,
        system_prompt="You are a test agent"
    )

@pytest.fixture
def mock_unified_agent(mock_agent_config) -> Mock:
    """Create a mock unified agent"""
    agent = Mock(spec=UnifiedAgent)
    agent.config = mock_agent_config
    agent.name = mock_agent_config.name
    agent.process_request = AsyncMock(return_value={"status": "success"})
    agent.stream_response = AsyncMock()
    agent.get_capabilities = Mock(return_value=["test", "mock"])
    return agent

@pytest.fixture
def mock_knowledge_base() -> Mock:
    """Create a mock knowledge base"""
    kb = Mock()
    kb.search = AsyncMock(return_value=[
        {"title": "Test Doc", "content": "Test content", "score": 0.9}
    ])
    kb.add_document = AsyncMock(return_value=True)
    kb.update_embeddings = AsyncMock()
    return kb

@pytest.fixture
def mock_scout_indexer(temp_project_dir) -> Mock:
    """Create a mock Scout indexer"""
    indexer = Mock(spec=ScoutIndexer)
    indexer.project_root = temp_project_dir
    indexer.find_duplicates = Mock(return_value=[])
    indexer.get_file_info = Mock(return_value={
        "file_path": "test.py",
        "functions": ["func1", "func2"],
        "classes": ["Class1"],
        "complexity": 5
    })
    indexer.full_index = Mock()
    indexer.get_stats = Mock(return_value={
        "files_indexed": 10,
        "functions_found": 25,
        "classes_found": 5
    })
    return indexer

@pytest.fixture
def mock_validation_pipeline() -> Mock:
    """Create a mock validation pipeline"""
    pipeline = Mock(spec=ValidationPipeline)
    pipeline.validate_file = AsyncMock(return_value={
        "status": "passed",
        "issues": [],
        "metrics": {"total_lines": 100}
    })
    return pipeline

@pytest.fixture
def mock_notification_manager() -> Mock:
    """Create a mock notification manager"""
    manager = Mock(spec=NotificationManager)
    manager.notify = AsyncMock()
    manager.get_history = Mock(return_value=[])
    return manager

@pytest.fixture
def mock_agent_router() -> AgentRouter:
    """Create an agent router instance"""
    return AgentRouter()

@pytest.fixture
def sample_code_files() -> dict:
    """Sample code files for testing"""
    return {
        "python_good.py": """
# Good Python code
def calculate_sum(numbers):
    \"\"\"Calculate sum of numbers\"\"\"
    return sum(numbers)

class Calculator:
    def add(self, a, b):
        return a + b
""",
        "python_bad.py": """
# Bad Python code with issues
def process_data(data):
    eval(data)  # Security issue
    password = "hardcoded123"  # Security issue
    
    # N+1 query problem
    for item in items:
        db.query(f"SELECT * FROM table WHERE id = {item}")  # SQL injection
""",
        "javascript_good.js": """
// Good JavaScript code
function greet(name) {
    return \`Hello, \${name}!\`;
}

class User {
    constructor(name) {
        this.name = name;
    }
}
""",
        "javascript_bad.js": """
// Bad JavaScript code
function dangerous() {
    eval(userInput);  // Security issue
    document.write(data);  // XSS vulnerability
    
    // Memory leak
    element.addEventListener('click', handler);
    // Missing removeEventListener
}
"""
    }

@pytest.fixture
def mock_fastapi_client():
    """Create a mock FastAPI test client"""
    from fastapi.testclient import TestClient
    from src.api.agent_server import app
    
    return TestClient(app)

@pytest.fixture
async def mock_websocket_client():
    """Create a mock WebSocket client"""
    import websockets
    
    async def connect():
        uri = "ws://localhost:8000/ws/agent/stream"
        return await websockets.connect(uri)
    
    return connect

@pytest.fixture
def mock_agent_request():
    """Create a mock agent request"""
    return {
        "type": "developer",
        "action": "generate_code",
        "payload": {
            "specification": "Create a function to calculate fibonacci"
        },
        "context": {},
        "priority": "normal",
        "timeout": 30
    }

@pytest.fixture
def mock_validation_context():
    """Create a mock validation context"""
    return {
        "file_path": "test.py",
        "content": "def test(): pass",
        "language": "python",
        "previous_content": None
    }

# Test data fixtures
@pytest.fixture
def sample_prd():
    """Sample Product Requirements Document"""
    return """
# Product Requirements Document
## Feature: User Authentication
### Requirements:
- Users can register with email and password
- Users can login with credentials
- Password reset functionality
- Session management
"""

@pytest.fixture
def sample_architecture():
    """Sample architecture specification"""
    return """
# Architecture Design
## Services:
- API Gateway (Cloud Endpoints)
- Auth Service (Cloud Run)
- User Database (Cloud SQL)
## Scaling:
- Horizontal scaling for API
- Read replicas for database
"""

@pytest.fixture
def sample_test_cases():
    """Sample test cases"""
    return [
        {
            "name": "test_user_registration",
            "type": "unit",
            "description": "Test user registration flow"
        },
        {
            "name": "test_login",
            "type": "integration",
            "description": "Test login with valid credentials"
        }
    ]

# Helper fixtures
@pytest.fixture
def capture_logs():
    """Capture log output for testing"""
    import logging
    from io import StringIO
    
    log_capture = StringIO()
    handler = logging.StreamHandler(log_capture)
    handler.setLevel(logging.DEBUG)
    
    logger = logging.getLogger()
    logger.addHandler(handler)
    
    yield log_capture
    
    logger.removeHandler(handler)

@pytest.fixture
def mock_env_vars():
    """Mock environment variables"""
    env_vars = {
        "BMAD_PROJECT_ROOT": "/test/project",
        "BMAD_LOG_LEVEL": "DEBUG",
        "OPENAI_API_KEY": "test-key",
        "GCP_PROJECT": "test-project"
    }
    
    with patch.dict(os.environ, env_vars):
        yield env_vars

@pytest.fixture
def async_timeout():
    """Timeout for async tests"""
    return 5.0  # 5 seconds

# Markers for test categorization
def pytest_configure(config):
    """Register custom markers"""
    config.addinivalue_line(
        "markers", "unit: Unit tests"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests"
    )
    config.addinivalue_line(
        "markers", "slow: Slow tests"
    )
    config.addinivalue_line(
        "markers", "requires_api: Tests that require API access"
    )