"""
DORA Metrics Tracking System
Implements the Four Key Metrics for software delivery performance
"""

import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from pathlib import Path

import aiohttp
import asyncpg
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

@dataclass
class DeploymentRecord:
    """Record of a deployment event"""
    timestamp: datetime
    repository: str
    commit_sha: str
    branch: str
    environment: str
    actor: str
    duration_seconds: Optional[float] = None
    success: bool = True
    workflow_id: Optional[str] = None

@dataclass
class IncidentRecord:
    """Record of an incident/failure"""
    timestamp: datetime
    repository: str
    incident_type: str
    severity: str
    description: str
    detection_time: datetime
    resolution_time: Optional[datetime] = None
    affected_deployments: List[str] = None

@dataclass
class DORAMetrics:
    """DORA metrics for a specific time period"""
    deployment_frequency: float  # Deployments per day
    lead_time_for_changes: float  # Hours from commit to deploy
    mean_time_to_recovery: float  # Hours to recover from failures
    change_failure_rate: float  # Percentage of deployments causing failures
    
    # Performance levels
    deployment_frequency_level: str
    lead_time_level: str
    mttr_level: str
    change_failure_level: str
    
    # Metadata
    period_start: datetime
    period_end: datetime
    total_deployments: int
    total_incidents: int
    calculated_at: datetime

class DORAMetricsTracker:
    """Main DORA metrics tracking and calculation engine"""
    
    def __init__(self, db_url: str = None):
        self.db_url = db_url
        self.db_pool = None
        
        # DORA performance level thresholds
        self.thresholds = {
            'deployment_frequency': {
                'elite': 1.0,      # >1 per day
                'high': 1/7,       # Weekly
                'medium': 1/30,    # Monthly
            },
            'lead_time': {
                'elite': 1,        # <1 hour
                'high': 24,        # <1 day
                'medium': 168,     # <1 week
            },
            'mttr': {
                'elite': 1,        # <1 hour
                'high': 24,        # <1 day
                'medium': 168,     # <1 week
            },
            'change_failure_rate': {
                'elite': 5,        # <5%
                'high': 10,        # <10%
                'medium': 20,      # <20%
            }
        }
    
    async def initialize(self):
        """Initialize database connection and tables"""
        if self.db_url:
            self.db_pool = await asyncpg.create_pool(self.db_url)
            await self._create_tables()
    
    async def _create_tables(self):
        """Create database tables for DORA metrics"""
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                CREATE TABLE IF NOT EXISTS deployments (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL,
                    repository VARCHAR(255) NOT NULL,
                    commit_sha VARCHAR(64) NOT NULL,
                    branch VARCHAR(255) NOT NULL,
                    environment VARCHAR(100) NOT NULL,
                    actor VARCHAR(255) NOT NULL,
                    duration_seconds FLOAT,
                    success BOOLEAN DEFAULT TRUE,
                    workflow_id VARCHAR(255),
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                
                CREATE TABLE IF NOT EXISTS incidents (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMPTZ NOT NULL,
                    repository VARCHAR(255) NOT NULL,
                    incident_type VARCHAR(100) NOT NULL,
                    severity VARCHAR(50) NOT NULL,
                    description TEXT,
                    detection_time TIMESTAMPTZ NOT NULL,
                    resolution_time TIMESTAMPTZ,
                    affected_deployments TEXT[],
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                
                CREATE TABLE IF NOT EXISTS lead_times (
                    id SERIAL PRIMARY KEY,
                    commit_sha VARCHAR(64) NOT NULL,
                    commit_time TIMESTAMPTZ NOT NULL,
                    deploy_time TIMESTAMPTZ NOT NULL,
                    lead_time_seconds FLOAT NOT NULL,
                    repository VARCHAR(255) NOT NULL,
                    created_at TIMESTAMPTZ DEFAULT NOW()
                );
                
                CREATE INDEX IF NOT EXISTS idx_deployments_repo_time 
                ON deployments(repository, timestamp);
                
                CREATE INDEX IF NOT EXISTS idx_incidents_repo_time 
                ON incidents(repository, timestamp);
            ''')
    
    async def record_deployment(self, deployment: DeploymentRecord):
        """Record a deployment event"""
        if not self.db_pool:
            logger.warning("Database not configured, storing deployment locally")
            await self._store_locally('deployments', asdict(deployment))
            return
        
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO deployments 
                (timestamp, repository, commit_sha, branch, environment, 
                 actor, duration_seconds, success, workflow_id)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9)
            ''', 
            deployment.timestamp, deployment.repository, deployment.commit_sha,
            deployment.branch, deployment.environment, deployment.actor,
            deployment.duration_seconds, deployment.success, deployment.workflow_id)
        
        logger.info(f"Recorded deployment: {deployment.repository}@{deployment.commit_sha}")
    
    async def record_incident(self, incident: IncidentRecord):
        """Record an incident/failure event"""
        if not self.db_pool:
            logger.warning("Database not configured, storing incident locally")
            await self._store_locally('incidents', asdict(incident))
            return
        
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO incidents 
                (timestamp, repository, incident_type, severity, description,
                 detection_time, resolution_time, affected_deployments)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            ''',
            incident.timestamp, incident.repository, incident.incident_type,
            incident.severity, incident.description, incident.detection_time,
            incident.resolution_time, incident.affected_deployments)
        
        logger.info(f"Recorded incident: {incident.repository} - {incident.incident_type}")
    
    async def record_lead_time(self, commit_sha: str, commit_time: datetime, 
                              deploy_time: datetime, repository: str):
        """Record lead time for a specific commit"""
        lead_time_seconds = (deploy_time - commit_time).total_seconds()
        
        if not self.db_pool:
            await self._store_locally('lead_times', {
                'commit_sha': commit_sha,
                'commit_time': commit_time.isoformat(),
                'deploy_time': deploy_time.isoformat(),
                'lead_time_seconds': lead_time_seconds,
                'repository': repository
            })
            return
        
        async with self.db_pool.acquire() as conn:
            await conn.execute('''
                INSERT INTO lead_times 
                (commit_sha, commit_time, deploy_time, lead_time_seconds, repository)
                VALUES ($1, $2, $3, $4, $5)
            ''', commit_sha, commit_time, deploy_time, lead_time_seconds, repository)
    
    async def calculate_metrics(self, repository: str, 
                              period_days: int = 7) -> DORAMetrics:
        """Calculate DORA metrics for a repository over a time period"""
        end_time = datetime.utcnow()
        start_time = end_time - timedelta(days=period_days)
        
        # Get deployments in period
        deployments = await self._get_deployments(repository, start_time, end_time)
        incidents = await self._get_incidents(repository, start_time, end_time)
        lead_times = await self._get_lead_times(repository, start_time, end_time)
        
        # Calculate metrics
        deployment_frequency = self._calculate_deployment_frequency(
            deployments, period_days)
        
        lead_time_for_changes = self._calculate_lead_time(lead_times)
        
        mean_time_to_recovery = self._calculate_mttr(incidents)
        
        change_failure_rate = self._calculate_change_failure_rate(
            deployments, incidents)
        
        # Determine performance levels
        levels = self._determine_performance_levels({
            'deployment_frequency': deployment_frequency,
            'lead_time': lead_time_for_changes,
            'mttr': mean_time_to_recovery,
            'change_failure_rate': change_failure_rate
        })
        
        return DORAMetrics(
            deployment_frequency=deployment_frequency,
            lead_time_for_changes=lead_time_for_changes,
            mean_time_to_recovery=mean_time_to_recovery,
            change_failure_rate=change_failure_rate,
            deployment_frequency_level=levels['deployment_frequency'],
            lead_time_level=levels['lead_time'],
            mttr_level=levels['mttr'],
            change_failure_level=levels['change_failure_rate'],
            period_start=start_time,
            period_end=end_time,
            total_deployments=len(deployments),
            total_incidents=len(incidents),
            calculated_at=datetime.utcnow()
        )
    
    def _calculate_deployment_frequency(self, deployments: List[Dict], 
                                      period_days: int) -> float:
        """Calculate deployments per day"""
        if period_days == 0:
            return 0.0
        return len(deployments) / period_days
    
    def _calculate_lead_time(self, lead_times: List[Dict]) -> float:
        """Calculate average lead time in hours"""
        if not lead_times:
            return 0.0
        
        total_seconds = sum(lt['lead_time_seconds'] for lt in lead_times)
        return total_seconds / len(lead_times) / 3600  # Convert to hours
    
    def _calculate_mttr(self, incidents: List[Dict]) -> float:
        """Calculate mean time to recovery in hours"""
        resolved_incidents = [
            i for i in incidents 
            if i.get('resolution_time') and i.get('detection_time')
        ]
        
        if not resolved_incidents:
            return 0.0
        
        total_recovery_time = 0
        for incident in resolved_incidents:
            detection = incident['detection_time']
            resolution = incident['resolution_time']
            if isinstance(detection, str):
                detection = datetime.fromisoformat(detection)
            if isinstance(resolution, str):
                resolution = datetime.fromisoformat(resolution)
            
            recovery_time = (resolution - detection).total_seconds()
            total_recovery_time += recovery_time
        
        return total_recovery_time / len(resolved_incidents) / 3600  # Hours
    
    def _calculate_change_failure_rate(self, deployments: List[Dict], 
                                     incidents: List[Dict]) -> float:
        """Calculate change failure rate as percentage"""
        if not deployments:
            return 0.0
        
        # Count deployments that caused incidents
        failed_deployments = set()
        for incident in incidents:
            if incident.get('affected_deployments'):
                failed_deployments.update(incident['affected_deployments'])
        
        return (len(failed_deployments) / len(deployments)) * 100
    
    def _determine_performance_levels(self, metrics: Dict[str, float]) -> Dict[str, str]:
        """Determine performance level (Elite, High, Medium, Low) for each metric"""
        levels = {}
        
        # Deployment Frequency
        df = metrics['deployment_frequency']
        if df >= self.thresholds['deployment_frequency']['elite']:
            levels['deployment_frequency'] = 'Elite'
        elif df >= self.thresholds['deployment_frequency']['high']:
            levels['deployment_frequency'] = 'High'
        elif df >= self.thresholds['deployment_frequency']['medium']:
            levels['deployment_frequency'] = 'Medium'
        else:
            levels['deployment_frequency'] = 'Low'
        
        # Lead Time (lower is better)
        lt = metrics['lead_time']
        if lt <= self.thresholds['lead_time']['elite']:
            levels['lead_time'] = 'Elite'
        elif lt <= self.thresholds['lead_time']['high']:
            levels['lead_time'] = 'High'
        elif lt <= self.thresholds['lead_time']['medium']:
            levels['lead_time'] = 'Medium'
        else:
            levels['lead_time'] = 'Low'
        
        # MTTR (lower is better)
        mttr = metrics['mttr']
        if mttr <= self.thresholds['mttr']['elite']:
            levels['mttr'] = 'Elite'
        elif mttr <= self.thresholds['mttr']['high']:
            levels['mttr'] = 'High'
        elif mttr <= self.thresholds['mttr']['medium']:
            levels['mttr'] = 'Medium'
        else:
            levels['mttr'] = 'Low'
        
        # Change Failure Rate (lower is better)
        cfr = metrics['change_failure_rate']
        if cfr <= self.thresholds['change_failure_rate']['elite']:
            levels['change_failure_rate'] = 'Elite'
        elif cfr <= self.thresholds['change_failure_rate']['high']:
            levels['change_failure_rate'] = 'High'
        elif cfr <= self.thresholds['change_failure_rate']['medium']:
            levels['change_failure_rate'] = 'Medium'
        else:
            levels['change_failure_rate'] = 'Low'
        
        return levels
    
    async def _get_deployments(self, repository: str, start_time: datetime, 
                             end_time: datetime) -> List[Dict]:
        """Get deployments for repository in time period"""
        if not self.db_pool:
            return await self._load_locally('deployments', repository, start_time, end_time)
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM deployments 
                WHERE repository = $1 AND timestamp BETWEEN $2 AND $3
                ORDER BY timestamp
            ''', repository, start_time, end_time)
            
            return [dict(row) for row in rows]
    
    async def _get_incidents(self, repository: str, start_time: datetime,
                           end_time: datetime) -> List[Dict]:
        """Get incidents for repository in time period"""
        if not self.db_pool:
            return await self._load_locally('incidents', repository, start_time, end_time)
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM incidents 
                WHERE repository = $1 AND timestamp BETWEEN $2 AND $3
                ORDER BY timestamp
            ''', repository, start_time, end_time)
            
            return [dict(row) for row in rows]
    
    async def _get_lead_times(self, repository: str, start_time: datetime,
                            end_time: datetime) -> List[Dict]:
        """Get lead times for repository in time period"""
        if not self.db_pool:
            return await self._load_locally('lead_times', repository, start_time, end_time)
        
        async with self.db_pool.acquire() as conn:
            rows = await conn.fetch('''
                SELECT * FROM lead_times 
                WHERE repository = $1 AND deploy_time BETWEEN $2 AND $3
                ORDER BY deploy_time
            ''', repository, start_time, end_time)
            
            return [dict(row) for row in rows]
    
    async def _store_locally(self, table: str, data: Dict):
        """Store data locally when database is not available"""
        local_dir = Path('data/dora_metrics')
        local_dir.mkdir(parents=True, exist_ok=True)
        
        file_path = local_dir / f"{table}.jsonl"
        
        # Append to JSONL file
        with open(file_path, 'a') as f:
            json.dump(data, f, default=str)
            f.write('\n')
    
    async def _load_locally(self, table: str, repository: str,
                          start_time: datetime, end_time: datetime) -> List[Dict]:
        """Load data from local files"""
        file_path = Path(f'data/dora_metrics/{table}.jsonl')
        if not file_path.exists():
            return []
        
        records = []
        with open(file_path) as f:
            for line in f:
                record = json.loads(line)
                if record.get('repository') == repository:
                    # Check time range
                    timestamp_field = 'timestamp' if 'timestamp' in record else 'deploy_time'
                    if timestamp_field in record:
                        record_time = datetime.fromisoformat(
                            record[timestamp_field].replace('Z', '+00:00'))
                        if start_time <= record_time <= end_time:
                            records.append(record)
        
        return records
    
    async def get_trends(self, repository: str, weeks: int = 12) -> Dict[str, List]:
        """Get trend data for dashboard charts"""
        trends = {
            'deployment_frequency': [],
            'lead_time': [],
            'mttr': [],
            'change_failure_rate': [],
            'weeks': []
        }
        
        for week in range(weeks):
            start_week = datetime.utcnow() - timedelta(weeks=week+1)
            metrics = await self.calculate_metrics(repository, period_days=7)
            
            trends['deployment_frequency'].insert(0, metrics.deployment_frequency)
            trends['lead_time'].insert(0, metrics.lead_time_for_changes)
            trends['mttr'].insert(0, metrics.mean_time_to_recovery)
            trends['change_failure_rate'].insert(0, metrics.change_failure_rate)
            trends['weeks'].insert(0, start_week.strftime('%Y-W%U'))
        
        return trends

# FastAPI router for DORA metrics API
router = APIRouter(prefix="/api/v1/dora", tags=["DORA Metrics"])

# Global tracker instance
tracker = DORAMetricsTracker()

class DeploymentRequest(BaseModel):
    repository: str
    commit_sha: str
    branch: str
    environment: str
    actor: str
    success: bool = True
    workflow_id: Optional[str] = None

class IncidentRequest(BaseModel):
    repository: str
    incident_type: str
    severity: str
    description: str
    affected_deployments: Optional[List[str]] = None

@router.post("/deployments")
async def record_deployment_endpoint(deployment: DeploymentRequest):
    """Record a deployment event"""
    deployment_record = DeploymentRecord(
        timestamp=datetime.utcnow(),
        repository=deployment.repository,
        commit_sha=deployment.commit_sha,
        branch=deployment.branch,
        environment=deployment.environment,
        actor=deployment.actor,
        success=deployment.success,
        workflow_id=deployment.workflow_id
    )
    
    await tracker.record_deployment(deployment_record)
    return {"status": "recorded", "deployment_id": deployment.commit_sha}

@router.post("/incidents")
async def record_incident_endpoint(incident: IncidentRequest):
    """Record an incident/failure event"""
    incident_record = IncidentRecord(
        timestamp=datetime.utcnow(),
        repository=incident.repository,
        incident_type=incident.incident_type,
        severity=incident.severity,
        description=incident.description,
        detection_time=datetime.utcnow(),
        affected_deployments=incident.affected_deployments or []
    )
    
    await tracker.record_incident(incident_record)
    return {"status": "recorded"}

@router.get("/metrics/{repository}")
async def get_metrics_endpoint(repository: str, period_days: int = 7):
    """Get DORA metrics for a repository"""
    try:
        metrics = await tracker.calculate_metrics(repository, period_days)
        return asdict(metrics)
    except Exception as e:
        logger.error(f"Error calculating metrics: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/trends/{repository}")
async def get_trends_endpoint(repository: str, weeks: int = 12):
    """Get trend data for dashboard"""
    try:
        trends = await tracker.get_trends(repository, weeks)
        return trends
    except Exception as e:
        logger.error(f"Error getting trends: {e}")
        raise HTTPException(status_code=500, detail=str(e))