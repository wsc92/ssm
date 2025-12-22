#!/usr/bin/env python3
import sys
import argparse
from pathlib import Path

from src.core.scanner import SystemScanner
from src.core.executor import CommandExecutor
from src.checks import disk, memory, services, ssh, fail2ban, restarts, nginx, database, logins
from src.reporting.console import ConsoleReporter
from src.reporting.json import JSONReporter
from src.utils.logging import setup_logging
from src.config import ScannerConfig

def parse_args():
    parser = argparse.ArgumentParser(
        description='System Health & Security Scanner',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run with default config
  ssm

  # Use custom config file
  ssm --config /etc/scanner/config.yaml

  # Generate config in config directory
  ssm --generate-config

  # Generate config with custom name
  ssm --generate-config my-custom-config.yaml
        """
    )

    # Config file
    parser.add_argument('--config', '-c', metavar='FILE',
                       help='Path to YAML configuration file')
    parser.add_argument('--generate-config', nargs='?', const='scanner.yaml', metavar='FILE',
                       help='Generate default config file (default: config/scanner.yaml)')

    parser.add_argument('--json', metavar='FILE',
                       help='Export results to JSON file')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    parser.add_argument('--quiet', '-q', action='store_true',
                       help='Suppress output unless issues found')
    parser.add_argument('--log-file', metavar='FILE',
                       help='Write logs to file')
    parser.add_argument('--checks', metavar='LIST',
                       help='Comma-separated list of checks to run')
    parser.add_argument('--list-checks', action='store_true',
                       help='List available checks and exit')
    parser.add_argument('--disk-warn', type=int,
                       help='Disk space warning threshold %%')
    parser.add_argument('--disk-crit', type=int,
                       help='Disk space critical threshold %%')
    parser.add_argument('--mem-warn', type=int,
                       help='Memory warning threshold %%')
    parser.add_argument('--mem-crit', type=int,
                       help='Memory critical threshold %%')
    parser.add_argument('--ssh-days', type=int,
                       help='Days to analyze SSH attacks')
    parser.add_argument('--restart-threshold', type=int,
                       help='Service restart warning threshold')

    return parser.parse_args()

def get_available_checks():
    """Return dict of available check names -> (module, class)"""
    return {
        'services': (services, 'FailedServicesCheck'),
        'disk': (disk, 'DiskSpaceCheck'),
        'memory': (memory, 'MemoryCheck'),
        'fail2ban': (fail2ban, 'Fail2BanCheck'),
        'ssh': (ssh, 'SSHAttackCheck'),
        'restarts': (restarts, 'ServiceRestartsCheck'),
        'nginx': (nginx, 'NginxCheck'),
        'database': (database, 'DatabaseCheck'),
        'logins': (logins, 'RecentLoginsCheck'),
    }

def main():
    args = parse_args()

    # Generate config file if requested
    if args.generate_config is not None:
        config = ScannerConfig.default()

        # Determine output path
        if args.generate_config and not args.generate_config.startswith('-'):
            # User provided a filename
            if '/' in args.generate_config:
                # Absolute or relative path provided
                output_path = args.generate_config
            else:
                # Just filename, put in config directory
                config_dir = ScannerConfig.get_default_config_path()
                output_path = str(config_dir / args.generate_config)
        else:
            # Use default location
            config_dir = ScannerConfig.get_default_config_path()
            output_path = str(config_dir / 'scanner.yaml')

        config.to_yaml(output_path)
        print(f"Generated default configuration: {output_path}")
        return 0

    # Load configuration
    if args.config:
        try:
            config = ScannerConfig.from_yaml(args.config)
            print(f"Loaded configuration from: {args.config}")
        except FileNotFoundError as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
        except Exception as e:
            print(f"Error loading config: {e}", file=sys.stderr)
            return 1
    else:
        config = ScannerConfig.default()

    # CLI args override config file
    if args.verbose:
        config.output.verbose = True
    if args.quiet:
        config.output.quiet = True
    if args.json:
        config.output.json_file = args.json
    if args.log_file:
        config.output.log_file = args.log_file
    if args.checks:
        config.enabled_checks = [c.strip() for c in args.checks.split(',')]
    if args.disk_warn is not None:
        config.thresholds.disk_warn = args.disk_warn
    if args.disk_crit is not None:
        config.thresholds.disk_crit = args.disk_crit
    if args.mem_warn is not None:
        config.thresholds.memory_warn = args.mem_warn
    if args.mem_crit is not None:
        config.thresholds.memory_crit = args.mem_crit
    if args.ssh_days is not None:
        config.checks.ssh_days = args.ssh_days
    if args.restart_threshold is not None:
        config.thresholds.restart_threshold = args.restart_threshold

    # Setup logging
    if not config.output.quiet:
        setup_logging(verbose=config.output.verbose, log_file=config.output.log_file)
    else:
        import logging
        logging.basicConfig(level=logging.WARNING)

    # List checks if requested
    if args.list_checks:
        print("Available checks:")
        for name in get_available_checks().keys():
            enabled = "✓" if name in config.enabled_checks else "✗"
            print(f"  [{enabled}] {name}")
        return 0

    # Initialize scanner
    executor = CommandExecutor(timeout=config.command_timeout)
    scanner = SystemScanner(executor)

    # Validate enabled checks
    available = get_available_checks()
    for check_name in config.enabled_checks:
        if check_name not in available:
            print(f"Warning: Unknown check '{check_name}' (skipping)", file=sys.stderr)
            continue

        module, class_name = available[check_name]
        check_class = getattr(module, class_name)

        # Build kwargs from config
        kwargs = {}
        if check_name == 'disk':
            kwargs = {
                'crit_threshold': config.thresholds.disk_crit,
                'warn_threshold': config.thresholds.disk_warn
            }
        elif check_name == 'memory':
            kwargs = {
                'crit_threshold': config.thresholds.memory_crit,
                'warn_threshold': config.thresholds.memory_warn
            }
        elif check_name == 'ssh':
            kwargs = {'days': config.checks.ssh_days}
        elif check_name == 'restarts':
            kwargs = {
                'days': 7,
                'threshold': config.thresholds.restart_threshold
            }
        elif check_name == 'nginx':
            kwargs = {
                'hours': config.checks.nginx_hours,
                'error_threshold': config.thresholds.nginx_error_threshold
            }
        elif check_name == 'database':
            kwargs = {'error_threshold': config.thresholds.db_error_threshold}
        elif check_name == 'logins':
            kwargs = {'hours': config.checks.login_hours}

        scanner.register_check(check_class, **kwargs)

    # Run scan
    result = scanner.run_all()

    # Report
    if config.output.json_file or config.output.format in ['json', 'both']:
        reporter = JSONReporter()
        reporter.generate(result, output_file=config.output.json_file)

    if not config.output.quiet or result.issues or result.warnings:
        if config.output.format in ['console', 'both'] or not config.output.json_file:
            reporter = ConsoleReporter()
            reporter.generate(result)

    # Exit code
    return 1 if result.has_critical() else 0

if __name__ == "__main__":
    sys.exit(main())

