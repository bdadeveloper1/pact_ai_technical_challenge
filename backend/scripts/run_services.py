#!/usr/bin/env python3
"""
Script to run both FastAPI and gRPC services
"""

import subprocess
import sys
import time
import signal
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_fastapi():
    """Run FastAPI server"""
    backend_dir = Path(__file__).parent.parent
    
    cmd = [
        sys.executable, "-m", "uvicorn",
        "app.main:app",
        "--host", "0.0.0.0",
        "--port", "8000",
        "--reload"
    ]
    
    logger.info("Starting FastAPI server on http://localhost:8000")
    
    try:
        return subprocess.run(cmd, cwd=backend_dir)
    except KeyboardInterrupt:
        logger.info("FastAPI server stopped")
        return None

def run_grpc_server():
    """Run gRPC server"""
    backend_dir = Path(__file__).parent.parent
    
    cmd = [
        sys.executable, "-m", "app.grpc_server"
    ]
    
    logger.info("Starting gRPC server on localhost:50051")
    
    try:
        return subprocess.run(cmd, cwd=backend_dir)
    except KeyboardInterrupt:
        logger.info("gRPC server stopped")
        return None

def main():
    """Run both services"""
    logger.info("Starting EHR backend services...")
    
    # Check if generated gRPC code exists
    backend_dir = Path(__file__).parent.parent
    generated_dir = backend_dir / "generated"
    
    if not generated_dir.exists() or not list(generated_dir.glob("*_pb2.py")):
        logger.info("gRPC code not found. Generating...")
        generate_script = backend_dir / "scripts" / "generate_grpc.py"
        subprocess.run([sys.executable, str(generate_script)])
    
    # Run services in parallel
    with ThreadPoolExecutor(max_workers=2) as executor:
        try:
            # Submit both services
            fastapi_future = executor.submit(run_fastapi)
            grpc_future = executor.submit(run_grpc_server)
            
            # Wait for both to complete
            fastapi_future.result()
            grpc_future.result()
            
        except KeyboardInterrupt:
            logger.info("Shutting down services...")
            executor.shutdown(wait=False)
            
    logger.info("All services stopped")

if __name__ == "__main__":
    main()
