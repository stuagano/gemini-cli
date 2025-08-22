"""
API Usage Examples
Comprehensive examples for using the Gemini CLI Enterprise Architect API
"""

import asyncio
import aiohttp
import json
import websockets
from typing import Dict, Any, Optional
from datetime import datetime

class GeminiAPIClient:
    """Python client for Gemini CLI API with comprehensive examples"""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.access_token = None
        self.session = None
    
    async def __aenter__(self):
        """Async context manager entry"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.close()
    
    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with authentication"""
        headers = {"Content-Type": "application/json"}
        
        if self.access_token:
            headers["Authorization"] = f"Bearer {self.access_token}"
        elif self.api_key:
            headers["X-API-Key"] = self.api_key
        
        return headers
    
    async def authenticate(self, username: str, password: str) -> Dict[str, Any]:
        """Authenticate with username/password and get access token"""
        login_data = {
            "username": username,
            "password": password
        }
        
        async with self.session.post(
            f"{self.base_url}/api/v1/auth/login",
            json=login_data
        ) as response:
            if response.status == 200:
                result = await response.json()
                self.access_token = result["access_token"]
                return result
            else:
                error = await response.text()
                raise Exception(f"Authentication failed: {error}")
    
    async def get_current_user(self) -> Dict[str, Any]:
        """Get current user information"""
        async with self.session.get(
            f"{self.base_url}/api/v1/auth/me",
            headers=self._get_headers()
        ) as response:
            response.raise_for_status()
            return await response.json()

# Authentication Examples
async def example_authentication():
    """Example: Authentication flow"""
    print("=== Authentication Example ===")
    
    async with GeminiAPIClient() as client:
        try:
            # Login with credentials
            auth_result = await client.authenticate("user@example.com", "password123")
            print(f"✅ Login successful: {auth_result['user']['username']}")
            print(f"   Token expires in: {auth_result['expires_in']} seconds")
            
            # Get current user info
            user_info = await client.get_current_user()
            print(f"✅ User info: {user_info['full_name']} ({user_info['role']})")
            print(f"   Permissions: {user_info['permissions']}")
            
        except Exception as e:
            print(f"❌ Authentication failed: {e}")

async def example_api_key_usage():
    """Example: Using API keys for authentication"""
    print("\n=== API Key Authentication Example ===")
    
    api_key = "gek_your_api_key_here"  # Replace with actual API key
    
    async with GeminiAPIClient(api_key=api_key) as client:
        try:
            user_info = await client.get_current_user()
            print(f"✅ API key authentication successful")
            print(f"   User: {user_info['username']}")
            
        except Exception as e:
            print(f"❌ API key authentication failed: {e}")

# AI Agent Examples
async def example_agent_request():
    """Example: Single agent request"""
    print("\n=== AI Agent Request Example ===")
    
    async with GeminiAPIClient() as client:
        await client.authenticate("user@example.com", "password123")
        
        # Architecture design request
        agent_request = {
            "type": "architect",
            "action": "design_system",
            "payload": {
                "requirements": "Design a microservices architecture for e-commerce platform",
                "constraints": ["cloud-native", "scalable", "secure", "cost-effective"],
                "scale": "medium"
            },
            "context": {
                "project_type": "ecommerce",
                "team_size": "10-15 developers",
                "timeline": "6 months"
            },
            "timeout": 60
        }
        
        try:
            async with client.session.post(
                f"{client.base_url}/api/v1/agent/request",
                json=agent_request,
                headers=client._get_headers()
            ) as response:
                response.raise_for_status()
                result = await response.json()
                
                print(f"✅ Agent request successful")
                print(f"   Agent: {result['metadata']['agent']}")
                print(f"   Response time: {result['metadata']['response_time']:.2f}s")
                print(f"   Result preview: {str(result['result'])[:200]}...")
                
        except Exception as e:
            print(f"❌ Agent request failed: {e}")

async def example_batch_agent_requests():
    """Example: Batch agent requests"""
    print("\n=== Batch Agent Requests Example ===")
    
    async with GeminiAPIClient() as client:
        await client.authenticate("user@example.com", "password123")
        
        # Multiple requests to different agents
        batch_requests = [
            {
                "type": "analyst",
                "action": "analyze_requirements",
                "payload": {"requirements": "User authentication system"}
            },
            {
                "type": "architect", 
                "action": "design_api",
                "payload": {"requirements": "REST API for user management"}
            },
            {
                "type": "developer",
                "action": "estimate_effort",
                "payload": {"features": ["login", "registration", "password reset"]}
            }
        ]
        
        try:
            async with client.session.post(
                f"{client.base_url}/api/v1/agent/batch",
                json=batch_requests,
                headers=client._get_headers()
            ) as response:
                response.raise_for_status()
                results = await response.json()
                
                print(f"✅ Batch request completed: {len(results)} responses")
                for i, result in enumerate(results):
                    status = "✅" if result['success'] else "❌"
                    agent_type = batch_requests[i]['type']
                    print(f"   {status} {agent_type}: {result.get('result', result.get('error', {})).get('message', 'OK')}")
                
        except Exception as e:
            print(f"❌ Batch request failed: {e}")

async def example_websocket_streaming():
    """Example: WebSocket streaming responses"""
    print("\n=== WebSocket Streaming Example ===")
    
    ws_url = "ws://localhost:8000/ws/agent/stream"
    
    try:
        async with websockets.connect(ws_url) as websocket:
            # Initialize connection
            await websocket.send(json.dumps({"type": "init"}))
            response = await websocket.recv()
            init_data = json.loads(response)
            print(f"✅ WebSocket connected: {init_data['sessionId']}")
            
            # Send streaming request
            stream_request = {
                "type": "stream_request",
                "request": {
                    "type": "developer",
                    "action": "code_review",
                    "payload": {
                        "code": """
def calculate_total(items):
    total = 0
    for item in items:
        total += item.price * item.quantity
    return total
                        """,
                        "language": "python"
                    }
                }
            }
            
            await websocket.send(json.dumps(stream_request))
            print("📤 Sent streaming request")
            
            # Receive streaming responses
            while True:
                response = await websocket.recv()
                data = json.loads(response)
                
                if data['type'] == 'stream_chunk':
                    print(f"📥 Chunk: {data['data'][:100]}...")
                elif data['type'] == 'stream_complete':
                    print("✅ Streaming complete")
                    break
                elif data['type'] == 'error':
                    print(f"❌ Stream error: {data['error']}")
                    break
    
    except Exception as e:
        print(f"❌ WebSocket failed: {e}")

# Security Scanning Examples
async def example_security_scan():
    """Example: Security vulnerability scanning"""
    print("\n=== Security Scanning Example ===")
    
    async with GeminiAPIClient() as client:
        await client.authenticate("admin@example.com", "admin123")
        
        scan_request = {
            "target": "/path/to/project",
            "scan_types": ["dependencies", "code", "secrets", "docker"]
        }
        
        try:
            async with client.session.post(
                f"{client.base_url}/api/v1/security/scan",
                json=scan_request,
                headers=client._get_headers()
            ) as response:
                response.raise_for_status()
                result = await response.json()
                
                print(f"✅ Security scan completed")
                print(f"   Scan ID: {result['scan_id']}")
                print(f"   Risk Score: {result['risk_score']}/100")
                print(f"   Duration: {result['scan_duration']:.2f}s")
                print(f"   Findings: {result['summary']}")
                
                # Show critical findings
                critical_findings = [f for f in result['findings'] if f['severity'] == 'critical']
                if critical_findings:
                    print(f"🚨 Critical findings:")
                    for finding in critical_findings[:3]:
                        print(f"   - {finding['title']}")
                
        except Exception as e:
            print(f"❌ Security scan failed: {e}")

async def example_compliance_report():
    """Example: Get compliance report"""
    print("\n=== Compliance Report Example ===")
    
    async with GeminiAPIClient() as client:
        await client.authenticate("admin@example.com", "admin123")
        
        try:
            async with client.session.get(
                f"{client.base_url}/api/v1/security/compliance/report?framework=owasp",
                headers=client._get_headers()
            ) as response:
                response.raise_for_status()
                result = await response.json()
                
                print(f"✅ OWASP Compliance Report")
                print(f"   Overall Score: {result['overall_score']}/100")
                print(f"   Status: {result['compliance_level']}")
                print(f"   Categories:")
                
                for category in result['categories']:
                    status_icon = "✅" if category['status'] == "Compliant" else "⚠️"
                    print(f"   {status_icon} {category['name']}: {category['score']}/100")
                
        except Exception as e:
            print(f"❌ Compliance report failed: {e}")

# Monitoring Examples
async def example_dora_metrics():
    """Example: Get DORA metrics"""
    print("\n=== DORA Metrics Example ===")
    
    async with GeminiAPIClient() as client:
        await client.authenticate("user@example.com", "password123")
        
        try:
            async with client.session.get(
                f"{client.base_url}/api/v1/monitoring/dora?days=30",
                headers=client._get_headers()
            ) as response:
                response.raise_for_status()
                result = await response.json()
                
                print(f"✅ DORA Metrics (30 days)")
                print(f"   Deployment Frequency: {result['deployment_frequency']:.1f} deploys/day")
                print(f"   Lead Time for Changes: {result['lead_time_for_changes']:.1f} hours")
                print(f"   Mean Time to Recovery: {result['mean_time_to_recovery']:.1f} hours")
                print(f"   Change Failure Rate: {result['change_failure_rate']:.1f}%")
                
        except Exception as e:
            print(f"❌ DORA metrics failed: {e}")

async def example_performance_metrics():
    """Example: Get performance metrics"""
    print("\n=== Performance Metrics Example ===")
    
    async with GeminiAPIClient() as client:
        await client.authenticate("user@example.com", "password123")
        
        try:
            async with client.session.get(
                f"{client.base_url}/api/v1/monitoring/performance",
                headers=client._get_headers()
            ) as response:
                response.raise_for_status()
                result = await response.json()
                
                print(f"✅ Performance Metrics")
                print(f"   Response Time P95: {result['response_time_p95']:.1f}ms")
                print(f"   Requests/Second: {result['requests_per_second']:.1f}")
                print(f"   Error Rate: {result['error_rate']:.2f}%")
                print(f"   CPU Usage: {result['cpu_usage']:.1f}%")
                print(f"   Memory Usage: {result['memory_usage']:.1f}%")
                
        except Exception as e:
            print(f"❌ Performance metrics failed: {e}")

async def example_dashboard_summary():
    """Example: Get dashboard summary"""
    print("\n=== Dashboard Summary Example ===")
    
    async with GeminiAPIClient() as client:
        await client.authenticate("user@example.com", "password123")
        
        try:
            async with client.session.get(
                f"{client.base_url}/api/v1/monitoring/dashboard/summary",
                headers=client._get_headers()
            ) as response:
                response.raise_for_status()
                result = await response.json()
                
                print(f"✅ Dashboard Summary")
                print(f"   System Status: {result['system_status']}")
                print(f"   Timestamp: {result['timestamp']}")
                
                dora = result['dora_metrics']
                perf = result['performance_metrics']
                
                print(f"   📊 Key Metrics:")
                print(f"      Deployments: {dora['deployment_frequency']:.1f}/day")
                print(f"      Response Time: {perf['response_time_p95']:.0f}ms")
                print(f"      Error Rate: {perf['error_rate']:.2f}%")
                
        except Exception as e:
            print(f"❌ Dashboard summary failed: {e}")

# Document Search Examples
async def example_document_search():
    """Example: RAG document search"""
    print("\n=== Document Search Example ===")
    
    async with GeminiAPIClient() as client:
        await client.authenticate("user@example.com", "password123")
        
        search_request = {
            "query": "authentication best practices JWT security",
            "filters": {
                "file_type": "markdown",
                "tags": ["security", "authentication"]
            },
            "limit": 5
        }
        
        try:
            async with client.session.post(
                f"{client.base_url}/api/v1/rag/search",
                json=search_request,
                headers=client._get_headers()
            ) as response:
                response.raise_for_status()
                result = await response.json()
                
                print(f"✅ Document search completed")
                print(f"   Query: {result['query']}")
                print(f"   Results: {result['total']} documents found")
                
                for i, item in enumerate(result['results'][:3], 1):
                    doc = item['document']
                    print(f"   {i}. {doc['title']} (score: {item['score']:.2f})")
                    print(f"      File: {doc['metadata']['file_name']}")
                    print(f"      Highlights: {', '.join(item['highlights'][:2])}")
                
        except Exception as e:
            print(f"❌ Document search failed: {e}")

# Error Handling Examples
async def example_error_handling():
    """Example: Proper error handling"""
    print("\n=== Error Handling Example ===")
    
    async with GeminiAPIClient() as client:
        # Example: Authentication error
        try:
            await client.authenticate("invalid@example.com", "wrongpassword")
        except Exception as e:
            print(f"Expected auth error: {e}")
        
        # Example: Invalid agent request
        await client.authenticate("user@example.com", "password123")
        
        invalid_request = {
            "type": "nonexistent_agent",
            "action": "invalid_action",
            "payload": {}
        }
        
        try:
            async with client.session.post(
                f"{client.base_url}/api/v1/agent/request",
                json=invalid_request,
                headers=client._get_headers()
            ) as response:
                if response.status != 200:
                    error_data = await response.json()
                    print(f"Expected API error: {error_data['error']['message']}")
                
        except Exception as e:
            print(f"Request error: {e}")

# Health Check Examples
async def example_health_checks():
    """Example: System health monitoring"""
    print("\n=== Health Check Example ===")
    
    async with GeminiAPIClient() as client:
        try:
            # Basic health check
            async with client.session.get(f"{client.base_url}/health") as response:
                response.raise_for_status()
                result = await response.json()
                print(f"✅ System Health: {result['status']}")
                print(f"   Uptime: {result.get('uptime', 0):.0f} seconds")
                print(f"   Version: {result.get('version', 'Unknown')}")
            
            # Detailed health (requires auth)
            await client.authenticate("user@example.com", "password123")
            
            async with client.session.get(
                f"{client.base_url}/api/v1/monitoring/health/detailed",
                headers=client._get_headers()
            ) as response:
                response.raise_for_status()
                result = await response.json()
                print(f"✅ Detailed Health: {result['status']}")
                
                for component, status in result['components'].items():
                    icon = "✅" if status == "healthy" else "❌"
                    print(f"   {icon} {component}: {status}")
                
        except Exception as e:
            print(f"❌ Health check failed: {e}")

# Rate Limiting Example
async def example_rate_limiting():
    """Example: Handle rate limiting"""
    print("\n=== Rate Limiting Example ===")
    
    async with GeminiAPIClient() as client:
        await client.authenticate("user@example.com", "password123")
        
        # Make multiple rapid requests to trigger rate limiting
        for i in range(5):
            try:
                async with client.session.get(
                    f"{client.base_url}/api/v1/auth/me",
                    headers=client._get_headers()
                ) as response:
                    if response.status == 429:
                        # Rate limited
                        retry_after = response.headers.get('Retry-After', '60')
                        rate_limit = response.headers.get('X-RateLimit-Limit', 'Unknown')
                        remaining = response.headers.get('X-RateLimit-Remaining', 'Unknown')
                        
                        print(f"⚠️ Rate limited (attempt {i+1})")
                        print(f"   Limit: {rate_limit} requests")
                        print(f"   Remaining: {remaining}")
                        print(f"   Retry after: {retry_after} seconds")
                        break
                    else:
                        remaining = response.headers.get('X-RateLimit-Remaining', 'Unknown')
                        print(f"✅ Request {i+1} successful (remaining: {remaining})")
                        
            except Exception as e:
                print(f"❌ Request {i+1} failed: {e}")

# Main execution function
async def run_all_examples():
    """Run all API examples"""
    print("🚀 Gemini CLI API Examples")
    print("=" * 50)
    
    examples = [
        example_authentication,
        example_api_key_usage,
        example_agent_request,
        example_batch_agent_requests,
        example_websocket_streaming,
        example_security_scan,
        example_compliance_report,
        example_dora_metrics,
        example_performance_metrics,
        example_dashboard_summary,
        example_document_search,
        example_error_handling,
        example_health_checks,
        example_rate_limiting
    ]
    
    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"❌ Example {example.__name__} failed: {e}")
        finally:
            await asyncio.sleep(1)  # Brief pause between examples
    
    print("\n✅ All examples completed!")

if __name__ == "__main__":
    # Run examples
    asyncio.run(run_all_examples())