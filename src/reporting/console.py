from datetime import datetime
from src.core.models import ScanResult, Issue

class ConsoleReporter:
    """Format and print scan results to terminal"""

    def generate(self, result: ScanResult):
        """Generate and print the console report"""
        self._print_header(result)
        self._print_issues(result.issues)
        self._print_warnings(result.warnings)
        self._print_info(result.info)
        self._print_footer(result)

    def _print_header(self, result: ScanResult):
        print("\n" + "=" * 80)
        print("📊 SYSTEM HEALTH & SECURITY REPORT")
        print(f"Generated: {result.scan_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80 + "\n")

    def _print_issues(self, issues: list[Issue]):
        if issues:
            print("🚨 CRITICAL ISSUES:")
            print("-" * 80)
            for issue in issues:
                print(f"\n[{issue.severity}] {issue.type}")
                print(f" └─ {issue.details}")

                # Handle special metadata
                if 'services' in issue.metadata:
                    for svc in issue.metadata['services'][:5]:
                        print(f"   • {svc.strip()}")

                if 'top_attackers' in issue.metadata:
                    print(f"\n   Top 10 Attackers:")
                    for attacker in issue.metadata['top_attackers']:
                        print(f"   • {attacker['ip']}: {attacker['attempts']} attempts, "
                              f"{attacker['usernames']} usernames, last: {attacker['last_seen']}")
            print()
        else:
            print("✅ No critical issues found!\n")

    def _print_warnings(self, warnings: list[str]):
        if warnings:
            print("⚠️  WARNINGS:")
            print("-" * 80)
            for warning in warnings:
                print(f" • {warning}")
            print()

    def _print_info(self, info: list[str]):
        if info:
            print("ℹ️  INFORMATION:")
            print("-" * 80)
            for item in info:
                print(f" • {item}")
            print()

    def _print_footer(self, result: ScanResult):
        print("=" * 80)
        print("Scan complete!")
        print("=" * 80 + "\n")
        print(f"Summary: {len(result.issues)} issues, {len(result.warnings)} warnings, {len(result.info)} info")

