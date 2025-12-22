# SSM – Simple System Monitor

SSM (Simple System Monitor) is a modular, extensible Linux system health and security scanner.  
It runs a series of focused checks (services, disk, memory, SSH, fail2ban, etc.), aggregates the results, and outputs a concise report suitable for terminals, automation, and monitoring integration. [file:1]

---

## Features

- **Modular architecture** – Each check is its own module; easy to extend and test independently. [file:1]  
- **Systemd/journalctl aware** – Uses systemd units and journal logs to detect failures, errors, and anomalies. [file:1]  
- **Security focused** – SSH brute-force analysis, fail2ban status, recent SSH logins, nginx error inspection, PostgreSQL health. [file:1]  
- **Configurable thresholds** – Disk and memory thresholds, restart limits, nginx/db error thresholds, and time windows. [file:1]  
- **YAML configuration** – Central config file with sane defaults and per-check tuning. [file:1]  
- **Multiple outputs** – Human-readable console output and structured JSON for automation. [file:1]  
- **CLI-first design** – Select checks, tweak thresholds, change output, and generate config from the command line. [file:1]

---

## Core Checks

SSM currently includes:

- **services** – Failed systemd services (`systemctl list-units --state=failed`). [file:1]  
- **disk** – Disk space usage on `/dev*` filesystems with warning/critical thresholds. [file:1]  
- **memory** – RAM usage derived from `free -m`, with configurable thresholds. [file:1]  
- **fail2ban** – Ensures `fail2ban` is active and reports current/total banned IPs for the `sshd` jail. [file:1]  
- **ssh** – Aggregates SSH failed/invalid logins, counts attacking IPs, and flags brute-force patterns. [file:1]  
- **restarts** – Detects services with frequent restarts from the journal over a time window. [file:1]  
- **nginx** – Scans nginx journal for errors and permission problems. [file:1]  
- **database** – Checks PostgreSQL service status and error volume. [file:1]  
- **logins** – Reports number of successful SSH logins over a recent window. [file:1]

You can enable/disable or parameterize each check via YAML or CLI flags. [file:1]

---

## Project Layout

```
├── config/ # Runtime config & systemd units
│ ├── scanner.yaml # Example/default YAML configuration
│ ├── scanner.service # Optional systemd service
│ └── scanner.timer # Optional systemd timer
├── src/
│ ├── main.py # CLI entrypoint
│ ├── core/
│ │ ├── scanner.py # Orchestrates registered checks
│ │ ├── executor.py # Shell command execution wrapper
│ │ └── models.py # Issue/ScanResult data models
│ ├── checks/ # Individual checks (services, disk, ssh, etc.)
│ ├── reporting/ # Console and JSON reporters
│ ├── config/ # Config dataclasses + YAML loader
│ └── utils/ # Logging setup, helpers
├── tests/ # Unit tests and fixtures
├── install.sh # Optional systemd installation helper
├── pyproject.toml # Build/metadata (Poetry / PEP 517)
└── README.md
```

---
## Installation

### Using Poetry (development)


```
git clone https://github.com/your-user/ssm-simplesystemmonitor.git
```

```
cd ssm-simplesystemmonitor
```

Install dependencies and create venv
```
poetry install
```
Run via poetry
```
poetry run ssm --help
```


This assumes the `ssm` console script is defined in `pyproject.toml` pointing at `src.main:main`. [file:1]

###Using pipx (recommended for system-wide CLI)

```
cd /path/to/ssm-simplesystemmonitor
pipx install .
```


After installation:

```
ssm --help
ssm --list-checks
ssm
```


To update after pulling new changes:

```
cd /path/to/ssm-simplesystemmonitor
pipx reinstall .
```


### Using a simple wrapper script (no packaging required)

```
sudo tee /usr/local/bin/ssm << 'EOF'
#!/bin/bash
cd /home/youruser/dev/ssm-simplesystemmonitor
exec poetry run python -m src.main "$@"
EOF
sudo chmod +x /usr/local/bin/ssm
```

---

## Configuration (YAML)

SSM can run with defaults, but is designed to use a YAML config file. [file:1]

### Generate a default config

Default path (e.g., ./config/scanner.yaml)
```
ssm --generate-config
```
Custom filename in config directory
```
ssm --generate-config my-scanner.yaml
```
Or explicit path
```
ssm --generate-config /etc/ssm/scanner.yaml
```

### Example `config/scanner.yaml`

```
# Threshold settings for system checks
thresholds:
  disk_warn: 80           # Disk space warning threshold (%)
  disk_crit: 90           # Disk space critical threshold (%)
  memory_warn: 80         # Memory usage warning threshold (%)
  memory_crit: 90         # Memory usage critical threshold (%)
  restart_threshold: 20   # Service restart warning threshold
  nginx_error_threshold: 100
  db_error_threshold: 10

# Check-specific configuration
checks:
  enabled: true
  ssh_days: 7            # Days to analyze SSH attacks
  nginx_hours: 24        # Hours to check nginx logs
  login_hours: 24        # Hours to check recent logins

# Output configuration
output:
  format: console        # Options: console, json, both
  json_file: null        # Path to JSON output file (null = disabled)
  log_file: null         # Path to log file (null = disabled)
  verbose: false         # Enable verbose logging
  quiet: false           # Suppress output unless issues found

# List of checks to run (comment out to disable)
enabled_checks:
  - services
  - disk
  - memory
  - fail2ban
  - ssh
  - restarts
  - nginx
  - database
  - logins

# Command execution timeout (seconds)
command_timeout: 30command_timeout: 30
```


Run with a config:
```
ssm --config config/scanner.yaml
```


CLI flags override config values. [file:1]

---

## CLI Usage

Some common commands:

Basic scan with defaults
```
ssm
```
Use a specific config file
```
ssm --config config/scanner.yaml
```

List all available checks and whether they are enabled in the current config
```
ssm --config config/scanner.yaml --list-checks
```
Run only a subset of checks
```
ssm --checks disk,memory,ssh
```
Generate JSON report (no config needed)
```
ssm --json /tmp/ssm-report.json
```
Quiet mode: only output if issues/warnings are found
```
ssm --quiet --json /var/log/ssm/report.json
```
Custom thresholds via CLI overrides
```
ssm --disk-warn 75 --disk-crit 90 --mem-crit 95
```
More verbose logging with file output
```
ssm --verbose --log-file /var/log/ssm/scanner.log
```


Exit code is non-zero if critical issues are detected, making it suitable for CI/CD and monitoring hooks. [file:1]

---

## Automation

### systemd service + timer (optional)

The repository includes example units in `config/` that can be installed to run SSM periodically. [file:1]

```
sudo cp config/scanner.service /etc/systemd/system/
sudo cp config/scanner.timer /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now scanner.timer

#Check scheduled runs

systemctl list-timers | grep scanner
#View last runs

journalctl -u scanner.service -n 50
```


###Cron job example
Run every 6 hours, write JSON, only output on issues
```
0 */6 * * * /usr/local/bin/ssm --quiet --json /var/log/ssm/report.json
```

---

##Development

Install dev dependencies
```
poetry install
```
Run tests
```
poetry run pytest
```
Format code (if using black)
```
poetry run black src/ tests/
```
Type-check (if using mypy)
```
poetry run mypy src/
```


### Adding a new check

1. Create `src/checks/mycheck.py`.  
2. Subclass the shared `BaseCheck` and implement `name` + `run()`. [file:1]  
3. Register it in the main CLI wiring so it can be toggled via config/CLI. [file:1]  
4. Add unit tests under `tests/test_checks/`.  

The design keeps each check’s logic and thresholds localized while sharing command execution, reporting, and configuration infrastructure. [file:1]

---

## License

Copyright (c) 2025 William Craig

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the "Software"), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.

