import re
from datetime import datetime, timedelta
from collections import Counter
from src.checks.base import BaseCheck

class ServiceRestartsCheck(BaseCheck):
    def __init__(self, executor, days=7, threshold=20):
        super().__init__(executor)
        self.days = days
        self.threshold = threshold

    @property
    def name(self) -> str:
        return f"Service Restarts (last {self.days} days)"

    def run(self):
        since_date = (datetime.now() - timedelta(days=self.days)).strftime('%Y-%m-%d')
        cmd = f"journalctl --since '{since_date}' --no-pager | grep -E 'Started|Stopped' | grep '.service'"
        output = self.executor.run(cmd)

        if not output:
            return self.result

        # Count restarts per service
        service_restarts = Counter()
        for line in output.split('\n'):
            match = re.search(r'([\w-]+\.service)', line)
            if match and 'Started' in line:
                service_restarts[match.group(1)] += 1

        # Flag services with excessive restarts
        for service, count in service_restarts.items():
            if count > self.threshold:
                self.result.warnings.append(
                    f"Service '{service}' has restarted {count} times in the last {self.days} days"
                )

        return self.result

