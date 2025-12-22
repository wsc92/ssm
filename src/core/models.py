from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
from datetime import datetime

@dataclass
class Issue:
    type: str
    severity: str  # CRITICAL, HIGH, MEDIUM
    details: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class ScanResult:
    issues: List[Issue] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    info: List[str] = field(default_factory=list)
    scan_time: datetime = field(default_factory=datetime.now)
    
    def has_critical(self) -> bool:
        return any(i.severity == "CRITICAL" for i in self.issues)

