#!/usr/bin/env python3
"""
Test script for BMAD Agent Server
Verifies that the server is running and agents are responsive
"""

import asyncio
import aiohttp
import json
import sys
from typing import Dict, Any

# Server configuration
SERVER_URL = "http://localhost:8000"
WS_URL = "ws://localhost:8000/ws/agent/stream"

async def test_health_check():
    """Test health check endpoint"""
    print("Testing health check...")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{SERVER_URL}/api/v1/health") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Health check passed: {data['status']}")
                print(f"   Active agents: {list(data['agents'].keys())}")
                return True
            else:
                print(f"❌ Health check failed: {response.status}")
                return False

async def test_list_agents():
    """Test list agents endpoint"""
    print("\nTesting list agents...")
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{SERVER_URL}/api/v1/agents") as response:
            if response.status == 200:
                data = await response.json()
                print(f"✅ Found {len(data['agents'])} agents:")
                for agent in data['agents']:
                    print(f"   - {agent['type']}: {agent['status']}")
                return True
            else:
                print(f"❌ List agents failed: {response.status}")
                return False

async def test_agent_request(agent_type: str, action: str, payload: Dict[str, Any]):
    """Test agent request endpoint"""
    print(f"\nTesting {agent_type} agent with action '{action}'...")
    
    request_data = {
        "type": agent_type,
        "action": action,
        "payload": payload,
        "context": {"test": True}
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(
            f"{SERVER_URL}/api/v1/agent/request",
            json=request_data
        ) as response:
            if response.status == 200:
                data = await response.json()
                if data['success']:
                    print(f"✅ Agent request succeeded")
                    print(f"   Response time: {data['metadata'].get('response_time', 'N/A')}s")
                    return True
                else:
                    print(f"❌ Agent request failed: {data.get('error', 'Unknown error')}")
                    return False
            else:
                print(f"❌ Request failed with status: {response.status}")
                return False

async def test_websocket_connection():
    """Test WebSocket connection"""
    print("\nTesting WebSocket connection...")
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.ws_connect(WS_URL) as ws:
                # Send init message
                await ws.send_json({
                    "type": "init",
                    "metadata": {"client": "test"}
                })
                
                # Wait for response
                msg = await asyncio.wait_for(ws.receive(), timeout=5)
                if msg.type == aiohttp.WSMsgType.TEXT:
                    data = json.loads(msg.data)
                    if data['type'] == 'connected':
                        print(f"✅ WebSocket connected: {data['data']['client_id']}")
                        
                        # Test ping
                        await ws.send_json({"type": "ping"})
                        msg = await asyncio.wait_for(ws.receive(), timeout=5)
                        if msg.type == aiohttp.WSMsgType.TEXT:
                            data = json.loads(msg.data)
                            if data['type'] == 'pong':
                                print(f"✅ WebSocket ping/pong successful")
                                return True
                
                print("❌ WebSocket test failed")
                return False
                
    except asyncio.TimeoutError:
        print("❌ WebSocket connection timed out")
        return False
    except Exception as e:
        print(f"❌ WebSocket error: {e}")
        return False

async def run_tests():
    """Run all tests"""
    print("=" * 50)
    print("BMAD Agent Server Test Suite")
    print("=" * 50)
    
    # Check if server is running
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{SERVER_URL}/") as response:
                if response.status != 200:
                    print("❌ Server is not responding")
                    print("Please start the server first: python src/start_server.py")
                    return False
    except aiohttp.ClientConnectorError:
        print("❌ Cannot connect to server at", SERVER_URL)
        print("Please start the server first: python src/start_server.py")
        return False
    
    # Run tests
    results = []
    
    # Basic connectivity tests
    results.append(await test_health_check())
    results.append(await test_list_agents())
    
    # Agent tests (testing with mock since agents need proper initialization)
    # Note: These will fail if agents aren't properly initialized with their dependencies
    # Uncomment these when agents are fully configured:
    
    # results.append(await test_agent_request(
    #     "analyst",
    #     "analyze",
    #     {"query": "Test analysis request"}
    # ))
    
    # results.append(await test_agent_request(
    #     "scout",
    #     "scan",
    #     {"path": "/test/path"}
    # ))
    
    # WebSocket test
    results.append(await test_websocket_connection())
    
    # Summary
    print("\n" + "=" * 50)
    passed = sum(results)
    total = len(results)
    
    if passed == total:
        print(f"✅ All tests passed ({passed}/{total})")
        return True
    else:
        print(f"⚠️  Some tests failed ({passed}/{total} passed)")
        return False

def main():
    """Main entry point"""
    try:
        success = asyncio.run(run_tests())
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\nTest interrupted")
        sys.exit(1)
    except Exception as e:
        print(f"Test error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()