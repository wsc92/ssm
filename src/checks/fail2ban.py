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
        status_output = self.executor.run(f"sudo fail2ban-client status {jail} 2>/dev/null")
        
        if status_output:
            # Look for "Banned IP list:" followed by IPs
            banned_match = re.search(r'Banned IP list:\s+(.+?)(?:\n|$)', status_output, re.DOTALL)
            if banned_match:
                ip_str = banned_match.group(1).strip()
                if ip_str:
                    ips = ip_str.split()
                    return [ip for ip in ips if re.match(r'^\d+\.\d+\.\d+\.\d+$', ip)]
        
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

        # Check banned IPs - needs sudo
        output = self.executor.run("sudo fail2ban-client status sshd 2>/dev/null")

        if output:
            banned_match = re.search(r'Currently banned:\s+(\d+)', output)
            total_banned_match = re.search(r'Total banned:\s+(\d+)', output)

            if banned_match and total_banned_match:
                currently_banned = int(banned_match.group(1))
                total_banned = int(total_banned_match.group(1))
                
                if currently_banned > 0:
                    banned_ips = self._get_banned_ips("sshd")
                    if banned_ips:
                        ip_list = ', '.join(banned_ips)
                        self.result.info.append(
                            f"fail2ban: {currently_banned} IPs currently banned - {ip_list}"
                        )
                    else:
                        self.result.info.append(
                            f"fail2ban: {currently_banned} IPs currently banned, {total_banned} total"
                        )
                else:
                    self.result.info.append(
                        f"fail2ban is active: 0 IPs currently banned, {total_banned} total historical bans"
                    )
            else:
                # Fallback if we can't parse counts
                self.result.info.append("fail2ban is active")
        else:
            # No output from fail2ban-client (likely permissions issue)
            self.result.info.append("fail2ban is active (unable to query jail status - check sudo permissions)")
 
        return self.result

