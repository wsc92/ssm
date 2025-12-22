from src.checks.base import BaseCheck
from src.core.models import Issue

class DatabaseCheck(BaseCheck):
    def __init__(self, executor, error_threshold=10):
        super().__init__(executor)
        self.error_threshold = error_threshold

    @property
    def name(self) -> str:
        return "PostgreSQL Status"

    def run(self):
        # Check if PostgreSQL is running
        status = self.executor.run("systemctl is-active postgresql")

        if "active" not in status:
            self.result.issues.append(Issue(
                type="Database",
                severity="CRITICAL",
                details="PostgreSQL is not running"
            ))
            return self.result

        # Check for errors in postgres logs
        cmd = "journalctl -u postgresql --since '24 hours ago' --no-pager | grep -i error | wc -l"
        error_count = self.executor.run(cmd).strip()

        if error_count and int(error_count) > self.error_threshold:
            self.result.warnings.append(
                f"PostgreSQL has {error_count} errors in the last 24 hours"
            )

        return self.result

