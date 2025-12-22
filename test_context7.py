import logging
import sys
import os
from src.book_writing_flow.tools.context7_mcp import Context7_MCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Console output
    ]
)

def test_context7():
    """Test the Context7_MCP class with a simple tool."""
    try:
        # Print the PATH environment variable
        print("PATH environment variable:")
        path_var = os.environ.get('PATH', '')
        path_dirs = path_var.split(os.pathsep)
        for i, directory in enumerate(path_dirs):
            print(f"  {i+1}. {directory}")
        
        # Check if Node.js directory is in PATH
        nodejs_dir = "C:\\Program Files\\nodejs"
        if nodejs_dir in path_dirs:
            print(f"\nNode.js directory ({nodejs_dir}) is in PATH")
        else:
            print(f"\nNode.js directory ({nodejs_dir}) is NOT in PATH")
        
        # Check if npx exists
        npx_path = os.path.join(nodejs_dir, "npx.cmd")
        if os.path.exists(npx_path):
            print(f"npx exists at: {npx_path}")
        else:
            print(f"npx does not exist at: {npx_path}")
            
        # Try to find npx using 'where' command
        import subprocess
        try:
            result = subprocess.run(["where", "npx"], capture_output=True, text=True, check=False)
            if result.returncode == 0:
                print(f"npx found using 'where' command at: {result.stdout.strip()}")
            else:
                print("npx not found using 'where' command")
        except Exception as e:
            print(f"Error running 'where npx': {e}")
        
        print("\nInitializing Context7_MCP...")
        context7 = Context7_MCP()
        
        print("Getting documentation for 'ChatGPT'...")
        docs = context7.get_documentation("ChatGPT", token_limit=1000)
        
        print(f"Documentation result length: {len(docs) if docs else 0}")
        print("First 500 characters of documentation:")
        print(docs[:500] if docs else "No documentation returned")
        
        return True
    except Exception as e:
        print(f"Error testing Context7_MCP: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("Starting Context7 MCP test...")
    success = test_context7()
    print(f"Test completed {'successfully' if success else 'with errors'}")