import re
from src.checks.base import BaseCheck
from src.core.models import Issue

class DatabaseCheck(BaseCheck):
    def __init__(self, executor, error_threshold=10):
        super().__init__(executor)
        self.error_threshold = error_threshold

    @property
    def name(self) -> str:
        return "PostgreSQL Status"

    def _get_postgres_errors(self) -> list:
        """Extract detailed PostgreSQL error messages from logs."""
        output = self.executor.run(
            "journalctl -u postgresql --since '24 hours ago' --no-pager "
            "| grep -i -E 'error|fatal|panic' | tail -100"
        )

        error_counts = {}  # Track error counts
        error_messages = {}  # Map normalized key to display message

        if output and output.strip():
            lines = output.strip().split('\n')

            for line in lines:
                # Extract ERROR/FATAL/PANIC message only (strip timestamp, PID)
                msg_match = re.search(r'\[\d+\]\s+(ERROR|FATAL|PANIC):\s*(.+)', line)
                if not msg_match:
                    continue

                msg = msg_match.group(2).strip()

                # Normalize: remove character positions, line numbers, specific values
                normalized = re.sub(r'at character \d+', '', msg)
                normalized = re.sub(r'line \d+', 'line N', normalized)
                normalized = re.sub(r'\d{4}-\d{2}-\d{2}', 'DATE', normalized)
                normalized = normalized.strip()

                error_key = None
                display_msg = None

                # Connection errors
                if re.search(r'connection.*?(refused|failed|timeout)', normalized, re.IGNORECASE):
                    error_key = 'connection_error'
                    display_msg = f"Connection issue: {normalized[:80]}"

                # Authentication failures
                elif re.search(r'authentication failed|password.*failed', normalized, re.IGNORECASE):
                    match = re.search(r'for user "([^"]+)"', normalized)
                    user = match.group(1) if match else 'unknown'
                    error_key = f'auth_{user}'
                    display_msg = f"Authentication failed for user '{user}'"

                # Syntax errors
                elif re.search(r'syntax error', normalized, re.IGNORECASE):
                    error_key = 'syntax'
                    display_msg = f"SQL syntax error: {normalized[:80]}"

                # Lock/deadlock issues
                elif re.search(r'deadlock|lock timeout', normalized, re.IGNORECASE):
                    error_key = 'deadlock'
                    display_msg = "Deadlock detected"

                # Disk/storage issues
                elif re.search(r'no space left|disk full|could not write', normalized, re.IGNORECASE):
                    error_key = 'disk'
                    display_msg = "Disk/storage issue detected"

                # Out of memory
                elif re.search(r'out of memory|cannot allocate', normalized, re.IGNORECASE):
                    error_key = 'oom'
                    display_msg = "Out of memory error"

                # Corruption
                elif re.search(r'corruption|corrupt|invalid page', normalized, re.IGNORECASE):
                    error_key = 'corruption'
                    display_msg = f"Data corruption: {normalized[:70]}"

                # Missing relation/table
                elif 'does not exist' in normalized:
                    match = re.search(r'relation "([^"]+)" does not exist', normalized)
                    if match:
                        table = match.group(1)
                        error_key = f'missing_{table}'
                        display_msg = f'Missing table/relation: "{table}"'
                    else:
                        error_key = 'missing_relation'
                        display_msg = "Missing table/relation"

                # Generic errors
                else:
                    error_key = normalized[:80]
                    display_msg = normalized[:100]

                # Count this error
                if error_key:
                    error_counts[error_key] = error_counts.get(error_key, 0) + 1
                    if error_key not in error_messages:
                        error_messages[error_key] = display_msg

        # Format output with counts, sorted by frequency
        result = []
        for error_key, count in sorted(error_counts.items(), key=lambda x: x[1], reverse=True)[:5]:
            msg = error_messages[error_key]
            if count > 1:
                result.append(f"{msg} ({count}x)")
            else:
                result.append(msg)

        return result

    def run(self):
        # Check if PostgreSQL is running
        status = self.executor.run("systemctl is-active postgresql")

        if "active" not in status:
            self.result.issues.append(Issue(
                type="Database",
                severity="CRITICAL",
                details="PostgreSQL is not running"
            ))
            return self.result

        # Check for errors in postgres logs
        cmd = "journalctl -u postgresql --since '24 hours ago' --no-pager | grep -i error | wc -l"
        error_count = self.executor.run(cmd).strip()

        if error_count and int(error_count) > self.error_threshold:
            self.result.warnings.append(
                f"PostgreSQL has {error_count} errors in the last 24 hours"
            )

            # Get detailed error information
            errors = self._get_postgres_errors()
            if errors:
                self.result.info.append("Recent PostgreSQL errors:")
                for error in errors:
                    self.result.info.append(f"  • {error}")

        return self.result

