#!/usr/bin/env python3
"""
Script to generate gRPC Python code from proto files
"""

import subprocess
import os
import sys
from pathlib import Path

def generate_grpc_code():
    """Generate gRPC Python code from proto files"""
    
    # Get project directories
    backend_dir = Path(__file__).parent.parent
    proto_dir = backend_dir / "protos"
    generated_dir = backend_dir / "generated"
    
    # Create generated directory
    generated_dir.mkdir(exist_ok=True)
    
    # Create __init__.py file
    (generated_dir / "__init__.py").touch()
    
    print(f"Generating gRPC code...")
    print(f"Proto directory: {proto_dir}")
    print(f"Output directory: {generated_dir}")
    
    # Run protoc command
    proto_files = list(proto_dir.glob("*.proto"))
    
    if not proto_files:
        print("No .proto files found in protos directory")
        return False
    
    for proto_file in proto_files:
        cmd = [
            sys.executable, "-m", "grpc_tools.protoc",
            f"--proto_path={proto_dir}",
            f"--python_out={generated_dir}",
            f"--grpc_python_out={generated_dir}",
            str(proto_file)
        ]
        
        print(f"Running: {' '.join(cmd)}")
        
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            print(f"✓ Generated code for {proto_file.name}")
            
        except subprocess.CalledProcessError as e:
            print(f"✗ Error generating code for {proto_file.name}")
            print(f"Error: {e.stderr}")
            return False
        except FileNotFoundError:
            print("✗ grpc_tools not found. Install with: pip install grpcio-tools")
            return False
    
    print("✓ gRPC code generation completed successfully")
    
    # List generated files
    print("\nGenerated files:")
    for file in generated_dir.glob("*.py"):
        print(f"  - {file.name}")
    
    return True

if __name__ == "__main__":
    success = generate_grpc_code()
    sys.exit(0 if success else 1)
