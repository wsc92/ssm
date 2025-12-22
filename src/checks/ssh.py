import re
from datetime import datetime, timedelta
from collections import defaultdict
from src.checks.base import BaseCheck
from src.core.models import Issue

class SSHAttackCheck(BaseCheck):
    def __init__(self, executor, days=7):
        super().__init__(executor)
        self.days = days
        self.attackers = defaultdict(lambda: {
            "attempts": 0,
            "usernames": set(),
            "last_seen": None
        })

    @property
    def name(self) -> str:
        return f"SSH Attacks (last {self.days} days)"

    def run(self):
        since_date = (datetime.now() - timedelta(days=self.days)).strftime('%Y-%m-%d')
        cmd = f"journalctl -u sshd --since '{since_date}' --no-pager | grep -E 'Failed password|Invalid user'"
        output = self.executor.run(cmd)

        if not output:
            self.result.info.append("No SSH attacks detected in the specified period")
            return self.result

        # Parse attacks
        for line in output.split('\n'):
            if not line.strip():
                continue

            ip_match = re.search(r'from (\d+\.\d+\.\d+\.\d+)', line)
            user_match = re.search(r'for (?:invalid user )?(\S+)', line)

            if ip_match:
                ip = ip_match.group(1)
                username = user_match.group(1) if user_match else "unknown"

                # Skip local network IPs
                if ip.startswith(('192.168.', '10.', '172.')):
                    continue

                self.attackers[ip]["attempts"] += 1
                self.attackers[ip]["usernames"].add(username)
                self.attackers[ip]["last_seen"] = datetime.now()

        # Sort by attempts
        sorted_attackers = sorted(
            self.attackers.items(),
            key=lambda x: x[1]["attempts"],
            reverse=True
        )

        if sorted_attackers:
            top_10 = sorted_attackers[:10]
            total_attempts = sum(data["attempts"] for _, data in sorted_attackers)

            self.result.issues.append(Issue(
                type="SSH Attacks",
                severity="HIGH" if total_attempts > 1000 else "MEDIUM",
                details=f"Detected {len(sorted_attackers)} attacking IPs with {total_attempts} total attempts",
                metadata={
                    "top_attackers": [
                        {
                            "ip": ip,
                            "attempts": data["attempts"],
                            "usernames": len(data["usernames"]),
                            "last_seen": data["last_seen"].strftime("%Y-%m-%d %H:%M") if data["last_seen"] else "unknown"
                        }
                        for ip, data in top_10
                    ]
                }
            ))

        return self.result

