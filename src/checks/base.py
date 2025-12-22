from abc import ABC, abstractmethod
from src.core.models import ScanResult
from src.core.executor import CommandExecutor

class BaseCheck(ABC):
    def __init__(self, executor: CommandExecutor):
        self.executor = executor
        self.result = ScanResult()
    
    @abstractmethod
    def run(self) -> ScanResult:
        """Execute the check and return results"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Human-readable check name"""
        pass

