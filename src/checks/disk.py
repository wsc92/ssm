from src.checks.base import BaseCheck
from src.core.models import Issue

class DiskSpaceCheck(BaseCheck):
    def __init__(self, executor, crit_threshold=90, warn_threshold=80):
        super().__init__(executor)
        self.crit_threshold = crit_threshold
        self.warn_threshold = warn_threshold

    @property
    def name(self) -> str:
        return "Disk Space"

    def run(self):
        output = self.executor.run("df -h | grep -E '^/dev'")

        for line in output.split('\n'):
            if not line.strip():
                continue

            parts = line.split()
            if len(parts) >= 5:
                usage = int(parts[4].rstrip('%'))
                mount = parts[5] if len(parts) > 5 else parts[0]

                if usage >= self.crit_threshold:
                    self.result.issues.append(Issue(
                        type="Disk Space",
                        severity="CRITICAL",
                        details=f"{mount} is {usage}% full",
                        metadata={"mount": mount, "usage": usage}
                    ))
                elif usage >= self.warn_threshold:
                    self.result.warnings.append(
                        f"Disk space warning: {mount} is {usage}% full"
                    )

        return self.result

