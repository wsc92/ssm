import re
from datetime import datetime, timedelta
from src.checks.base import BaseCheck

class RecentLoginsCheck(BaseCheck):
    def __init__(self, executor, hours=24):
        super().__init__(executor)
        self.hours = hours

    @property
    def name(self) -> str:
        return f"Recent SSH Logins (last {self.hours} hours)"

    def run(self):
        since_time = (datetime.now() - timedelta(hours=self.hours)).strftime('%Y-%m-%d %H:%M:%S')
        cmd = f"journalctl -u sshd --since '{since_time}' --no-pager | grep 'Accepted'"
        output = self.executor.run(cmd)

        if output:
            logins = []
            for line in output.split('\n'):
                if not line.strip():
                    continue

                ip_match = re.search(r'from (\d+\.\d+\.\d+\.\d+)', line)
                user_match = re.search(r'for (\w+)', line)
                time_match = re.search(r'(\w{3}\s+\d+\s+\d{2}:\d{2}:\d{2})', line)

                if ip_match and user_match:
                    logins.append({
                        "time": time_match.group(1) if time_match else "unknown",
                        "user": user_match.group(1),
                        "ip": ip_match.group(1)
                    })

            if logins:
                self.result.info.append(
                    f"Found {len(logins)} successful login(s) in the last {self.hours} hours:"
                )
                
                for login in logins:
                    self.result.info.append(
                        f"  [{login['time']}] User '{login['user']}' from {login['ip']}"
                    )

        return self.result

