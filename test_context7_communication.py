import logging
import sys
import os
import subprocess
import time
import json
from src.book_writing_flow.tools.context7_mcp import Context7_MCP

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # Console output
    ]
)

class SimpleContext7Test:
    def __init__(self):
        self.binary = "C:\\Program Files\\nodejs\\npx.cmd"
        self.package = "@upstash/context7-mcp"
        self.proc = None
    
    def startup(self):
        """Start the subprocess directly with more debugging."""
        print(f"Starting subprocess: {self.binary} {self.package}")
        self.proc = subprocess.Popen(
            ["cmd.exe", "/c", self.binary, self.package],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        print(f"Subprocess started with PID: {self.proc.pid}")
        
        # Check if process is running
        if self.proc.poll() is not None:
            print(f"Process exited immediately with code: {self.proc.returncode}")
            stderr = self.proc.stderr.read()
            if stderr:
                print(f"Stderr: {stderr}")
            return False
        
        return True
    
    def send_request(self, request_type, args):
        """Send a request to the subprocess and read the response."""
        if not self.proc:
            print("Subprocess not started")
            return None
        
        # Prepare the request
        request = {
            "tool": request_type,
            "args": args
        }
        request_json = json.dumps(request) + "\n"
        
        print(f"Sending request: {request_json.strip()}")
        
        # Send the request
        self.proc.stdin.write(request_json)
        self.proc.stdin.flush()
        
        # Read the response with timeout
        timeout = 10  # 10 seconds
        start_time = time.time()
        
        response_lines = []
        print("Waiting for response...")
        
        while time.time() - start_time < timeout:
            # Check if process is still running
            if self.proc.poll() is not None:
                print(f"Process exited with code: {self.proc.returncode}")
                stderr = self.proc.stderr.read()
                if stderr:
                    print(f"Stderr: {stderr}")
                break
            
            # Check if there's data to read from stdout
            try:
                # Try to read a line with a small timeout
                line = self.proc.stdout.readline()
                if line:
                    print(f"Received line: {line.strip()}")
                    response_lines.append(line.strip())
                    if line.strip().endswith("}"):
                        # End of JSON response
                        break
                else:
                    # No data available, sleep briefly
                    time.sleep(0.1)
            except Exception as e:
                print(f"Error reading from stdout: {e}")
                time.sleep(0.1)
        
        if not response_lines:
            print(f"No response received after {timeout} seconds")
            return None
        
        # Parse the response
        response_text = "".join(response_lines)
        print(f"Raw response: {response_text}")
        
        try:
            response = json.loads(response_text)
            return response.get("result")
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON response: {e}")
            return None
    
    def shutdown(self):
        """Shut down the subprocess."""
        if self.proc:
            print("Shutting down subprocess...")
            try:
                self.proc.terminate()
                self.proc.wait(timeout=5)
                print("Subprocess terminated successfully")
            except Exception as e:
                print(f"Error terminating subprocess: {e}")
                try:
                    self.proc.kill()
                    print("Subprocess killed")
                except Exception as e2:
                    print(f"Error killing subprocess: {e2}")
            self.proc = None

def test_simple_communication():
    """Test simple communication with the Context7 MCP subprocess."""
    print("\n=== Testing simple communication with Context7 MCP ===")
    tester = SimpleContext7Test()
    
    try:
        # Start the subprocess
        if not tester.startup():
            print("Failed to start subprocess")
            return False
        
        # Wait a moment for the subprocess to initialize
        print("Waiting for subprocess to initialize...")
        time.sleep(2)
        
        # Send a simple request to resolve a library ID
        print("Sending request to resolve library ID for 'ChatGPT'...")
        result = tester.send_request("resolve-library-id", {"libraryName": "ChatGPT"})
        
        if result:
            print(f"Received result: {result}")
            return True
        else:
            print("Failed to get a valid response")
            return False
    except Exception as e:
        print(f"Error in test_simple_communication: {e}")
        import traceback
        traceback.print_exc()
        return False
    finally:
        # Always shut down the subprocess
        tester.shutdown()

if __name__ == "__main__":
    print("Starting Context7 MCP communication test...")
    
    success = test_simple_communication()
    print(f"Communication test completed {'successfully' if success else 'with errors'}")