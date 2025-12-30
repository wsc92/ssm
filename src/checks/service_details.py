import re
from src.checks.base import BaseCheck
from src.core.models import Issue

class ServiceDetailsCheck(BaseCheck):
    def __init__(self, executor, services: list, days: int = 7, restart_threshold: int = 10):
        super().__init__(executor)
        self.services = services
        self.days = days
        self.restart_threshold = restart_threshold

    @property
    def name(self) -> str:
        return "Service Health Details"

    def _get_restart_reasons(self, service_name: str) -> list:
        """Extract restart/failure reasons from journal."""
        output = self.executor.run(
            f"journalctl -u {service_name} --since '{self.days} days ago' "
            f"-p err..warning -n 10 --no-pager"
        )
        
        reasons = []
        if output and 'No entries' not in output:
            lines = output.strip().split('\n')
            for line in lines:
                # Extract meaningful error messages
                if any(keyword in line.lower() for keyword in 
                       ['error', 'failed', 'exit', 'signal', 'crash']):
                    # Clean up timestamp and service name
                    clean_line = re.sub(r'^.*?\]: ', '', line)
                    if clean_line and len(clean_line) > 10:
                        reasons.append(clean_line[:100])
        
        return reasons[:5]  # Top 5 most recent

    def run(self):
        for service in self.services:
            # Get restart count
            restart_output = self.executor.run(
                f"journalctl -u {service} --since '{self.days} days ago' "
                f"| grep -c 'Started' || echo 0"
            )
            
            restart_count = int(restart_output.strip()) if restart_output.strip().isdigit() else 0
            
            if restart_count >= self.restart_threshold:
                reasons = self._get_restart_reasons(service)
                
                details = f"Service '{service}' has restarted {restart_count} times in the last {self.days} days"
                
                if reasons:
                    self.result.warnings.append(
                        Issue(
                            type="Service Instability",
                            severity="MEDIUM",
                            details=details,
                            metadata={"recent_errors": reasons}
                        )
                    )
                    # Add error details to info
                    self.result.info.append(f"Recent errors for {service}:")
                    for reason in reasons:
                        self.result.info.append(f"  • {reason}")
                else:
                    self.result.warnings.append(
                        Issue(
                            type="Service Instability",
                            severity="MEDIUM",
                            details=details
                        )
                    )

        return self.result

