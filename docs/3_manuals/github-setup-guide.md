# GitHub Integration Setup Guide

## Overview

Gemini Enterprise Architect integrates with GitHub through two complementary approaches:

1. **GitHub Actions Integration** - CI/CD workflows for automated analysis and deployment
2. **GitHub App Integration** - Real-time webhook processing for instant feedback

Both approaches can be used together for maximum automation and efficiency.

## GitHub Actions Setup

### Quick Start

1. Create `.github/workflows/gemini-analysis.yml` in your repository:

```yaml
name: Gemini Enterprise Analysis

on:
  push:
    branches: [main, develop]
  pull_request:
    types: [opened, synchronize, reopened]
  workflow_dispatch:
    inputs:
      analysis_depth:
        description: 'Analysis depth (quick/standard/comprehensive)'
        required: false
        default: 'standard'

jobs:
  analyze:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0  # Full history for better analysis
      
      - name: Setup Gemini CLI
        run: |
          npm install -g @gemini/cli
          gemini config set api.key ${{ secrets.GEMINI_API_KEY }}
      
      - name: Run Security Scan
        run: |
          gemini scan security \
            --output security-report.json \
            --fail-on critical
      
      - name: Analyze Architecture
        run: |
          gemini analyze architecture \
            --pattern microservices \
            --output architecture-report.json
      
      - name: Check Code Quality
        run: |
          gemini analyze quality \
            --threshold 80 \
            --output quality-report.json
      
      - name: Generate Summary
        if: github.event_name == 'pull_request'
        run: |
          gemini report summary \
            --format markdown \
            --output summary.md
      
      - name: Comment on PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const summary = fs.readFileSync('summary.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: summary
            });
```

2. Add repository secrets:
   - `GEMINI_API_KEY` - Your Gemini API key
   - `GCP_PROJECT_ID` - Google Cloud project ID
   - `GITHUB_TOKEN` - Automatically provided by GitHub Actions

### Advanced Workflows

#### Mobile-Triggered Analysis

```yaml
name: Gemini Mobile Trigger

on:
  workflow_dispatch:
    inputs:
      command:
        description: 'Gemini command to run'
        required: true
        type: choice
        options:
          - 'quick-analysis'
          - 'security-scan'
          - 'architecture-review'
          - 'performance-check'
          - 'deploy-staging'
          - 'deploy-production'
      
      notify_slack:
        description: 'Send results to Slack'
        required: false
        type: boolean
        default: true

jobs:
  mobile_analysis:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Gemini
        run: |
          npm install -g @gemini/cli
          gemini config set api.key ${{ secrets.GEMINI_API_KEY }}
      
      - name: Execute Command
        id: gemini
        run: |
          case "${{ inputs.command }}" in
            "quick-analysis")
              gemini analyze quick --json > result.json
              ;;
            "security-scan")
              gemini scan security --comprehensive --json > result.json
              ;;
            "architecture-review")
              gemini analyze architecture --deep --json > result.json
              ;;
            "performance-check")
              gemini analyze performance --profile --json > result.json
              ;;
            "deploy-staging")
              gemini deploy staging --auto-rollback --json > result.json
              ;;
            "deploy-production")
              gemini deploy production --canary --json > result.json
              ;;
          esac
          
          # Extract summary for output
          echo "summary=$(jq -r '.summary' result.json)" >> $GITHUB_OUTPUT
      
      - name: Send to Slack
        if: inputs.notify_slack == true
        uses: slackapi/slack-github-action@v1
        with:
          payload: |
            {
              "text": "Gemini Analysis Complete",
              "blocks": [
                {
                  "type": "section",
                  "text": {
                    "type": "mrkdwn",
                    "text": "*Command:* ${{ inputs.command }}\n*Result:* ${{ steps.gemini.outputs.summary }}"
                  }
                }
              ]
            }
        env:
          SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }}
```

#### Comprehensive PR Analysis

```yaml
name: PR Comprehensive Analysis

on:
  pull_request:
    types: [opened, synchronize]

jobs:
  analyze_pr:
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
        with:
          fetch-depth: 0
      
      - name: Setup Environment
        run: |
          npm install -g @gemini/cli
          pip install safety bandit
          
      - name: Scout Duplicate Detection
        id: scout
        run: |
          gemini scout analyze \
            --detect-duplicates \
            --threshold 0.8 \
            --output scout-report.json
          
          duplicates=$(jq '.duplicates | length' scout-report.json)
          echo "duplicate_count=$duplicates" >> $GITHUB_OUTPUT
      
      - name: Security Analysis
        run: |
          gemini scan security --comprehensive
          safety check --json > safety-report.json
          bandit -r . -f json > bandit-report.json
      
      - name: Architecture Impact Analysis
        run: |
          gemini analyze architecture \
            --compare-with main \
            --detect-breaking-changes \
            --output architecture-impact.json
      
      - name: Performance Regression Check
        run: |
          gemini analyze performance \
            --baseline main \
            --fail-on-regression \
            --output performance-report.json
      
      - name: Generate Comprehensive Report
        run: |
          gemini report generate \
            --input "*.json" \
            --format markdown \
            --include-recommendations \
            --output pr-analysis.md
      
      - name: Update PR Status
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('pr-analysis.md', 'utf8');
            
            // Add comment
            await github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: report
            });
            
            // Add labels based on analysis
            const labels = [];
            if (${{ steps.scout.outputs.duplicate_count }} > 0) {
              labels.push('has-duplicates');
            }
            
            if (labels.length > 0) {
              await github.rest.issues.addLabels({
                issue_number: context.issue.number,
                owner: context.repo.owner,
                repo: context.repo.repo,
                labels: labels
              });
            }
```

### Deployment Workflows

#### Automated Deployment Pipeline

```yaml
name: Deploy with Gemini

on:
  push:
    branches: [main]
  workflow_dispatch:

env:
  GCP_PROJECT: ${{ secrets.GCP_PROJECT_ID }}
  REGION: us-central1

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Tests
        run: |
          npm test
          python -m pytest
      
      - name: Gemini Test Analysis
        run: |
          gemini analyze test-results \
            --coverage-threshold 80 \
            --fail-on-decrease

  deploy:
    needs: test
    runs-on: ubuntu-latest
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Setup Cloud SDK
        uses: google-github-actions/setup-gcloud@v1
        with:
          service_account_key: ${{ secrets.GCP_SA_KEY }}
          project_id: ${{ secrets.GCP_PROJECT_ID }}
      
      - name: Build and Deploy
        run: |
          # Build Docker image
          docker build -t gcr.io/$GCP_PROJECT/gemini-app:$GITHUB_SHA .
          docker push gcr.io/$GCP_PROJECT/gemini-app:$GITHUB_SHA
          
          # Deploy with Gemini orchestration
          gemini deploy production \
            --image gcr.io/$GCP_PROJECT/gemini-app:$GITHUB_SHA \
            --strategy canary \
            --rollback-on-error \
            --monitor-duration 10m
      
      - name: Update DORA Metrics
        run: |
          gemini metrics record deployment \
            --sha $GITHUB_SHA \
            --environment production \
            --timestamp $(date -u +"%Y-%m-%dT%H:%M:%SZ")
```

## GitHub App Setup

### Creating the GitHub App

1. Go to GitHub Settings > Developer settings > GitHub Apps
2. Click "New GitHub App"
3. Configure with these settings:

```yaml
name: Gemini Enterprise Architect
description: AI-powered code analysis and architecture guidance
homepage_url: https://gemini-architect.example.com
webhook_url: https://api.gemini-architect.example.com/webhooks/github
webhook_secret: <generate-strong-secret>

permissions:
  actions: read
  checks: write
  contents: read
  issues: write
  metadata: read
  pull_requests: write
  repository_projects: read
  statuses: write
  
subscribe_to_events:
  - check_run
  - check_suite
  - issue_comment
  - issues
  - pull_request
  - pull_request_review
  - pull_request_review_comment
  - push
  - release
  - repository_dispatch
  - workflow_dispatch
  - workflow_run
```

### Server Implementation

#### FastAPI Webhook Handler

```python
# github_app/webhook_handler.py
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
import hmac
import hashlib
import json
from typing import Dict, Any
import asyncio

app = FastAPI(title="Gemini GitHub App")

# Import agent system
from agents.unified_agent_base import UnifiedAgent
from agents.scout import ScoutAgent
from agents.architect import ArchitectAgent

class GitHubWebhookHandler:
    def __init__(self, webhook_secret: str):
        self.webhook_secret = webhook_secret.encode()
        self.agents = {
            'scout': ScoutAgent(),
            'architect': ArchitectAgent()
        }
    
    def verify_signature(self, payload: bytes, signature: str) -> bool:
        """Verify GitHub webhook signature"""
        expected = hmac.new(
            self.webhook_secret,
            payload,
            hashlib.sha256
        ).hexdigest()
        return hmac.compare_digest(f"sha256={expected}", signature)
    
    async def process_event(self, event_type: str, payload: Dict[str, Any]):
        """Process GitHub webhook event"""
        
        if event_type == "pull_request":
            await self.handle_pull_request(payload)
        elif event_type == "push":
            await self.handle_push(payload)
        elif event_type == "issue_comment":
            await self.handle_comment(payload)
        elif event_type == "workflow_run":
            await self.handle_workflow_run(payload)
    
    async def handle_pull_request(self, payload: Dict[str, Any]):
        """Handle PR events"""
        action = payload['action']
        pr = payload['pull_request']
        
        if action in ['opened', 'synchronize']:
            # Run Scout analysis
            scout_result = await self.agents['scout'].analyze_pr(
                repo=payload['repository']['full_name'],
                pr_number=pr['number'],
                base_sha=pr['base']['sha'],
                head_sha=pr['head']['sha']
            )
            
            # Run Architect review
            architect_result = await self.agents['architect'].review_changes(
                changes=scout_result['changes'],
                patterns=scout_result['patterns']
            )
            
            # Post results as PR comment
            await self.post_pr_comment(
                repo=payload['repository']['full_name'],
                pr_number=pr['number'],
                comment=self.format_analysis_results(scout_result, architect_result)
            )
    
    async def handle_comment(self, payload: Dict[str, Any]):
        """Handle issue/PR comments for commands"""
        comment = payload['comment']['body']
        
        # Check for Gemini commands
        if comment.startswith('/gemini'):
            command_parts = comment.split()
            
            if len(command_parts) > 1:
                command = command_parts[1]
                
                if command == 'analyze':
                    await self.run_analysis(payload)
                elif command == 'deploy':
                    await self.trigger_deployment(payload)
                elif command == 'benchmark':
                    await self.run_benchmarks(payload)

handler = GitHubWebhookHandler(webhook_secret=os.getenv('GITHUB_WEBHOOK_SECRET'))

@app.post("/webhooks/github")
async def github_webhook(request: Request):
    """Handle GitHub webhook events"""
    
    # Verify signature
    signature = request.headers.get('X-Hub-Signature-256')
    if not signature:
        raise HTTPException(status_code=401, detail="Missing signature")
    
    payload = await request.body()
    
    if not handler.verify_signature(payload, signature):
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Process event
    event_type = request.headers.get('X-GitHub-Event')
    payload_dict = json.loads(payload)
    
    # Process asynchronously
    asyncio.create_task(handler.process_event(event_type, payload_dict))
    
    return JSONResponse({"status": "accepted"}, status_code=202)
```

### Docker Deployment

```yaml
# docker-compose.yml
version: '3.8'

services:
  gemini-server:
    build: .
    ports:
      - "8000:8000"
    environment:
      - GITHUB_APP_ID=${GITHUB_APP_ID}
      - GITHUB_APP_PRIVATE_KEY=${GITHUB_APP_PRIVATE_KEY}
      - GITHUB_WEBHOOK_SECRET=${GITHUB_WEBHOOK_SECRET}
      - GEMINI_API_KEY=${GEMINI_API_KEY}
      - REDIS_URL=redis://redis:6379
      - DATABASE_URL=postgresql://postgres:password@db:5432/gemini
    depends_on:
      - redis
      - db
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

  db:
    image: postgres:15
    environment:
      - POSTGRES_DB=gemini
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./certs:/etc/nginx/certs
    depends_on:
      - gemini-server
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
```

### Production Deployment

#### Kubernetes Deployment

```yaml
# k8s/deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: gemini-github-app
  namespace: gemini
spec:
  replicas: 3
  selector:
    matchLabels:
      app: gemini-github-app
  template:
    metadata:
      labels:
        app: gemini-github-app
    spec:
      containers:
      - name: app
        image: gcr.io/PROJECT_ID/gemini-github-app:latest
        ports:
        - containerPort: 8000
        env:
        - name: GITHUB_APP_ID
          valueFrom:
            secretKeyRef:
              name: github-app-secrets
              key: app-id
        - name: GITHUB_WEBHOOK_SECRET
          valueFrom:
            secretKeyRef:
              name: github-app-secrets
              key: webhook-secret
        - name: REDIS_URL
          value: redis://redis-service:6379
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /ready
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: gemini-github-app-service
  namespace: gemini
spec:
  selector:
    app: gemini-github-app
  ports:
  - port: 80
    targetPort: 8000
  type: LoadBalancer
---
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: gemini-github-app-ingress
  namespace: gemini
  annotations:
    kubernetes.io/ingress.class: nginx
    cert-manager.io/cluster-issuer: letsencrypt-prod
spec:
  tls:
  - hosts:
    - api.gemini-architect.example.com
    secretName: gemini-tls
  rules:
  - host: api.gemini-architect.example.com
    http:
      paths:
      - path: /webhooks/github
        pathType: Prefix
        backend:
          service:
            name: gemini-github-app-service
            port:
              number: 80
```

### Security Configuration

#### Secrets Management

```bash
# Create GitHub App private key secret
kubectl create secret generic github-app-secrets \
  --from-file=private-key=github-app.pem \
  --from-literal=app-id=123456 \
  --from-literal=webhook-secret=your-webhook-secret \
  -n gemini

# Create Gemini API key secret
kubectl create secret generic gemini-secrets \
  --from-literal=api-key=your-gemini-api-key \
  -n gemini
```

#### Network Security

```yaml
# k8s/network-policy.yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata:
  name: gemini-app-network-policy
  namespace: gemini
spec:
  podSelector:
    matchLabels:
      app: gemini-github-app
  policyTypes:
  - Ingress
  - Egress
  ingress:
  - from:
    - namespaceSelector:
        matchLabels:
          name: ingress-nginx
    ports:
    - protocol: TCP
      port: 8000
  egress:
  - to:
    - namespaceSelector: {}
    ports:
    - protocol: TCP
      port: 443  # HTTPS
    - protocol: TCP
      port: 6379  # Redis
    - protocol: TCP
      port: 5432  # PostgreSQL
```

### Monitoring and Health Checks

#### Health Check Endpoints

```python
# health.py
from fastapi import APIRouter
from datetime import datetime
import redis
import psycopg2

router = APIRouter()

@router.get("/health")
async def health_check():
    """Basic health check"""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "version": "1.0.0"
    }

@router.get("/ready")
async def readiness_check():
    """Readiness check with dependency validation"""
    checks = {
        "redis": check_redis(),
        "database": check_database(),
        "github": check_github_connection()
    }
    
    all_healthy = all(checks.values())
    
    return {
        "ready": all_healthy,
        "checks": checks,
        "timestamp": datetime.utcnow().isoformat()
    }

def check_redis():
    try:
        r = redis.Redis.from_url(os.getenv('REDIS_URL'))
        r.ping()
        return True
    except:
        return False

def check_database():
    try:
        conn = psycopg2.connect(os.getenv('DATABASE_URL'))
        conn.close()
        return True
    except:
        return False

def check_github_connection():
    try:
        # Verify GitHub App installation
        return True  # Implement actual check
    except:
        return False
```

#### Prometheus Metrics

```python
# metrics.py
from prometheus_client import Counter, Histogram, Gauge
import time

# Define metrics
webhook_received = Counter(
    'github_webhooks_received_total',
    'Total GitHub webhooks received',
    ['event_type']
)

webhook_processing_time = Histogram(
    'github_webhook_processing_seconds',
    'Time to process GitHub webhooks',
    ['event_type']
)

active_analysis_jobs = Gauge(
    'gemini_active_analysis_jobs',
    'Number of active analysis jobs'
)

def track_webhook(event_type: str):
    """Decorator to track webhook metrics"""
    def decorator(func):
        async def wrapper(*args, **kwargs):
            webhook_received.labels(event_type=event_type).inc()
            active_analysis_jobs.inc()
            
            start_time = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration = time.time() - start_time
                webhook_processing_time.labels(event_type=event_type).observe(duration)
                active_analysis_jobs.dec()
        
        return wrapper
    return decorator
```

## Advanced Features

### Custom Commands

Add custom slash commands to your repository:

```python
# commands/custom_commands.py
class GeminiCommands:
    """Custom Gemini slash commands for GitHub"""
    
    COMMANDS = {
        '/gemini analyze': 'Run comprehensive analysis',
        '/gemini deploy <env>': 'Deploy to environment',
        '/gemini rollback': 'Rollback last deployment',
        '/gemini benchmark': 'Run performance benchmarks',
        '/gemini security': 'Run security scan',
        '/gemini scale <replicas>': 'Scale application',
        '/gemini logs <service>': 'Get service logs',
        '/gemini metrics': 'Get current metrics'
    }
    
    async def handle_command(self, command: str, args: List[str], context: Dict):
        """Handle custom command"""
        
        if command == 'analyze':
            return await self.run_analysis(context)
        elif command == 'deploy':
            return await self.deploy_environment(args[0], context)
        elif command == 'rollback':
            return await self.rollback_deployment(context)
        # ... more commands
```

### Branch Protection Integration

```python
# branch_protection.py
async def setup_branch_protection(repo: str, branch: str = "main"):
    """Setup branch protection with Gemini checks"""
    
    protection_rules = {
        "required_status_checks": {
            "strict": True,
            "contexts": [
                "Gemini Security Scan",
                "Gemini Architecture Review",
                "Gemini Code Quality",
                "Gemini Performance Check"
            ]
        },
        "enforce_admins": True,
        "required_pull_request_reviews": {
            "required_approving_review_count": 1,
            "dismiss_stale_reviews": True
        },
        "restrictions": None
    }
    
    # Apply via GitHub API
    await github_client.update_branch_protection(repo, branch, protection_rules)
```

### Auto-Fix Capabilities

```python
# auto_fix.py
class AutoFixer:
    """Automatically fix common issues"""
    
    async def auto_fix_pr(self, pr_url: str):
        """Automatically fix issues in PR"""
        
        # Analyze PR
        issues = await self.analyze_pr(pr_url)
        
        fixes_applied = []
        
        for issue in issues:
            if issue['type'] == 'formatting':
                await self.fix_formatting(issue)
                fixes_applied.append('formatting')
            
            elif issue['type'] == 'imports':
                await self.fix_imports(issue)
                fixes_applied.append('imports')
            
            elif issue['type'] == 'simple_bugs':
                await self.fix_simple_bugs(issue)
                fixes_applied.append('bugs')
        
        if fixes_applied:
            # Commit fixes
            await self.commit_fixes(pr_url, fixes_applied)
            
            # Comment on PR
            await self.comment_fixes_applied(pr_url, fixes_applied)
```

## Integration with Other Services

### Slack Integration

```python
# integrations/slack.py
from slack_sdk.webhook import WebhookClient

class SlackNotifier:
    def __init__(self, webhook_url: str):
        self.client = WebhookClient(webhook_url)
    
    async def notify_analysis_complete(self, repo: str, pr: int, results: Dict):
        """Send analysis results to Slack"""
        
        blocks = [
            {
                "type": "header",
                "text": {
                    "type": "plain_text",
                    "text": f"Gemini Analysis Complete"
                }
            },
            {
                "type": "section",
                "fields": [
                    {"type": "mrkdwn", "text": f"*Repository:* {repo}"},
                    {"type": "mrkdwn", "text": f"*PR:* #{pr}"},
                    {"type": "mrkdwn", "text": f"*Security Score:* {results['security_score']}/100"},
                    {"type": "mrkdwn", "text": f"*Quality Score:* {results['quality_score']}/100"}
                ]
            },
            {
                "type": "actions",
                "elements": [
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "View Details"},
                        "url": f"https://github.com/{repo}/pull/{pr}"
                    },
                    {
                        "type": "button",
                        "text": {"type": "plain_text", "text": "Deploy"},
                        "action_id": "deploy_pr",
                        "value": f"{repo}:{pr}"
                    }
                ]
            }
        ]
        
        self.client.send(blocks=blocks)
```

### JIRA Integration

```python
# integrations/jira.py
from jira import JIRA

class JiraIntegration:
    def __init__(self, server: str, email: str, token: str):
        self.jira = JIRA(server=server, basic_auth=(email, token))
    
    async def create_issue_from_finding(self, finding: Dict):
        """Create JIRA issue from security finding"""
        
        issue_dict = {
            'project': 'SEC',
            'summary': f"Security: {finding['title']}",
            'description': finding['description'],
            'issuetype': {'name': 'Bug'},
            'priority': {'name': self.map_priority(finding['severity'])},
            'labels': ['security', 'gemini-detected']
        }
        
        issue = self.jira.create_issue(fields=issue_dict)
        return issue.key
```

## Best Practices

### Repository Configuration

Create `.gemini/config.yml` in your repository:

```yaml
# .gemini/config.yml
version: 1
analysis:
  auto_analyze_prs: true
  auto_fix_simple_issues: true
  fail_on_critical_issues: true
  
security:
  scan_dependencies: true
  scan_containers: true
  scan_secrets: true
  block_on_vulnerabilities: true
  
architecture:
  enforce_patterns: true
  pattern: microservices
  service_boundaries: strict
  
quality:
  min_coverage: 80
  max_complexity: 10
  enforce_standards: true
  
deployment:
  environments:
    - staging
    - production
  strategy: canary
  rollback_on_failure: true
  
notifications:
  slack:
    enabled: true
    channel: "#deployments"
  email:
    enabled: false
```

### Team Workflows

1. **Developer Workflow**
   - Push code to feature branch
   - Gemini automatically analyzes changes
   - Address feedback before merging
   - Auto-deploy on merge to main

2. **Security Team Workflow**
   - Monitor security dashboard
   - Review critical findings
   - Track remediation progress
   - Validate fixes

3. **DevOps Workflow**
   - Monitor deployment metrics
   - Review performance impacts
   - Manage rollbacks if needed
   - Track DORA metrics