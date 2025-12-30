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
            f"sudo journalctl -u {service_name} --since '{self.days} days ago' "
            f"-n 150 --no-pager"
        )

        reasons = []
        seen_errors = set()

        if output and 'No entries' not in output:
            lines = output.strip().split('\n')

            for line in lines:
                # Extract message after systemd prefix
                msg_match = re.search(r'\[\d+\]:\s*(.+)', line)
                if not msg_match:
                    continue

                msg = msg_match.group(1).strip()

                # Python exceptions
                if re.search(r'\w*(Error|Exception):', msg):
                    match = re.search(r'(\w*(?:Error|Exception)):\s*(.+)', msg)
                    if match:
                        error_key = match.group(0)[:100]
                        if error_key not in seen_errors:
                            reasons.append(match.group(0)[:100])
                            seen_errors.add(error_key)

                # Segmentation faults (C/C++)
                elif 'segmentation fault' in msg.lower() or 'sigsegv' in msg.lower():
                    if 'segfault' not in seen_errors:
                        reasons.append("Segmentation fault (SIGSEGV)")
                        seen_errors.add('segfault')

                # Signal terminations
                elif re.search(r'signal \d+|killed by signal|terminated by signal', msg.lower()):
                    match = re.search(r'(signal \d+|SIG\w+)', msg, re.IGNORECASE)
                    if match:
                        sig = match.group(1)
                        if sig not in seen_errors:
                            reasons.append(f"Terminated by {sig}")
                            seen_errors.add(sig)

                # Assertion failures (C/C++)
                elif 'assertion' in msg.lower() and 'failed' in msg.lower():
                    match = re.search(r'assertion.*failed.*', msg, re.IGNORECASE)
                    if match and 'assertion' not in seen_errors:
                        reasons.append(match.group(0)[:100])
                        seen_errors.add('assertion')

                # Panic (Rust/Go)
                elif 'panic' in msg.lower() or 'fatal error' in msg.lower():
                    if 'panic' not in seen_errors:
                        reasons.append(msg[:100])
                        seen_errors.add('panic')

                # Core dumps
                elif 'core dump' in msg.lower():
                    if 'core_dump' not in seen_errors:
                        reasons.append("Core dumped")
                        seen_errors.add('core_dump')

                # Out of memory
                elif 'out of memory' in msg.lower() or 'oom' in msg.lower():
                    if 'oom' not in seen_errors:
                        reasons.append("Out of memory (OOM)")
                        seen_errors.add('oom')

                # Worker/process failures
                elif 'worker failed' in msg.lower() or 'process exited' in msg.lower():
                    match = re.search(r'(worker failed to boot|process exited.*code \d+)', msg, re.IGNORECASE)
                    if match:
                        key = match.group(1)[:50]
                        if key not in seen_errors:
                            reasons.append(match.group(1))
                            seen_errors.add(key)

                # Generic fatal/error lines with context
                elif re.search(r'\b(fatal|critical|abort)', msg.lower()):
                    key = msg[:80]
                    if key not in seen_errors and len(msg) > 20:
                        reasons.append(msg[:100])
                        seen_errors.add(key)

                if len(reasons) >= 5:
                    break

        return reasons

    def run(self):
        for service in self.services:
            restart_output = self.executor.run(
                f"journalctl -u {service} --since '{self.days} days ago' "
                f"| grep -c 'Started' || echo 0"
            )

            restart_count = int(restart_output.strip()) if restart_output.strip().isdigit() else 0

            if restart_count >= self.restart_threshold:
                reasons = self._get_restart_reasons(service)

                if reasons:
                    self.result.info.append(f"Crash diagnostics for {service}:")
                    for reason in reasons:
                        self.result.info.append(f"  • {reason}")
                else:
                    self.result.info.append(
                        f"No detailed errors found. Check: sudo journalctl -u {service} -n 100"
                    )

        return self.result

