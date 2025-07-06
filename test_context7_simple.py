import logging
import sys
import os
import subprocess
import time
from src.book_writing_flow.tools.context7_mcp import Context7_MCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Console output
    ]
)

def test_npx_directly():
    """Test running npx directly to verify it works."""
    print("\n=== Testing npx directly ===")
    try:
        # Try running npx --version
        print("Running 'npx --version'...")
        result = subprocess.run(["cmd.exe", "/c", "npx", "--version"], 
                               capture_output=True, text=True, timeout=5)
        print(f"Exit code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        
        # Try running npx with the context7-mcp package
        print("\nRunning 'npx @upstash/context7-mcp --help'...")
        result = subprocess.run(["cmd.exe", "/c", "npx", "@upstash/context7-mcp", "--help"], 
                               capture_output=True, text=True, timeout=5)
        print(f"Exit code: {result.returncode}")
        print(f"Stdout: {result.stdout}")
        print(f"Stderr: {result.stderr}")
        
        return True
    except Exception as e:
        print(f"Error testing npx directly: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_context7_startup():
    """Test just starting up the Context7_MCP subprocess."""
    print("\n=== Testing Context7_MCP startup ===")
    try:
        print("Initializing Context7_MCP...")
        context7 = Context7_MCP()
        
        print("Starting up Context7 MCP subprocess...")
        context7.startup()
        
        print("Sleeping for 3 seconds...")
        time.sleep(3)
        
        print("Shutting down Context7 MCP subprocess...")
        context7.shutdown()
        
        return True
    except Exception as e:
        print(f"Error testing Context7_MCP startup: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting simple Context7 MCP tests...")
    
    success1 = test_npx_directly()
    print(f"Direct npx test completed {'successfully' if success1 else 'with errors'}")
    
    success2 = test_context7_startup()
    print(f"Context7_MCP startup test completed {'successfully' if success2 else 'with errors'}")
    
    print(f"All tests completed {'successfully' if success1 and success2 else 'with some errors'}")