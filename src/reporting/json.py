import json
from datetime import datetime
from src.core.models import ScanResult, Issue

class JSONReporter:
    """Export scan results as JSON"""

    def generate(self, result: ScanResult, output_file: str = None):
        """Generate JSON report"""
        data = {
            "scan_time": result.scan_time.isoformat(),
            "summary": {
                "issues": len(result.issues),
                "warnings": len(result.warnings),
                "info": len(result.info),
                "has_critical": result.has_critical()
            },
            "issues": [self._serialize_issue(issue) for issue in result.issues],
            "warnings": result.warnings,
            "info": result.info
        }

        json_str = json.dumps(data, indent=2)

        if output_file:
            with open(output_file, 'w') as f:
                f.write(json_str)
            print(f"JSON report written to: {output_file}")
        else:
            print(json_str)

        return data

    def _serialize_issue(self, issue: Issue) -> dict:
        return {
            "type": issue.type,
            "severity": issue.severity,
            "details": issue.details,
            "timestamp": issue.timestamp.isoformat(),
            "metadata": self._serialize_metadata(issue.metadata)
        }

    def _serialize_metadata(self, metadata: dict) -> dict:
        """Convert non-JSON-serializable types"""
        result = {}
        for key, value in metadata.items():
            if isinstance(value, set):
                result[key] = list(value)
            else:
                result[key] = value
        return result

