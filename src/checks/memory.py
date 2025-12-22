from src.checks.base import BaseCheck
from src.core.models import Issue

class MemoryCheck(BaseCheck):
    def __init__(self, executor, crit_threshold=90, warn_threshold=80):
        super().__init__(executor)
        self.crit_threshold = crit_threshold
        self.warn_threshold = warn_threshold

    @property
    def name(self) -> str:
        return "Memory Usage"

    def run(self):
        output = self.executor.run("free -m | grep Mem")

        if output:
            parts = output.split()
            total = int(parts[1])
            used = int(parts[2])
            usage = (used / total) * 100

            if usage >= self.crit_threshold:
                self.result.issues.append(Issue(
                    type="Memory Usage",
                    severity="HIGH",
                    details=f"Memory usage is {usage:.1f}% ({used}MB / {total}MB)",
                    metadata={"usage": usage, "used": used, "total": total}
                ))
            elif usage >= self.warn_threshold:
                self.result.warnings.append(f"Memory usage is {usage:.1f}%")

        return self.result

