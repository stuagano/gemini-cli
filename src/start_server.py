#!/usr/bin/env python3
"""
Startup script for BMAD Agent Server
Run this to start the FastAPI server with all agents
"""

import sys
import os
import logging
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent
sys.path.insert(0, str(src_path))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def main():
    """Main entry point"""
    try:
        import uvicorn
        from api.agent_server import app
        
        logger.info("Starting BMAD Agent Server...")
        logger.info("Server will be available at http://localhost:8000")
        logger.info("API documentation at http://localhost:8000/docs")
        logger.info("WebSocket endpoint at ws://localhost:8000/ws/agent/stream")
        
        # Run server
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=8000,
            reload=True,
            log_level="info"
        )
        
    except ImportError as e:
        logger.error(f"Missing dependency: {e}")
        logger.error("Please install requirements: pip install -r requirements.txt")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Failed to start server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()