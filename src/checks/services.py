from src.checks.base import BaseCheck
from src.core.models import Issue

class FailedServicesCheck(BaseCheck):
    @property
    def name(self) -> str:
        return "Failed Services"

    def _get_service_restart_details(self, service_name: str, days: int = 7) -> dict:
        """Get detailed restart information for a service."""
        details = {
            'restart_count': 0,
            'recent_errors': [],
            'status': None
        }
        
        # Get restart count
        since_date = f"{days} days ago"
        journal_output = self.executor.run(
            f"journalctl -u {service_name} --since '{since_date}' "
            f"| grep -E 'Started|Stopped|Failed|Main process exited' | tail -20"
        )
        
        if journal_output:
            lines = journal_output.strip().split('\n')
            details['restart_count'] = len([l for l in lines if 'Started' in l])
            
            # Get recent error messages
            error_output = self.executor.run(
                f"journalctl -u {service_name} --since '{since_date}' "
                f"-p err -n 5 --no-pager"
            )
            if error_output and 'No entries' not in error_output:
                details['recent_errors'] = [
                    line.strip() for line in error_output.split('\n')
                    if line.strip() and not line.startswith('--')
                ][:3]
        
        # Get current status
        status_output = self.executor.run(f"systemctl status {service_name} --no-pager")
        if status_output:
            details['status'] = 'active' if 'active (running)' in status_output else 'inactive'
        
        return details

    def run(self):
        # Check for failed services
        output = self.executor.run("systemctl list-units --state=failed --no-pager")

        if "0 loaded units listed" not in output and output.strip():
            failed = [line for line in output.split('\n')
                     if '.service' in line and 'failed' in line]

            if failed:
                self.result.issues.append(Issue(
                    type="Failed Services",
                    severity="HIGH",
                    details=f"Found {len(failed)} failed service(s)",
                    metadata={"services": failed}
                ))

        return self.result

