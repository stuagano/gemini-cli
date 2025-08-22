# GitHub Integration Troubleshooting Guide

## Common Issues and Solutions

### Connection Issues

#### Error: "Failed to connect to Gemini server"

**Symptoms:**
- Webhook returns 502/503 errors
- GitHub Actions fail with connection timeout
- Cannot reach API endpoints

**Solutions:**

1. **Check server status:**
```bash
curl -I https://api.gemini-architect.example.com/health
```

2. **Verify DNS resolution:**
```bash
nslookup api.gemini-architect.example.com
dig api.gemini-architect.example.com
```

3. **Check firewall rules:**
```bash
# For GCP
gcloud compute firewall-rules list
gcloud compute firewall-rules describe gemini-allow-github

# For AWS
aws ec2 describe-security-groups --group-ids sg-xxxxx
```

4. **Verify SSL certificate:**
```bash
openssl s_client -connect api.gemini-architect.example.com:443 -servername api.gemini-architect.example.com
```

5. **Check container/pod status:**
```bash
# Docker
docker ps -a | grep gemini
docker logs gemini-server

# Kubernetes
kubectl get pods -n gemini
kubectl describe pod <pod-name> -n gemini
kubectl logs <pod-name> -n gemini
```

#### Error: "Webhook delivery failed"

**Symptoms:**
- GitHub shows webhook delivery failures
- Red X next to webhook deliveries
- No analysis results on PRs

**Solutions:**

1. **Verify webhook URL:**
```bash
# Check webhook configuration in GitHub
# Settings > Webhooks > Edit webhook
# Ensure URL is: https://api.gemini-architect.example.com/webhooks/github
```

2. **Test webhook manually:**
```bash
curl -X POST https://api.gemini-architect.example.com/webhooks/github \
  -H "Content-Type: application/json" \
  -H "X-GitHub-Event: ping" \
  -H "X-Hub-Signature-256: sha256=test" \
  -d '{"zen": "Design for failure."}'
```

3. **Check webhook secret:**
```python
# verify_webhook.py
import hmac
import hashlib

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)

# Test with your secret
secret = "your-webhook-secret"
payload = b'{"test": "data"}'
signature = "sha256=" + hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
print(verify_signature(payload, signature, secret))
```

4. **Review webhook logs:**
```bash
# Server logs
docker logs gemini-server --tail 100 | grep webhook

# Kubernetes logs
kubectl logs -n gemini deployment/gemini-github-app --tail=100 | grep webhook
```

### Authentication Issues

#### Error: "Bad credentials" or "401 Unauthorized"

**Symptoms:**
- Cannot authenticate with GitHub API
- PR comments fail to post
- Status checks don't update

**Solutions:**

1. **Verify GitHub App installation:**
```bash
# List installations
curl -H "Authorization: Bearer $(generate-jwt)" \
  https://api.github.com/app/installations

# Check specific installation
curl -H "Authorization: Bearer $(generate-jwt)" \
  https://api.github.com/app/installations/{installation_id}
```

2. **Regenerate installation token:**
```python
# generate_token.py
import jwt
import time
import requests

def generate_jwt(app_id: str, private_key: str) -> str:
    payload = {
        'iat': int(time.time()),
        'exp': int(time.time()) + 600,
        'iss': app_id
    }
    return jwt.encode(payload, private_key, algorithm='RS256')

def get_installation_token(jwt_token: str, installation_id: str) -> str:
    headers = {
        'Authorization': f'Bearer {jwt_token}',
        'Accept': 'application/vnd.github.v3+json'
    }
    response = requests.post(
        f'https://api.github.com/app/installations/{installation_id}/access_tokens',
        headers=headers
    )
    return response.json()['token']
```

3. **Check API key/token in secrets:**
```bash
# GitHub Actions secrets
gh secret list

# Kubernetes secrets
kubectl get secrets -n gemini
kubectl describe secret github-app-secrets -n gemini
```

4. **Validate private key format:**
```bash
# Check if private key is valid
openssl rsa -in github-app.pem -check

# Convert if needed
openssl pkcs8 -topk8 -inform PEM -outform PEM -nocrypt -in github-app.pem -out github-app-pkcs8.pem
```

#### Error: "Resource not accessible by integration"

**Symptoms:**
- Cannot access certain repositories
- Missing permissions errors
- Cannot read/write specific resources

**Solutions:**

1. **Check app permissions:**
```yaml
# Required permissions in GitHub App settings
permissions:
  actions: read
  checks: write
  contents: read
  issues: write
  pull_requests: write
  statuses: write
```

2. **Verify repository access:**
```bash
# Check if app is installed on repository
curl -H "Authorization: Bearer $(installation-token)" \
  https://api.github.com/installation/repositories
```

3. **Request additional permissions:**
```python
# Update app permissions programmatically
def request_permissions(installation_id: str, permissions: dict):
    # This triggers a permission request to repo admin
    pass
```

### Analysis Issues

#### Error: "Analysis timeout"

**Symptoms:**
- Analysis never completes
- GitHub Actions job times out
- No results after extended wait

**Solutions:**

1. **Increase timeout settings:**
```yaml
# GitHub Actions
jobs:
  analyze:
    timeout-minutes: 30  # Increase from default
    
# In code
gemini analyze --timeout 1800  # 30 minutes
```

2. **Check resource limits:**
```bash
# Docker
docker update --memory="2g" --cpus="2" gemini-server

# Kubernetes
kubectl edit deployment gemini-github-app -n gemini
# Update resources:
#   limits:
#     memory: "2Gi"
#     cpu: "2000m"
```

3. **Optimize analysis scope:**
```yaml
# .gemini/config.yml
analysis:
  max_file_size: 1048576  # 1MB
  exclude_patterns:
    - "*.min.js"
    - "vendor/*"
    - "node_modules/*"
  parallel_workers: 4
```

4. **Debug long-running analysis:**
```python
# debug_analysis.py
import cProfile
import pstats

def profile_analysis():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Run analysis
    result = gemini.analyze(repo_path)
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats(20)
```

#### Error: "No duplicates found" (when they exist)

**Symptoms:**
- Scout agent not detecting obvious duplicates
- False negatives in duplicate detection
- Inconsistent results

**Solutions:**

1. **Adjust similarity threshold:**
```python
# config/scout.yml
scout:
  duplicate_threshold: 0.7  # Lower from 0.8
  min_lines: 5  # Minimum lines to consider
  ignore_whitespace: true
  ignore_comments: true
```

2. **Clear Scout cache:**
```bash
# Clear Redis cache
redis-cli FLUSHDB

# Or specific keys
redis-cli --scan --pattern "scout:*" | xargs redis-cli DEL
```

3. **Rebuild Scout index:**
```python
# rebuild_index.py
from scout.indexer import ScoutIndexer

indexer = ScoutIndexer()
indexer.clear_index()
indexer.full_reindex('/path/to/repo')
```

4. **Debug similarity calculation:**
```python
# debug_similarity.py
from scout.similarity import calculate_similarity

code1 = """def hello(): print("hello")"""
code2 = """def hello(): print("hi")"""

similarity = calculate_similarity(code1, code2)
print(f"Similarity: {similarity}")
```

### Performance Issues

#### Slow webhook processing

**Symptoms:**
- Webhooks take > 30s to process
- GitHub shows timeout warnings
- Delayed PR feedback

**Solutions:**

1. **Enable async processing:**
```python
# webhook_handler.py
@app.post("/webhooks/github")
async def github_webhook(request: Request, background_tasks: BackgroundTasks):
    # Quick validation
    validate_signature(request)
    
    # Process async
    background_tasks.add_task(process_webhook, await request.json())
    
    # Return immediately
    return {"status": "accepted"}
```

2. **Implement caching:**
```python
# cache.py
from functools import lru_cache
import redis

class AnalysisCache:
    def __init__(self):
        self.redis = redis.Redis()
    
    async def get_or_compute(self, key: str, compute_func):
        # Check cache
        cached = await self.redis.get(key)
        if cached:
            return json.loads(cached)
        
        # Compute and cache
        result = await compute_func()
        await self.redis.setex(key, 3600, json.dumps(result))
        return result
```

3. **Optimize database queries:**
```python
# Use connection pooling
from sqlalchemy.pool import QueuePool

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,
    pool_size=20,
    max_overflow=40,
    pool_pre_ping=True
)

# Use bulk operations
session.bulk_insert_mappings(Model, data)
session.bulk_update_mappings(Model, updates)
```

4. **Profile performance:**
```python
# profile.py
import yappi

yappi.start()

# Run slow operation
process_webhook(webhook_data)

yappi.stop()
stats = yappi.get_func_stats()
stats.print_all()
```

#### High memory usage

**Symptoms:**
- OOMKilled pods
- Server crashes
- Gradual performance degradation

**Solutions:**

1. **Monitor memory usage:**
```python
# memory_monitor.py
import psutil
import gc

def check_memory():
    process = psutil.Process()
    mem_info = process.memory_info()
    
    print(f"RSS: {mem_info.rss / 1024 / 1024:.2f} MB")
    print(f"VMS: {mem_info.vms / 1024 / 1024:.2f} MB")
    
    # Force garbage collection
    gc.collect()
    
    # Check for memory leaks
    import tracemalloc
    tracemalloc.start()
    # ... run operations ...
    snapshot = tracemalloc.take_snapshot()
    top_stats = snapshot.statistics('lineno')
    for stat in top_stats[:10]:
        print(stat)
```

2. **Implement memory limits:**
```python
# limit_memory.py
import resource

# Set memory limit to 1GB
resource.setrlimit(resource.RLIMIT_AS, (1024 * 1024 * 1024, -1))
```

3. **Use streaming for large files:**
```python
# stream_processing.py
async def process_large_file(file_path: str):
    async with aiofiles.open(file_path, 'r') as f:
        async for line in f:
            # Process line by line
            await process_line(line)
```

### Rate Limiting Issues

#### Error: "API rate limit exceeded"

**Symptoms:**
- 403 errors from GitHub API
- "Rate limit exceeded" messages
- Analysis stops working

**Solutions:**

1. **Check current rate limit:**
```bash
curl -H "Authorization: token YOUR_TOKEN" \
  https://api.github.com/rate_limit
```

2. **Implement rate limit handling:**
```python
# rate_limiter.py
import time
from typing import Optional

class GitHubRateLimiter:
    def __init__(self):
        self.remaining = 5000
        self.reset_time = 0
    
    async def wait_if_needed(self):
        if self.remaining < 10:
            wait_time = self.reset_time - time.time()
            if wait_time > 0:
                print(f"Rate limited. Waiting {wait_time}s")
                await asyncio.sleep(wait_time)
    
    def update_from_headers(self, headers):
        self.remaining = int(headers.get('X-RateLimit-Remaining', 5000))
        self.reset_time = int(headers.get('X-RateLimit-Reset', 0))
```

3. **Use conditional requests:**
```python
# conditional_requests.py
async def fetch_with_etag(url: str, etag: Optional[str] = None):
    headers = {}
    if etag:
        headers['If-None-Match'] = etag
    
    response = await session.get(url, headers=headers)
    
    if response.status == 304:  # Not Modified
        return None  # Use cached version
    
    return response.json(), response.headers.get('ETag')
```

4. **Implement request batching:**
```python
# batch_requests.py
async def batch_github_requests(requests: List[dict]):
    # Use GraphQL to batch multiple queries
    query = """
    query {
        repository(owner: "%s", name: "%s") {
            pullRequests(first: 100) {
                nodes { number title state }
            }
        }
    }
    """
    
    # Single request instead of multiple
    return await github_graphql(query)
```

## Debug Mode

### Enable debug logging

```python
# Set environment variables
import os
os.environ['GEMINI_DEBUG'] = 'true'
os.environ['LOG_LEVEL'] = 'DEBUG'

# Configure logging
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug.log'),
        logging.StreamHandler()
    ]
)

# Add request/response logging
import httpx

class LoggingTransport(httpx.HTTPTransport):
    def handle_request(self, request):
        print(f"Request: {request.method} {request.url}")
        print(f"Headers: {request.headers}")
        print(f"Body: {request.content[:200]}")
        response = super().handle_request(request)
        print(f"Response: {response.status_code}")
        return response
```

### Trace webhook processing

```python
# trace_webhook.py
import sys
import trace

tracer = trace.Trace(
    count=False,
    trace=True,
    tracedirs=[sys.prefix, sys.exec_prefix]
)

tracer.run('process_webhook(payload)')
```

### Debug GitHub Actions

```yaml
# Enable debug logging in workflow
name: Debug Analysis

on:
  workflow_dispatch:

env:
  ACTIONS_STEP_DEBUG: true
  ACTIONS_RUNNER_DEBUG: true

jobs:
  debug:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Debug Environment
        run: |
          echo "GitHub Context:"
          echo '${{ toJSON(github) }}'
          
          echo "Environment Variables:"
          env | sort
          
          echo "Network Configuration:"
          ip addr
          netstat -tuln
          
      - name: Test Gemini Connection
        run: |
          curl -v https://api.gemini-architect.example.com/health
          
      - name: Run Analysis with Debug
        run: |
          gemini --debug analyze \
            --verbose \
            --log-file debug.log
          
          echo "Debug Log:"
          cat debug.log
```

## Local Development Setup

### Run Gemini locally for testing

```bash
# 1. Clone repository
git clone https://github.com/your-org/gemini-cli.git
cd gemini-cli

# 2. Set up environment
python -m venv venv
source venv/bin/activate
pip install -r requirements-dev.txt

# 3. Configure local environment
cp .env.example .env.local
# Edit .env.local with your settings

# 4. Run local server
uvicorn app.main:app --reload --port 8000

# 5. Set up ngrok for webhook testing
ngrok http 8000
# Update GitHub webhook URL to ngrok URL

# 6. Test webhook locally
python test_webhook.py
```

### Integration testing

```python
# test_integration.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_webhook_ping():
    response = client.post(
        "/webhooks/github",
        json={"zen": "Design for failure."},
        headers={
            "X-GitHub-Event": "ping",
            "X-Hub-Signature-256": "sha256=test"
        }
    )
    assert response.status_code == 202

def test_pr_analysis():
    with open("fixtures/pr_opened.json") as f:
        payload = json.load(f)
    
    response = client.post(
        "/webhooks/github",
        json=payload,
        headers={
            "X-GitHub-Event": "pull_request",
            "X-Hub-Signature-256": generate_signature(payload)
        }
    )
    assert response.status_code == 202
```

## Performance Tuning

### Optimize webhook processing

```python
# optimizations.py

# 1. Use connection pooling
import aiohttp
connector = aiohttp.TCPConnector(
    limit=100,
    limit_per_host=30,
    ttl_dns_cache=300
)
session = aiohttp.ClientSession(connector=connector)

# 2. Implement circuit breaker
from circuit_breaker import CircuitBreaker

github_api = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=60,
    expected_exception=aiohttp.ClientError
)

@github_api
async def call_github_api(url):
    async with session.get(url) as response:
        return await response.json()

# 3. Use Redis for caching
import redis
import pickle

cache = redis.Redis(decode_responses=False)

def cached(ttl=3600):
    def decorator(func):
        async def wrapper(*args, **kwargs):
            key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Try cache
            cached_result = cache.get(key)
            if cached_result:
                return pickle.loads(cached_result)
            
            # Compute and cache
            result = await func(*args, **kwargs)
            cache.setex(key, ttl, pickle.dumps(result))
            return result
        return wrapper
    return decorator

# 4. Batch database operations
from sqlalchemy.ext.asyncio import AsyncSession

async def bulk_save(session: AsyncSession, objects: list):
    session.add_all(objects)
    await session.commit()
```

### Scale horizontally

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: gemini-app-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: gemini-github-app
  minReplicas: 2
  maxReplicas: 10
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: webhook_queue_depth
      target:
        type: AverageValue
        averageValue: "30"
```

## Emergency Recovery

### Rollback deployment

```bash
#!/bin/bash
# rollback.sh

# Get previous version
PREVIOUS_VERSION=$(kubectl rollout history deployment/gemini-github-app -n gemini | tail -2 | head -1 | awk '{print $1}')

# Rollback
kubectl rollout undo deployment/gemini-github-app -n gemini --to-revision=$PREVIOUS_VERSION

# Wait for rollout
kubectl rollout status deployment/gemini-github-app -n gemini

# Verify health
curl https://api.gemini-architect.example.com/health
```

### Clear stuck webhooks

```python
# clear_webhooks.py
import redis
import asyncio

async def clear_stuck_webhooks():
    r = redis.Redis()
    
    # Get all webhook keys
    webhook_keys = r.keys("webhook:*")
    
    for key in webhook_keys:
        data = r.get(key)
        webhook = json.loads(data)
        
        # Check if stuck (older than 1 hour)
        if time.time() - webhook['timestamp'] > 3600:
            print(f"Clearing stuck webhook: {key}")
            r.delete(key)
    
    # Clear processing flags
    r.delete("webhook:processing:*")

asyncio.run(clear_stuck_webhooks())
```

### Recover from data corruption

```bash
#!/bin/bash
# recover.sh

# 1. Stop services
kubectl scale deployment gemini-github-app --replicas=0 -n gemini

# 2. Backup current state
pg_dump -h localhost -d gemini > backup_$(date +%s).sql

# 3. Restore from last known good backup
psql -h localhost -d gemini < last_good_backup.sql

# 4. Clear Redis cache
redis-cli FLUSHALL

# 5. Rebuild indexes
python rebuild_indexes.py

# 6. Restart services
kubectl scale deployment gemini-github-app --replicas=3 -n gemini

# 7. Verify
python verify_integrity.py
```

## Monitoring Scripts

### Health check script

```bash
#!/bin/bash
# healthcheck.sh

ENDPOINTS=(
  "https://api.gemini-architect.example.com/health"
  "https://api.gemini-architect.example.com/ready"
  "https://api.gemini-architect.example.com/metrics"
)

for endpoint in "${ENDPOINTS[@]}"; do
  response=$(curl -s -o /dev/null -w "%{http_code}" $endpoint)
  if [ $response -eq 200 ]; then
    echo "✅ $endpoint is healthy"
  else
    echo "❌ $endpoint is unhealthy (HTTP $response)"
  fi
done
```

### Performance monitoring

```python
# monitor_performance.py
import asyncio
import time
import statistics

async def monitor_webhook_performance():
    response_times = []
    
    for _ in range(100):
        start = time.time()
        
        # Make test request
        response = await make_webhook_request()
        
        duration = time.time() - start
        response_times.append(duration)
        
        await asyncio.sleep(1)
    
    print(f"Average: {statistics.mean(response_times):.3f}s")
    print(f"Median: {statistics.median(response_times):.3f}s")
    print(f"P95: {statistics.quantiles(response_times, n=20)[18]:.3f}s")
    print(f"P99: {statistics.quantiles(response_times, n=100)[98]:.3f}s")

asyncio.run(monitor_webhook_performance())
```