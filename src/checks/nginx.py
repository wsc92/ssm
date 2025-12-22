from datetime import datetime, timedelta
from src.checks.base import BaseCheck
from src.core.models import Issue

class NginxCheck(BaseCheck):
    def __init__(self, executor, hours=24, error_threshold=100):
        super().__init__(executor)
        self.hours = hours
        self.error_threshold = error_threshold

    @property
    def name(self) -> str:
        return f"Nginx Errors (last {self.hours} hours)"

    def run(self):
        since_time = (datetime.now() - timedelta(hours=self.hours)).strftime('%Y-%m-%d %H:%M:%S')
        cmd = f"journalctl -u nginx --since '{since_time}' --no-pager | grep -E '\\[error\\]|\\[crit\\]|\\[alert\\]|\\[emerg\\]'"
        output = self.executor.run(cmd)

        if output:
            error_lines = output.split('\n')
            error_count = len([l for l in error_lines if l.strip()])

            if error_count > self.error_threshold:
                self.result.warnings.append(
                    f"nginx has {error_count} errors in the last {self.hours} hours"
                )

            # Check for permission errors specifically
            permission_errors = [l for l in error_lines if 'Permission denied' in l]
            if permission_errors:
                self.result.issues.append(Issue(
                    type="Nginx Permissions",
                    severity="MEDIUM",
                    details=f"Found {len(permission_errors)} permission denied errors"
                ))

        return self.result

