import re
from src.checks.base import BaseCheck
from src.core.models import Issue

class Fail2BanCheck(BaseCheck):
    @property
    def name(self) -> str:
        return "fail2ban Status"

    def run(self):
        # Check if fail2ban is running
        status = self.executor.run("systemctl is-active fail2ban")

        if "active" not in status:
            self.result.issues.append(Issue(
                type="Security",
                severity="CRITICAL",
                details="fail2ban is not running! SSH is vulnerable to brute force attacks"
            ))
            return self.result

        # Check banned IPs
        output = self.executor.run("fail2ban-client status sshd 2>/dev/null")

        if output:
            banned_match = re.search(r'Currently banned:\s+(\d+)', output)
            total_banned_match = re.search(r'Total banned:\s+(\d+)', output)

            if banned_match and total_banned_match:
                currently_banned = int(banned_match.group(1))
                total_banned = int(total_banned_match.group(1))
                self.result.info.append(
                    f"fail2ban is active: {currently_banned} currently banned, "
                    f"{total_banned} total banned"
                )
 
        return self.result
