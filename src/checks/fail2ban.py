import re
from typing import List
from src.checks.base import BaseCheck
from src.core.models import Issue

class Fail2BanCheck(BaseCheck):
    @property
    def name(self) -> str:
        return "fail2ban Status"

    def _get_banned_ips(self, jail: str = "sshd") -> List[str]:
        """Extract list of currently banned IPs from a specific jail."""
        output = self.executor.run(f"fail2ban-client get {jail} banip 2>/dev/null")
        
        if output and output.strip():
            # Command returns IPs space-separated on one line
            ips = output.strip().split()
            return [ip for ip in ips if ip and re.match(r'\d+\.\d+\.\d+\.\d+', ip)]
        
        return []

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
                
                # Get list of banned IPs if any exist
                if currently_banned > 0:
                    banned_ips = self._get_banned_ips("sshd")
                    if banned_ips:
                        self.result.info.append(
                            f"fail2ban: {currently_banned} currently banned IPs - {', '.join(banned_ips[:10])}"
                            + (f" (+{len(banned_ips)-10} more)" if len(banned_ips) > 10 else "")
                        )
                    else:
                        self.result.info.append(
                            f"fail2ban is active: {currently_banned} currently banned, {total_banned} total banned"
                        )
                else:
                    self.result.info.append(
                        f"fail2ban is active: no IPs currently banned, {total_banned} total banned"
                    )
 
        return self.result

