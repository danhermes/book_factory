import subprocess
import json
import threading
import logging
import sys
import time
from typing import List, Optional

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class Context7_MCP:
    def __init__(self, binary="npx", package="@upstash/context7-mcp"):
        if sys.platform == "win32" and binary == "npx":
            try:
                result = subprocess.run(["where", "npx"], capture_output=True, text=True)
                npx_paths = result.stdout.strip().split('\n')
                self.binary = next((p for p in npx_paths if p.endswith('.cmd')), npx_paths[0] if npx_paths else "C:\\Program Files\\nodejs\\npx.cmd")
            except Exception as e:
                logger.warning(f"Error finding npx path: {e}")
                self.binary = "C:\\Program Files\\nodejs\\npx.cmd"
            logger.info(f"Using npx at: {self.binary}")
        else:
            self.binary = binary

        self.package = package
        self.proc = None
        self.lock = threading.Lock()
        self.output_lines = []
        self.reader_thread = None
        logger.info(f"Context7_MCP initialized with binary={self.binary}, package={package}")

    def startup(self):
        if self.proc is None:
            logger.info(f"Starting Context7 MCP subprocess with command: {self.binary} {self.package}")
            try:
                cmd = ["cmd.exe", "/c", self.binary, self.package] if sys.platform == "win32" and self.binary.endswith('.cmd') else [self.binary, self.package]
                self.proc = subprocess.Popen(
                    cmd,
                    stdin=subprocess.PIPE,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )

                self.output_lines = []

                def read_stdout():
                    for line in iter(self.proc.stdout.readline, ''):
                        if line.strip():
                            logger.debug(f"[Context7 stdout] {line.strip()}")
                            self.output_lines.append(line.strip())

                self.reader_thread = threading.Thread(target=read_stdout, daemon=True)
                self.reader_thread.start()

                logger.info("Context7 MCP subprocess started successfully")
            except Exception as e:
                logger.error(f"Failed to start Context7 MCP subprocess: {e}")
                raise
        else:
            logger.info("Context7 MCP subprocess already running")

    def shutdown(self):
        if self.proc:
            logger.info("Shutting down Context7 MCP subprocess")
            try:
                self.proc.terminate()
                logger.info("Context7 MCP subprocess terminated successfully")
            except Exception as e:
                logger.warning(f"Error terminating Context7 MCP subprocess: {e}")
            self.proc = None
        else:
            logger.info("Context7 MCP subprocess not running, nothing to shutdown")

    def _send_request(self, payload: dict) -> Optional[str]:
        if not self.proc:
            logger.error("Context7MCP not started")
            raise RuntimeError("Context7MCP not started")

        logger.debug(f"Sending request to Context7: {payload}")

        with self.lock:
            try:
                self.output_lines.clear()

                request_str = json.dumps(payload)
                self.proc.stdin.write(request_str + "\n")
                self.proc.stdin.flush()
                logger.debug("Request sent to Context7 subprocess")

                timeout = 30
                start_time = time.time()
                while time.time() - start_time < timeout:
                    if self.output_lines:
                        break
                    time.sleep(0.1)
                else:
                    logger.warning(f"Timeout after {timeout} seconds waiting for Context7 response")
                    return f"[Context7 ERROR: Timeout after {timeout} seconds]"

                response_text = "\n".join(self.output_lines).strip()
                if not response_text:
                    logger.warning("Empty response from Context7")
                    return "[Context7 ERROR: Empty response]"

                logger.debug(f"Raw response from Context7: {response_text}")
                try:
                    response = json.loads(response_text)
                    result = response.get("result")
                    logger.debug(f"Parsed result from Context7: {result}")
                    return result
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing JSON response: {e}")
                    logger.error(f"Raw response was: {response_text}")
                    return f"[Context7 ERROR: Invalid JSON response: {e}]"
            except Exception as e:
                logger.error(f"Error in _send_request: {e}")
                import traceback
                logger.error(traceback.format_exc())
                return f"[Context7 ERROR: {e}]"

    def resolve_library_id(self, library_name: str) -> Optional[str]:
        logger.info(f"Resolving library ID for: {library_name}")
        result = self._send_request({
            "tool": "resolve-library-id",
            "args": {"libraryName": library_name}
        })
        logger.info(f"Library ID resolution result for '{library_name}': {result}")
        return result

    def get_library_docs(self, library_id: str, topic: Optional[str] = None, tokens: int = 2000) -> Optional[str]:
        logger.info(f"Getting library docs for ID: {library_id}, topic: {topic}, tokens: {tokens}")
        args = {
            "context7CompatibleLibraryID": library_id,
            "tokens": tokens
        }
        if topic:
            args["topic"] = topic

        result = self._send_request({
            "tool": "get-library-docs",
            "args": args
        })
        logger.info(f"Library docs result for '{library_id}' (topic: {topic}): {len(str(result)) if result else 0} chars")
        return result

    def get_documentation(self, product_name: str, functions: Optional[List[str]] = None, token_limit: int = 2000) -> str:
        logger.info(f"Getting documentation for product: {product_name}, functions: {functions}, token_limit: {token_limit}")
        self.startup()
        try:
            lib_id = self.resolve_library_id(product_name)
            if not lib_id:
                logger.warning(f"Could not resolve library ID for: {product_name}")
                return f"[Context7] Could not resolve library: {product_name}"

            docs = []
            if functions:
                per_topic = max(token_limit // len(functions), 300)
                logger.info(f"Getting docs for {len(functions)} functions, {per_topic} tokens per topic")
                for topic in functions:
                    doc = self.get_library_docs(lib_id, topic=topic, tokens=per_topic)
                    if doc:
                        docs.append(f"### {topic}\n{doc}")
            else:
                logger.info(f"Getting full documentation for {product_name}")
                doc = self.get_library_docs(lib_id, tokens=token_limit)
                if doc:
                    docs.append(doc)

            result = "\n\n".join(docs)
            logger.info(f"Documentation result for '{product_name}': {len(result)} chars")
            return result

        except Exception as e:
            logger.error(f"Error getting documentation for {product_name}: {e}")
            return f"[Context7 ERROR: {e}]"
        finally:
            self.shutdown()
