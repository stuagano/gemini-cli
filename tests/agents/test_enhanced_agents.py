"""
Unit tests for Enhanced Agents
Tests all agent implementations for correct behavior
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime

from src.agents.enhanced.analyst import EnhancedAnalyst
from src.agents.enhanced.pm import EnhancedPM
from src.agents.enhanced.architect import EnhancedArchitect
from src.agents.enhanced.developer import EnhancedDeveloper
from src.agents.enhanced.qa import EnhancedQA
from src.agents.enhanced.scout import EnhancedScout
from src.agents.enhanced.po import EnhancedPO
from src.agents.unified_agent_base import AgentConfig


class TestEnhancedAnalyst:
    """Test Enhanced Analyst agent"""
    
    @pytest.fixture
    def analyst(self, mock_agent_config):
        """Create analyst instance"""
        config = mock_agent_config
        config.agent_type = "analyst"
        return EnhancedAnalyst(config)
    
    @pytest.mark.unit
    async def test_market_research(self, analyst):
        """Test market research capability"""
        with patch.object(analyst, '_execute_llm_task', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "market_size": "$10B",
                "growth_rate": "15%",
                "competitors": ["Company A", "Company B"]
            }
            
            result = await analyst.process_request(
                "market_research",
                {"topic": "AI development tools"},
                {}
            )
            
            assert result is not None
            assert "market_size" in result
            mock_llm.assert_called_once()
    
    @pytest.mark.unit
    async def test_competitive_analysis(self, analyst):
        """Test competitive analysis"""
        with patch.object(analyst, '_execute_llm_task', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "competitors": [
                    {"name": "Competitor 1", "strengths": ["Feature A"]},
                    {"name": "Competitor 2", "strengths": ["Feature B"]}
                ],
                "market_position": "Emerging"
            }
            
            result = await analyst.process_request(
                "competitive_analysis",
                {"market": "DevTools"},
                {}
            )
            
            assert "competitors" in result
            assert len(result["competitors"]) == 2
    
    @pytest.mark.unit
    async def test_requirements_gathering(self, analyst):
        """Test requirements gathering"""
        with patch.object(analyst, '_execute_llm_task', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "functional_requirements": ["REQ-001", "REQ-002"],
                "non_functional_requirements": ["PERF-001", "SEC-001"],
                "constraints": ["Budget: $100k"]
            }
            
            result = await analyst.process_request(
                "gather_requirements",
                {"project": "New Feature"},
                {}
            )
            
            assert "functional_requirements" in result
            assert "non_functional_requirements" in result


class TestEnhancedPM:
    """Test Enhanced PM agent"""
    
    @pytest.fixture
    def pm(self, mock_agent_config):
        """Create PM instance"""
        config = mock_agent_config
        config.agent_type = "pm"
        return EnhancedPM(config)
    
    @pytest.mark.unit
    async def test_create_prd(self, pm):
        """Test PRD creation"""
        with patch.object(pm, '_execute_llm_task', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "title": "Feature X PRD",
                "objectives": ["Increase user engagement"],
                "requirements": ["Must support mobile"],
                "success_metrics": ["DAU increase by 20%"]
            }
            
            result = await pm.process_request(
                "create_prd",
                {"feature": "User Dashboard"},
                {}
            )
            
            assert "title" in result
            assert "objectives" in result
            assert "requirements" in result
    
    @pytest.mark.unit
    async def test_create_user_story(self, pm):
        """Test user story creation"""
        with patch.object(pm, '_execute_llm_task', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "title": "User Login",
                "story": "As a user, I want to login...",
                "acceptance_criteria": ["User can enter credentials"],
                "story_points": 3
            }
            
            result = await pm.process_request(
                "create_user_story",
                {"feature": "Authentication"},
                {}
            )
            
            assert "story" in result
            assert "acceptance_criteria" in result
    
    @pytest.mark.unit
    async def test_roadmap_planning(self, pm):
        """Test roadmap planning"""
        with patch.object(pm, '_execute_llm_task', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "quarters": [
                    {"Q1": ["Feature A", "Feature B"]},
                    {"Q2": ["Feature C"]}
                ],
                "milestones": ["MVP Launch", "v2.0"]
            }
            
            result = await pm.process_request(
                "plan_roadmap",
                {"timeframe": "6 months"},
                {}
            )
            
            assert "quarters" in result
            assert "milestones" in result


class TestEnhancedArchitect:
    """Test Enhanced Architect agent"""
    
    @pytest.fixture
    def architect(self, mock_agent_config):
        """Create Architect instance"""
        config = mock_agent_config
        config.agent_type = "architect"
        return EnhancedArchitect(config)
    
    @pytest.mark.unit
    async def test_design_system(self, architect):
        """Test system design"""
        with patch.object(architect, '_execute_llm_task', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "architecture": "Microservices",
                "services": ["Auth Service", "API Gateway", "User Service"],
                "database": "PostgreSQL",
                "scaling_strategy": "Horizontal"
            }
            
            result = await architect.process_request(
                "design_system",
                {"requirements": "E-commerce platform"},
                {}
            )
            
            assert "architecture" in result
            assert "services" in result
            assert len(result["services"]) > 0
    
    @pytest.mark.unit
    async def test_select_technologies(self, architect):
        """Test technology selection"""
        with patch.object(architect, '_execute_llm_task', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "frontend": "React",
                "backend": "FastAPI",
                "database": "PostgreSQL",
                "infrastructure": "GCP",
                "rationale": {"React": "Component reusability"}
            }
            
            result = await architect.process_request(
                "select_technologies",
                {"project_type": "Web Application"},
                {}
            )
            
            assert "frontend" in result
            assert "backend" in result
            assert "rationale" in result
    
    @pytest.mark.unit
    async def test_scalability_analysis(self, architect):
        """Test scalability analysis"""
        with patch.object(architect, '_execute_llm_task', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "bottlenecks": ["Database connections"],
                "recommendations": ["Add connection pooling"],
                "scaling_limits": {"users": 10000, "rps": 1000}
            }
            
            result = await architect.process_request(
                "analyze_scalability",
                {"system": "Current Architecture"},
                {}
            )
            
            assert "bottlenecks" in result
            assert "recommendations" in result


class TestEnhancedDeveloper:
    """Test Enhanced Developer agent"""
    
    @pytest.fixture
    def developer(self, mock_agent_config):
        """Create Developer instance"""
        config = mock_agent_config
        config.agent_type = "developer"
        return EnhancedDeveloper(config)
    
    @pytest.mark.unit
    async def test_generate_code(self, developer):
        """Test code generation"""
        with patch.object(developer, '_execute_llm_task', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "code": "def hello_world():\n    return 'Hello, World!'",
                "language": "python",
                "dependencies": [],
                "tests": ["test_hello_world"]
            }
            
            result = await developer.process_request(
                "generate_code",
                {"specification": "Hello world function"},
                {}
            )
            
            assert "code" in result
            assert "language" in result
            assert "def hello_world" in result["code"]
    
    @pytest.mark.unit
    async def test_debug_code(self, developer):
        """Test code debugging"""
        with patch.object(developer, '_execute_llm_task', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "issues": ["Variable undefined"],
                "fixes": ["Define variable before use"],
                "fixed_code": "x = 0\nprint(x)"
            }
            
            result = await developer.process_request(
                "debug",
                {"code": "print(x)", "error": "NameError"},
                {}
            )
            
            assert "issues" in result
            assert "fixes" in result
            assert "fixed_code" in result
    
    @pytest.mark.unit
    async def test_refactor_code(self, developer):
        """Test code refactoring"""
        with patch.object(developer, '_execute_llm_task', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "refactored_code": "def add(a: int, b: int) -> int:\n    return a + b",
                "improvements": ["Added type hints"],
                "complexity_reduction": 2
            }
            
            result = await developer.process_request(
                "refactor",
                {"code": "def add(a, b): return a+b"},
                {}
            )
            
            assert "refactored_code" in result
            assert "improvements" in result


class TestEnhancedQA:
    """Test Enhanced QA agent"""
    
    @pytest.fixture
    def qa(self, mock_agent_config):
        """Create QA instance"""
        config = mock_agent_config
        config.agent_type = "qa"
        return EnhancedQA(config)
    
    @pytest.mark.unit
    async def test_create_test_plan(self, qa):
        """Test test plan creation"""
        with patch.object(qa, '_execute_llm_task', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "test_cases": [
                    {"id": "TC001", "name": "Login Test"},
                    {"id": "TC002", "name": "Logout Test"}
                ],
                "coverage": "80%",
                "test_types": ["unit", "integration", "e2e"]
            }
            
            result = await qa.process_request(
                "create_test_plan",
                {"feature": "Authentication"},
                {}
            )
            
            assert "test_cases" in result
            assert len(result["test_cases"]) > 0
            assert "coverage" in result
    
    @pytest.mark.unit
    async def test_validate_code(self, qa):
        """Test code validation"""
        with patch.object(qa, '_execute_llm_task', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "validation_status": "passed",
                "issues": [],
                "suggestions": ["Add more edge case tests"]
            }
            
            result = await qa.process_request(
                "validate",
                {"code": "def add(a, b): return a + b"},
                {}
            )
            
            assert "validation_status" in result
            assert result["validation_status"] == "passed"
    
    @pytest.mark.unit
    async def test_security_review(self, qa):
        """Test security review"""
        with patch.object(qa, '_execute_llm_task', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "vulnerabilities": [],
                "security_score": 95,
                "recommendations": ["Enable HTTPS"]
            }
            
            result = await qa.process_request(
                "security_review",
                {"code": "Sample code"},
                {}
            )
            
            assert "vulnerabilities" in result
            assert "security_score" in result


class TestEnhancedScout:
    """Test Enhanced Scout agent"""
    
    @pytest.fixture
    def scout(self, mock_agent_config, temp_project_dir):
        """Create Scout instance"""
        config = mock_agent_config
        config.agent_type = "scout"
        with patch('src.agents.enhanced.scout.ScoutIndexer'):
            scout = EnhancedScout(config)
            scout.project_root = temp_project_dir
            return scout
    
    @pytest.mark.unit
    async def test_analyze_codebase(self, scout):
        """Test codebase analysis"""
        with patch.object(scout, '_execute_llm_task', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "total_files": 100,
                "languages": {"python": 60, "javascript": 40},
                "complexity": "medium",
                "tech_debt": ["Old dependencies"]
            }
            
            result = await scout.process_request(
                "analyze_codebase",
                {},
                {}
            )
            
            assert "total_files" in result
            assert "languages" in result
    
    @pytest.mark.unit
    async def test_find_duplicates(self, scout):
        """Test duplicate detection"""
        with patch.object(scout, 'find_duplicates') as mock_find:
            mock_find.return_value = [
                {
                    "file1": "a.py",
                    "file2": "b.py",
                    "similarity": 0.95,
                    "lines": 50
                }
            ]
            
            result = await scout.process_request(
                "find_duplicates",
                {"threshold": 0.8},
                {}
            )
            
            assert len(result) > 0
            assert result[0]["similarity"] > 0.8
    
    @pytest.mark.unit
    async def test_analyze_dependencies(self, scout):
        """Test dependency analysis"""
        with patch.object(scout, '_execute_llm_task', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "dependencies": ["fastapi", "pytest"],
                "outdated": ["old-package"],
                "vulnerabilities": [],
                "dependency_graph": {}
            }
            
            result = await scout.process_request(
                "analyze_dependencies",
                {},
                {}
            )
            
            assert "dependencies" in result
            assert "outdated" in result


class TestEnhancedPO:
    """Test Enhanced PO agent"""
    
    @pytest.fixture
    def po(self, mock_agent_config):
        """Create PO instance"""
        config = mock_agent_config
        config.agent_type = "po"
        return EnhancedPO(config)
    
    @pytest.mark.unit
    async def test_prioritize_backlog(self, po):
        """Test backlog prioritization"""
        with patch.object(po, '_execute_llm_task', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "prioritized_items": [
                    {"id": "STORY-1", "priority": 1, "value": "high"},
                    {"id": "STORY-2", "priority": 2, "value": "medium"}
                ],
                "rationale": "Business value and dependencies"
            }
            
            result = await po.process_request(
                "prioritize",
                {"backlog": ["STORY-1", "STORY-2"]},
                {}
            )
            
            assert "prioritized_items" in result
            assert len(result["prioritized_items"]) == 2
            assert result["prioritized_items"][0]["priority"] == 1
    
    @pytest.mark.unit
    async def test_calculate_roi(self, po):
        """Test ROI calculation"""
        with patch.object(po, '_execute_llm_task', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "roi": 250,
                "payback_period": "6 months",
                "benefits": ["Increased efficiency"],
                "costs": {"development": 50000}
            }
            
            result = await po.process_request(
                "calculate_roi",
                {"feature": "Automation"},
                {}
            )
            
            assert "roi" in result
            assert "payback_period" in result
            assert result["roi"] > 0
    
    @pytest.mark.unit
    async def test_stakeholder_communication(self, po):
        """Test stakeholder communication"""
        with patch.object(po, '_execute_llm_task', new_callable=AsyncMock) as mock_llm:
            mock_llm.return_value = {
                "communication_plan": {
                    "weekly": ["Status updates"],
                    "monthly": ["Progress review"]
                },
                "stakeholders": ["Product team", "Engineering"],
                "key_messages": ["On track for Q2 delivery"]
            }
            
            result = await po.process_request(
                "stakeholder_communication",
                {"project": "New Feature"},
                {}
            )
            
            assert "communication_plan" in result
            assert "stakeholders" in result


# Integration tests
class TestAgentIntegration:
    """Test agent integrations"""
    
    @pytest.mark.integration
    async def test_multi_agent_workflow(self, mock_agent_config):
        """Test workflow across multiple agents"""
        # Create agents
        analyst = EnhancedAnalyst(mock_agent_config)
        pm = EnhancedPM(mock_agent_config)
        architect = EnhancedArchitect(mock_agent_config)
        
        with patch.object(analyst, '_execute_llm_task', new_callable=AsyncMock) as mock_analyst, \
             patch.object(pm, '_execute_llm_task', new_callable=AsyncMock) as mock_pm, \
             patch.object(architect, '_execute_llm_task', new_callable=AsyncMock) as mock_architect:
            
            # Setup mock returns
            mock_analyst.return_value = {"requirements": ["REQ-1", "REQ-2"]}
            mock_pm.return_value = {"user_stories": ["STORY-1", "STORY-2"]}
            mock_architect.return_value = {"design": "Microservices"}
            
            # Simulate workflow
            req_result = await analyst.process_request("gather_requirements", {}, {})
            story_result = await pm.process_request("create_stories", {"requirements": req_result}, {})
            design_result = await architect.process_request("design", {"stories": story_result}, {})
            
            assert req_result is not None
            assert story_result is not None
            assert design_result is not None
    
    @pytest.mark.integration
    async def test_agent_error_handling(self, mock_agent_config):
        """Test agent error handling"""
        developer = EnhancedDeveloper(mock_agent_config)
        
        with patch.object(developer, '_execute_llm_task', new_callable=AsyncMock) as mock_llm:
            mock_llm.side_effect = Exception("API Error")
            
            with pytest.raises(Exception) as exc_info:
                await developer.process_request("generate_code", {}, {})
            
            assert "API Error" in str(exc_info.value)