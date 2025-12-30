from dataclasses import dataclass, field, asdict
from typing import Optional, List
from pathlib import Path
import yaml

@dataclass
class ThresholdsConfig:
    """Threshold configuration for various checks"""
    disk_warn: int = 80
    disk_crit: int = 90
    memory_warn: int = 80
    memory_crit: int = 90
    restart_threshold: int = 20
    nginx_error_threshold: int = 100
    db_error_threshold: int = 10

@dataclass
class CheckConfig:
    """Per-check configuration"""
    enabled: bool = True
    ssh_days: int = 7
    nginx_hours: int = 24
    login_hours: int = 24

@dataclass
class OutputConfig:
    """Output and reporting configuration"""
    format: str = "console"  # console, json, both
    json_file: Optional[str] = None
    log_file: Optional[str] = None
    verbose: bool = False
    quiet: bool = False

@dataclass
class ScannerConfig:
    """Main scanner configuration"""
    thresholds: ThresholdsConfig = field(default_factory=ThresholdsConfig)
    checks: CheckConfig = field(default_factory=CheckConfig)
    output: OutputConfig = field(default_factory=OutputConfig)
    enabled_checks: List[str] = field(default_factory=lambda: [
        'services', 'disk', 'memory', 'fail2ban', 'ssh',
        'restarts', 'service_details' 'nginx', 'database', 'logins'
    ])
    command_timeout: int = 30
    
    @classmethod
    def from_yaml(cls, path: str) -> 'ScannerConfig':
        """Load configuration from YAML file"""
        config_path = Path(path)
        
        if not config_path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        
        with open(config_path, 'r') as f:
            data = yaml.safe_load(f)
        
        if not data:
            return cls()
        
        # Parse nested configs
        thresholds = ThresholdsConfig(**data.get('thresholds', {}))
        checks = CheckConfig(**data.get('checks', {}))
        output = OutputConfig(**data.get('output', {}))
        
        return cls(
            thresholds=thresholds,
            checks=checks,
            output=output,
            enabled_checks=data.get('enabled_checks', cls().enabled_checks),
            command_timeout=data.get('command_timeout', 30)
        )
    
    def to_yaml(self, path: str):
        """Save configuration to YAML file"""
        config_path = Path(path)
        
        # Create parent directory if it doesn't exist
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        config_dict = {
            'thresholds': asdict(self.thresholds),
            'checks': asdict(self.checks),
            'output': asdict(self.output),
            'enabled_checks': self.enabled_checks,
            'command_timeout': self.command_timeout
        }
        
        with open(config_path, 'w') as f:
            yaml.dump(config_dict, f, default_flow_style=False, sort_keys=False)
    
    @classmethod
    def default(cls) -> 'ScannerConfig':
        """Create default configuration"""
        return cls()
    
    @staticmethod
    def get_default_config_path() -> Path:
        """Get the default config directory location"""
        # Try to find project root (where pyproject.toml lives)
        current = Path(__file__).resolve()
        
        # Walk up to find project root
        for parent in current.parents:
            if (parent / 'pyproject.toml').exists():
                return parent / 'config'
        
        # Fallback to current directory
        return Path.cwd() / 'config'

