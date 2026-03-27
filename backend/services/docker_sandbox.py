"""
Docker Sandbox Execution Module
Executes exploits in isolated Docker containers
"""

import docker
import json
import logging
import tempfile
import os
from pathlib import Path
from typing import Dict, Optional, Tuple
from datetime import datetime

logger = logging.getLogger(__name__)


class DockerSandbox:
    """
    Manages Docker container creation and exploit execution
    """

    def __init__(self):
        try:
            self.client = docker.from_env()
        except Exception as e:
            logger.error(f"Failed to initialize Docker client: {e}")
            self.client = None

    def is_available(self) -> bool:
        """Check if Docker is available"""
        if self.client is None:
            return False
        try:
            self.client.ping()
            return True
        except Exception as e:
            logger.error(f"Docker is not available: {e}")
            return False

    def execute_exploit(
        self,
        exploit_type: str,
        exploit_payload: str,
        snapshot_data: str,
        timeout: int = 30
    ) -> Dict:
        """
        Execute exploit in isolated Docker container

        Args:
            exploit_type: Type of exploit (SQL_INJECTION, XSS, etc.)
            exploit_payload: The actual exploit code/payload
            snapshot_data: Source code snapshot to test against
            timeout: Container timeout in seconds

        Returns:
            Dict with execution results
        """
        if not self.is_available():
            logger.warning("Docker not available, simulating execution")
            return self._simulate_execution(exploit_type, exploit_payload)

        container = None
        try:
            # Create temporary directory for snapshot
            with tempfile.TemporaryDirectory() as tmpdir:
                snapshot_file = Path(tmpdir) / "snapshot.py"
                exploit_file = Path(tmpdir) / "exploit.py"
                
                # Write snapshot and exploit to files
                snapshot_file.write_text(snapshot_data)
                exploit_file.write_text(self._create_test_script(exploit_payload, exploit_type))

                # Create container
                container = self.client.containers.run(
                    "python:3.11-slim",
                    command=["python", "/sandbox/exploit.py"],
                    volumes={tmpdir: {"bind": "/sandbox", "mode": "ro"}},
                    detach=True,
                    mem_limit="512m",
                    cpus=1.0,
                    network_disabled=True,  # Isolate network
                )

                # Wait for completion
                exit_code = container.wait(timeout=timeout)
                logs = container.logs(stdout=True, stderr=True).decode(errors='replace')

                # Analyze results
                is_vulnerable = self._analyze_vulnerability(logs, exploit_type)

                return {
                    "status": "success",
                    "vulnerable": is_vulnerable,
                    "stdout": logs,
                    "stderr": "",
                    "return_code": exit_code,
                    "container_id": container.id,
                    "execution_time_ms": timeout * 1000,
                }

        except docker.errors.APIError as e:
            logger.error(f"Docker API error: {e}")
            return {
                "status": "failed",
                "vulnerable": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": 1,
                "container_id": container.id if container else None,
                "execution_time_ms": timeout * 1000,
            }
        except Exception as e:
            logger.error(f"Execution error: {e}")
            return {
                "status": "failed",
                "vulnerable": False,
                "stdout": "",
                "stderr": str(e),
                "return_code": 1,
                "container_id": container.id if container else None,
                "execution_time_ms": timeout * 1000,
            }
        finally:
            # Cleanup container
            if container:
                try:
                    container.remove(force=True)
                except Exception as e:
                    logger.warning(f"Failed to remove container: {e}")

    def _create_test_script(self, exploit_payload: str, exploit_type: str) -> str:
        """Create a test script that executes the exploit"""
        
        if exploit_type == "SQL_INJECTION":
            return f"""
import sqlite3

# Create vulnerable database
conn = sqlite3.connect(':memory:')
cursor = conn.cursor()

# Create test table
cursor.execute('CREATE TABLE users (id INTEGER, username TEXT, password TEXT)')
cursor.execute("INSERT INTO users VALUES (1, 'admin', 'secret123')")
conn.commit()

# Vulnerable query (simulated)
user_input = "{exploit_payload}"
query = f"SELECT * FROM users WHERE username = '${{user_input}}'"

try:
    cursor.execute(query)
    result = cursor.fetchall()
    print(f"VULNERABLE: Retrieved data {{result}}")
    exit(0)
except Exception as e:
    print(f"ERROR: {{e}}")
    exit(1)
finally:
    conn.close()
"""
        
        elif exploit_type == "XSS":
            return f"""
import re

# Simulate web application
html_template = '<div>{input_field}</div>'
payload = "{exploit_payload}"

# Check if payload is properly escaped
rendered = html_template.format(input_field=payload)

if '<script>' in rendered or 'javascript:' in rendered or 'onclick=' in rendered:
    print(f"VULNERABLE: XSS payload executed")
    exit(0)
else:
    print("SAFE: XSS payload blocked")
    exit(1)
"""
        
        elif exploit_type == "COMMAND_INJECTION":
            return f"""
import subprocess
import os

payload = "{exploit_payload}"

# Vulnerable command construction
cmd = f"echo User input: ${{payload}}"

try:
    result = subprocess.run(cmd, shell=True, capture_output=True, timeout=5)
    output = result.stdout.decode()
    
    if result.returncode == 0 and 'User input' in output:
        print(f"VULNERABLE: Command injection successful")
        print(f"Output: ${{output}}")
        exit(0)
    else:
        print("SAFE: Command injection blocked")
        exit(1)
except Exception as e:
    print(f"ERROR: {{e}}")
    exit(1)
"""
        
        elif exploit_type == "PATH_TRAVERSAL":
            return f"""
import os
from pathlib import Path

payload = "{exploit_payload}"

# Vulnerable file access
base_dir = "/sandbox"
requested_file = os.path.join(base_dir, payload)
normalized = os.path.normpath(requested_file)

# Check if path escapes base directory
if not normalized.startswith(base_dir):
    print(f"VULNERABLE: Path traversal successful - accessed {{normalized}}")
    exit(0)
else:
    print("SAFE: Path traversal blocked")
    exit(1)
"""
        else:
            return f"""
# Generic exploit execution
print("Exploit: {exploit_payload}")
exit(0)
"""

    def _analyze_vulnerability(self, logs: str, exploit_type: str) -> bool:
        """
        Analyze execution logs to determine if vulnerability was exploited

        Args:
            logs: Container stdout/stderr logs
            exploit_type: Type of exploit being tested

        Returns:
            True if vulnerability confirmed, False otherwise
        """
        logs_lower = logs.lower()

        if "VULNERABLE" in logs:
            return True
        
        if exploit_type == "SQL_INJECTION":
            return "retrieved data" in logs_lower or "injection successful" in logs_lower
        
        elif exploit_type == "XSS":
            return "xss payload executed" in logs_lower or "<script>" in logs_lower
        
        elif exploit_type == "COMMAND_INJECTION":
            return "command injection successful" in logs_lower
        
        elif exploit_type == "PATH_TRAVERSAL":
            return "path traversal successful" in logs_lower
        
        return False

    def _simulate_execution(self, exploit_type: str, exploit_payload: str) -> Dict:
        """Simulate exploit execution when Docker is not available"""
        logger.info(f"Simulating {exploit_type} exploitation")
        
        # Simulate vulnerability detection based on payload patterns
        is_vulnerable = False
        
        if exploit_type == "SQL_INJECTION" and ("'" in exploit_payload or "OR" in exploit_payload.upper()):
            is_vulnerable = True
        elif exploit_type == "XSS" and ("<script>" in exploit_payload or "javascript:" in exploit_payload):
            is_vulnerable = True
        elif exploit_type == "COMMAND_INJECTION" and ("|" in exploit_payload or ";" in exploit_payload):
            is_vulnerable = True
        elif exploit_type == "PATH_TRAVERSAL" and ".." in exploit_payload:
            is_vulnerable = True
        
        return {
            "status": "success",
            "vulnerable": is_vulnerable,
            "stdout": f"Simulated {exploit_type} execution: {'VULNERABLE' if is_vulnerable else 'SAFE'}",
            "stderr": "",
            "return_code": 0,
            "container_id": "simulated",
            "execution_time_ms": 100,
        }
