from src.checks.base import BaseCheck
from src.core.models import Issue

class FailedServicesCheck(BaseCheck):
    @property
    def name(self) -> str:
        return "Failed Services"

    def run(self):
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

