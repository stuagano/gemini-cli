"""
Test script for the BMAD Agent Server
Tests REST endpoints and WebSocket functionality
"""

import asyncio
import aiohttp
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"

async def test_health_check():
    """Test health check endpoint"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/api/v1/health") as response:
            data = await response.json()
            print(f"✅ Health Check: {data['status']}")
            print(f"   Agents: {data['agents']}")
            return response.status == 200

async def test_list_agents():
    """Test listing all agents"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/api/v1/agents") as response:
            data = await response.json()
            print(f"✅ Available Agents:")
            for agent in data['agents']:
                print(f"   - {agent['type']}: {agent['status']}")
            return response.status == 200

async def test_agent_request():
    """Test single agent request"""
    request_data = {
        "type": "analyst",
        "action": "analyze",
        "payload": {
            "query": "What are the main components of this system?",
            "context": "Testing the agent server"
        },
        "timeout": 30
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{BASE_URL}/api/v1/agent/request",
            json=request_data
        ) as response:
            data = await response.json()
            print(f"✅ Agent Request:")
            print(f"   Success: {data.get('success', False)}")
            print(f"   Request ID: {data.get('id', 'N/A')}")
            if data.get('result'):
                print(f"   Result: {str(data['result'])[:100]}...")
            return response.status == 200

async def test_websocket_connection():
    """Test WebSocket streaming"""
    import websockets
    
    try:
        uri = "ws://localhost:8000/ws/agent/stream"
        async with websockets.connect(uri) as websocket:
            # Send init message
            await websocket.send(json.dumps({
                "type": "init"
            }))
            
            # Receive connection confirmation
            response = await websocket.recv()
            data = json.loads(response)
            print(f"✅ WebSocket Connected:")
            print(f"   Session ID: {data.get('sessionId', 'N/A')}")
            
            # Send a streaming request
            await websocket.send(json.dumps({
                "type": "stream_request",
                "request": {
                    "type": "developer",
                    "action": "generate_code",
                    "payload": {
                        "specification": "Create a simple hello world function"
                    }
                }
            }))
            
            # Receive streaming chunks
            chunks_received = 0
            while True:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                    data = json.loads(response)
                    
                    if data['type'] == 'stream_chunk':
                        chunks_received += 1
                        print(f"   Received chunk {chunks_received}")
                    elif data['type'] == 'stream_complete':
                        print(f"   Stream completed. Total chunks: {chunks_received}")
                        break
                    elif data['type'] == 'error':
                        print(f"   Error: {data.get('error', 'Unknown error')}")
                        break
                        
                except asyncio.TimeoutError:
                    print("   Timeout waiting for response")
                    break
            
            return True
            
    except Exception as e:
        print(f"❌ WebSocket Error: {e}")
        return False

async def test_scout_stats():
    """Test Scout indexer statistics"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/api/v1/scout/stats") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Scout Stats:")
                print(f"   Files indexed: {data.get('files_indexed', 0)}")
                print(f"   Functions found: {data.get('functions_found', 0)}")
                return True
            elif response.status == 503:
                print("⚠️  Scout indexer not available (expected if not initialized)")
                return True
            else:
                print(f"❌ Scout Stats Error: {response.status}")
                return False

async def test_metrics():
    """Test system metrics endpoint"""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/api/v1/metrics") as response:
            data = await response.json()
            print(f"✅ System Metrics:")
            print(f"   Total Requests: {data.get('total_requests', 0)}")
            print(f"   Active Requests: {data.get('active_requests', 0)}")
            print(f"   Memory Usage: {data.get('memory_usage', 0):.2f} MB")
            return response.status == 200

async def run_all_tests():
    """Run all tests"""
    print("="*50)
    print("BMAD Agent Server Test Suite")
    print("="*50)
    print(f"Testing server at: {BASE_URL}")
    print(f"Started at: {datetime.now().isoformat()}")
    print("-"*50)
    
    tests = [
        ("Health Check", test_health_check),
        ("List Agents", test_list_agents),
        ("Agent Request", test_agent_request),
        ("Scout Stats", test_scout_stats),
        ("System Metrics", test_metrics),
        ("WebSocket Streaming", test_websocket_connection),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\nRunning: {test_name}")
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ Test failed with error: {e}")
            results.append((test_name, False))
        print("-"*50)
    
    # Summary
    print("\n" + "="*50)
    print("TEST SUMMARY")
    print("="*50)
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status}: {test_name}")
    
    print("-"*50)
    print(f"Results: {passed}/{total} tests passed")
    print("="*50)
    
    return passed == total

if __name__ == "__main__":
    # Run the test suite
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)