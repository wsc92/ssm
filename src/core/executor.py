import subprocess
import logging
from typing import Optional

logger = logging.getLogger(__name__)

class CommandExecutor:
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
    
    def run(self, cmd: str) -> str:
        """Execute shell command and return stdout"""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                timeout=self.timeout
            )
            logger.debug(f"Executed: {cmd[:50]}...")
            return result.stdout
        except subprocess.TimeoutExpired:
            logger.warning(f"Command timed out: {cmd}")
            return ""
        except Exception as e:
            logger.error(f"Command failed: {cmd} - {e}")
            return ""

