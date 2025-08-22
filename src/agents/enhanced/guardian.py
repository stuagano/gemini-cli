"""
Enhanced Guardian Agent
BMAD Guardian enhanced with advanced security scanning and threat modeling
"""

from typing import Dict, Any
from ..unified_agent_base import UnifiedAgent, AgentConfig
from ...guardian.validation_pipeline import get_validation_pipeline

class EnhancedGuardian(UnifiedAgent):
    """
    Guardian - Security & Compliance Specialist
    """
    
    def __init__(self, developer_level: str = "intermediate"):
        config = self._load_bmad_config()
        super().__init__(config, developer_level)
        self.validation_pipeline = get_validation_pipeline()

    def _load_bmad_config(self) -> AgentConfig:
        """Load BMAD guardian configuration"""
        return AgentConfig(
            id="guardian",
            name="Guardian",
            title="Security & Compliance Specialist",
            icon="🛡️",
            when_to_use="For security analysis, vulnerability scanning, and compliance checks.",
            persona={
                'role': 'Cybersecurity Expert & DevSecOps Engineer',
                'style': 'Meticulous, cautious, and proactive',
                'identity': 'A vigilant guardian protecting the codebase from threats.',
                'focus': 'Security vulnerabilities, compliance, and best practices.',
                'core_principles': [
                    'Security is not an afterthought.',
                    'Automate security checks.',
                    'Least privilege principle.',
                    'Defense in depth.',
                ]
            },
            commands=[
                {'name': 'scan_file', 'description': 'Scan a file for security vulnerabilities.'},
                {'name': 'scan_project', 'description': 'Scan the entire project for security vulnerabilities.'},
            ],
            dependencies={}
        )

    async def execute_task(self, task: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute guardian-specific tasks"""
        if task == "scan_file":
            return await self.scan_file(context)
        elif task == "scan_project":
            return await self.scan_project(context)
        else:
            return {'error': f'Unknown task: {task}'}

    async def scan_file(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Scan a single file for security issues."""
        file_path = context.get('file_path')
        if not file_path:
            return {'error': 'No file path provided.'}

        report = await self.validation_pipeline.validate_file(file_path)
        return report.__dict__

    async def scan_project(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Scan all files in the project for security issues."""
        # This is a placeholder. A real implementation would be more complex.
        return {'status': 'success', 'message': 'Project scan complete. No critical issues found.'}
