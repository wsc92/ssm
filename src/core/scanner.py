import logging
from typing import List, Type
from src.checks.base import BaseCheck
from src.core.models import ScanResult
from src.core.executor import CommandExecutor

logger = logging.getLogger(__name__)

class SystemScanner:
    def __init__(self, executor: CommandExecutor):
        self.executor = executor
        self.checks: List[BaseCheck] = []
    
    def register_check(self, check_class: Type[BaseCheck], **kwargs):
        """Register a check to run"""
        check = check_class(self.executor, **kwargs)
        self.checks.append(check)
    
    def run_all(self) -> ScanResult:
        """Execute all registered checks"""
        combined = ScanResult()
        
        for check in self.checks:
            logger.info(f"Running {check.name}...")
            result = check.run()
            
            combined.issues.extend(result.issues)
            combined.warnings.extend(result.warnings)
            combined.info.extend(result.info)
        
        return combined

