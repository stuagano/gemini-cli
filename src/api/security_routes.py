"""
Security scanning and assessment API routes
Vulnerability scanning, security reports, and compliance endpoints
"""

import logging
import os
import asyncio
from datetime import datetime
from typing import Dict, List, Optional, Any
import tempfile
import shutil

from fastapi import APIRouter, Depends, HTTPException, status, File, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse

from security.auth import get_current_active_user, require_permission, User, Permission
from security.scanner import SecurityScanner, generate_security_report
from api.openapi_schemas import (
    BaseResponse, SecurityScanRequest, SecurityReport, SecurityFinding,
    SecuritySeverity
)

logger = logging.getLogger(__name__)

# Create router
router = APIRouter(prefix="/api/v1/security", tags=["Security"])

@router.post("/scan", response_model=SecurityReport)
async def start_security_scan(
    scan_request: SecurityScanRequest,
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_permission(Permission.SECURITY_SCAN))
):
    """Start a comprehensive security scan"""
    try:
        # Validate target path
        target_path = scan_request.target
        if not os.path.exists(target_path):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Target path does not exist: {target_path}"
            )
        
        # Validate scan types
        valid_scan_types = ["dependencies", "code", "secrets", "docker", "configuration", "api"]
        invalid_types = [t for t in scan_request.scan_types if t not in valid_scan_types]
        if invalid_types:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid scan types: {invalid_types}"
            )
        
        # Generate security report
        report = await generate_security_report(target_path)
        
        logger.info(f"Security scan completed for {target_path} by user {current_user.username}")
        
        return report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error during security scan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Security scan failed"
        )

@router.post("/scan/upload", response_model=SecurityReport)
async def scan_uploaded_file(
    file: UploadFile = File(..., description="File to scan"),
    scan_types: str = Form(default="dependencies,code,secrets", description="Comma-separated scan types"),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_permission(Permission.SECURITY_SCAN))
):
    """Scan an uploaded file or archive"""
    try:
        # Validate file type
        allowed_extensions = {'.py', '.js', '.ts', '.json', '.yaml', '.yml', '.txt', '.md', '.zip', '.tar.gz'}
        file_ext = os.path.splitext(file.filename)[1].lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File type not supported: {file_ext}"
            )
        
        # Create temporary directory
        temp_dir = tempfile.mkdtemp()
        temp_file_path = os.path.join(temp_dir, file.filename)
        
        try:
            # Save uploaded file
            with open(temp_file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Extract if archive
            scan_target = temp_file_path
            if file_ext in {'.zip', '.tar.gz'}:
                extract_dir = os.path.join(temp_dir, "extracted")
                os.makedirs(extract_dir)
                
                if file_ext == '.zip':
                    import zipfile
                    with zipfile.ZipFile(temp_file_path, 'r') as zip_ref:
                        zip_ref.extractall(extract_dir)
                elif file_ext == '.tar.gz':
                    import tarfile
                    with tarfile.open(temp_file_path, 'r:gz') as tar_ref:
                        tar_ref.extractall(extract_dir)
                
                scan_target = extract_dir
            
            # Perform security scan
            report = await generate_security_report(scan_target)
            
            # Update report to show it was from uploaded file
            report.target = f"uploaded_file:{file.filename}"
            
            logger.info(f"Security scan completed for uploaded file {file.filename} by user {current_user.username}")
            
            return report
            
        finally:
            # Cleanup temporary files
            shutil.rmtree(temp_dir, ignore_errors=True)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error scanning uploaded file: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="File scan failed"
        )

@router.get("/scans", response_model=List[Dict[str, Any]])
async def list_security_scans(
    limit: int = 50,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_permission(Permission.SECURITY_SCAN))
):
    """List recent security scans"""
    try:
        # In a real implementation, this would fetch from database
        # For now, return mock data
        scans = []
        
        return {
            "scans": scans,
            "total": len(scans),
            "limit": limit,
            "offset": offset
        }
        
    except Exception as e:
        logger.error(f"Error listing security scans: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list security scans"
        )

@router.get("/scans/{scan_id}", response_model=SecurityReport)
async def get_security_scan(
    scan_id: str,
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_permission(Permission.SECURITY_SCAN))
):
    """Get security scan results by ID"""
    try:
        # In a real implementation, fetch from database
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting security scan: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve security scan"
        )

@router.get("/scans/{scan_id}/report")
async def download_scan_report(
    scan_id: str,
    format: str = "json",
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_permission(Permission.SECURITY_SCAN))
):
    """Download security scan report in various formats"""
    try:
        if format not in ["json", "pdf", "csv"]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Unsupported format. Use: json, pdf, csv"
            )
        
        # In a real implementation, generate and return the report file
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Scan not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error downloading scan report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to download scan report"
        )

@router.get("/findings", response_model=List[SecurityFinding])
async def list_security_findings(
    severity: Optional[SecuritySeverity] = None,
    category: Optional[str] = None,
    limit: int = 100,
    offset: int = 0,
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_permission(Permission.SECURITY_SCAN))
):
    """List security findings with filtering"""
    try:
        # In a real implementation, fetch from database with filters
        findings = []
        
        # Apply filters
        if severity:
            findings = [f for f in findings if f.severity == severity]
        
        if category:
            findings = [f for f in findings if f.category == category]
        
        # Apply pagination
        paginated_findings = findings[offset:offset + limit]
        
        return paginated_findings
        
    except Exception as e:
        logger.error(f"Error listing security findings: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list security findings"
        )

@router.put("/findings/{finding_id}/status")
async def update_finding_status(
    finding_id: str,
    status: str = Form(..., regex="^(open|in_progress|resolved|false_positive|accepted_risk)$"),
    comment: Optional[str] = Form(None),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_permission(Permission.WRITE))
):
    """Update security finding status"""
    try:
        # In a real implementation, update finding in database
        logger.info(f"Finding {finding_id} status updated to {status} by {current_user.username}")
        
        return {
            "message": "Finding status updated successfully",
            "finding_id": finding_id,
            "status": status,
            "updated_by": current_user.username,
            "updated_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error updating finding status: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update finding status"
        )

@router.get("/compliance/report")
async def get_compliance_report(
    framework: str = "owasp",
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_permission(Permission.SECURITY_SCAN))
):
    """Get compliance report for security frameworks"""
    try:
        supported_frameworks = ["owasp", "nist", "iso27001", "pci_dss"]
        
        if framework not in supported_frameworks:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported framework. Use: {', '.join(supported_frameworks)}"
            )
        
        # Generate compliance report based on recent scans
        compliance_report = {
            "framework": framework,
            "timestamp": datetime.utcnow().isoformat(),
            "overall_score": 75,  # Mock score
            "compliance_level": "Partially Compliant",
            "categories": [
                {
                    "name": "Authentication",
                    "score": 85,
                    "status": "Compliant",
                    "findings": 2,
                    "recommendations": [
                        "Implement multi-factor authentication",
                        "Regular password policy review"
                    ]
                },
                {
                    "name": "Data Protection",
                    "score": 70,
                    "status": "Partially Compliant",
                    "findings": 5,
                    "recommendations": [
                        "Encrypt sensitive data at rest",
                        "Implement data classification"
                    ]
                },
                {
                    "name": "Access Control",
                    "score": 80,
                    "status": "Compliant",
                    "findings": 1,
                    "recommendations": [
                        "Review user permissions quarterly"
                    ]
                }
            ],
            "action_items": [
                "Address critical security findings",
                "Implement missing security controls",
                "Update security policies"
            ]
        }
        
        return compliance_report
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to generate compliance report"
        )

@router.get("/vulnerabilities/dashboard")
async def get_vulnerability_dashboard(
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_permission(Permission.SECURITY_SCAN))
):
    """Get vulnerability dashboard with key metrics"""
    try:
        # Mock dashboard data (in real implementation, aggregate from scans)
        dashboard = {
            "timestamp": datetime.utcnow().isoformat(),
            "summary": {
                "total_findings": 42,
                "critical": 2,
                "high": 8,
                "medium": 20,
                "low": 12,
                "open": 30,
                "resolved": 12
            },
            "trends": {
                "new_findings_7d": 5,
                "resolved_findings_7d": 8,
                "trend": "improving"
            },
            "top_categories": [
                {"category": "dependencies", "count": 15},
                {"category": "code", "count": 12},
                {"category": "secrets", "count": 8},
                {"category": "configuration", "count": 7}
            ],
            "recent_scans": [
                {
                    "id": "scan_123",
                    "target": "/path/to/project",
                    "timestamp": "2024-01-15T10:30:00Z",
                    "findings": 5,
                    "risk_score": 35
                }
            ],
            "recommendations": [
                "Update vulnerable dependencies",
                "Fix hardcoded secrets",
                "Enable security headers",
                "Implement input validation"
            ]
        }
        
        return dashboard
        
    except Exception as e:
        logger.error(f"Error getting vulnerability dashboard: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get vulnerability dashboard"
        )

@router.post("/whitelist")
async def add_to_whitelist(
    finding_id: str = Form(...),
    reason: str = Form(...),
    expires_at: Optional[datetime] = Form(None),
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_permission(Permission.ADMIN))
):
    """Add security finding to whitelist (admin only)"""
    try:
        # In a real implementation, add to whitelist in database
        logger.info(f"Finding {finding_id} added to whitelist by {current_user.username}")
        
        return {
            "message": "Finding added to whitelist successfully",
            "finding_id": finding_id,
            "reason": reason,
            "expires_at": expires_at.isoformat() if expires_at else None,
            "added_by": current_user.username,
            "added_at": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error adding finding to whitelist: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to add finding to whitelist"
        )

@router.get("/policies")
async def list_security_policies(
    current_user: User = Depends(get_current_active_user),
    _: None = Depends(require_permission(Permission.SECURITY_SCAN))
):
    """List security scanning policies and configurations"""
    try:
        policies = [
            {
                "id": "policy_1",
                "name": "Default Security Policy",
                "description": "Standard security scanning configuration",
                "scan_types": ["dependencies", "code", "secrets"],
                "severity_threshold": "medium",
                "auto_scan": True,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-10T15:30:00Z"
            },
            {
                "id": "policy_2", 
                "name": "Critical Systems Policy",
                "description": "Enhanced scanning for critical systems",
                "scan_types": ["dependencies", "code", "secrets", "docker", "configuration"],
                "severity_threshold": "low",
                "auto_scan": True,
                "created_at": "2024-01-01T12:00:00Z",
                "updated_at": "2024-01-05T09:15:00Z"
            }
        ]
        
        return {"policies": policies}
        
    except Exception as e:
        logger.error(f"Error listing security policies: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list security policies"
        )

@router.get("/health")
async def security_service_health():
    """Security service health check"""
    try:
        # Check security scanner components
        health_checks = {
            "scanner": "healthy",
            "dependency_db": "healthy", 
            "vulnerability_db": "healthy"
        }
        
        # In a real implementation, perform actual health checks
        overall_status = "healthy"
        
        return {
            "status": overall_status,
            "timestamp": datetime.utcnow().isoformat(),
            "components": health_checks,
            "version": "1.0.0"
        }
        
    except Exception as e:
        logger.error(f"Security service health check failed: {e}")
        return {
            "status": "unhealthy",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e)
        }