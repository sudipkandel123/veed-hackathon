import os
import re
from typing import List, Dict, Tuple
import json

class APIScanner:
    def __init__(self):
        # Common API endpoint patterns
        self.api_patterns = [
            r'https?://[^\s<>"\']+?/api/',
            r'https?://[^\s<>"\']+?/v\d+/',
            r'https?://[^\s<>"\']+?/graphql',
            r'https?://[^\s<>"\']+?/rest/',
            r'https?://[^\s<>"\']+?/swagger',
            r'https?://[^\s<>"\']+?/openapi',
            r'https?://[^\s<>"\']+?/docs',
        ]
        
        # Common API key patterns
        self.api_key_patterns = [
            r'api[_-]?key["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_-]+["\']?',
            r'apikey["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_-]+["\']?',
            r'secret["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_-]+["\']?',
            r'password["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_-]+["\']?',
            r'token["\']?\s*[:=]\s*["\']?[a-zA-Z0-9_-]+["\']?',
        ]
        
        # File extensions to scan
        self.scan_extensions = {
            '.py', '.js', '.jsx', '.ts', '.tsx', '.json', '.env',
            '.yaml', '.yml', '.html', '.css', '.md', '.txt'
        }
        
        # Directories to exclude
        self.exclude_dirs = {
            'node_modules', '.git', '__pycache__', 'venv', 'env',
            '.vscode', '.idea', 'dist', 'build', 'frontend'
        }

    def scan_file(self, file_path: str) -> List[Dict[str, str]]:
        """Scan a single file for API endpoints and sensitive information."""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                line_number = 0
                
                for line in content.split('\n'):
                    line_number += 1
                    
                    # Check for API endpoints
                    for pattern in self.api_patterns:
                        matches = re.finditer(pattern, line, re.IGNORECASE)
                        for match in matches:
                            findings.append({
                                'type': 'API Endpoint',
                                'file': file_path,
                                'line': line_number,
                                'content': line.strip(),
                                'match': match.group()
                            })
                    
                    # Check for API keys and sensitive information
                    for pattern in self.api_key_patterns:
                        matches = re.finditer(pattern, line, re.IGNORECASE)
                        for match in matches:
                            findings.append({
                                'type': 'Potential API Key',
                                'file': file_path,
                                'line': line_number,
                                'content': line.strip(),
                                'match': match.group()
                            })
                            
        except Exception as e:
            print(f"Error scanning file {file_path}: {str(e)}")
            
        return findings

    def scan_directory(self, directory: str) -> List[Dict[str, str]]:
        """Recursively scan a directory for API endpoints and sensitive information."""
        all_findings = []
        
        for root, dirs, files in os.walk(directory):
            # Skip excluded directories
            dirs[:] = [d for d in dirs if d not in self.exclude_dirs]
            
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()
                
                if file_ext in self.scan_extensions:
                    findings = self.scan_file(file_path)
                    all_findings.extend(findings)
        
        return all_findings

    def generate_report(self, findings: List[Dict[str, str]]) -> str:
        """Generate a formatted report of the findings."""
        if not findings:
            return "No exposed APIs or sensitive information found."
        
        report = []
        report.append("=== API Security Scan Report ===\n")
        
        # Group findings by type
        grouped_findings = {}
        for finding in findings:
            finding_type = finding['type']
            if finding_type not in grouped_findings:
                grouped_findings[finding_type] = []
            grouped_findings[finding_type].append(finding)
        
        # Generate report sections
        for finding_type, type_findings in grouped_findings.items():
            report.append(f"\n## {finding_type} ({len(type_findings)} found)")
            for finding in type_findings:
                report.append(f"\nFile: {finding['file']}")
                report.append(f"Line: {finding['line']}")
                report.append(f"Content: {finding['content']}")
                report.append(f"Match: {finding['match']}")
                report.append("-" * 50)
        
        return "\n".join(report)

def main():
    # Initialize scanner
    scanner = APIScanner()
    
    # Get the current directory
    current_dir = os.getcwd()
    
    print(f"Scanning directory: {current_dir}")
    print("This may take a few moments...")
    
    # Perform scan
    findings = scanner.scan_directory(current_dir)
    
    # Generate and print report
    report = scanner.generate_report(findings)
    print("\n" + report)
    
    # Save report to file
    report_file = "api_security_report.txt"
    with open(report_file, 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\nReport has been saved to: {report_file}")

if __name__ == "__main__":
    main()
