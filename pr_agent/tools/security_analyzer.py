"""
Security Analyzer

Analyzes code for security vulnerabilities:
- Secrets in code
- Sensitive data exposure
- Unsafe deserialization
- Path traversal
- XSS vulnerabilities
- SSRF patterns
"""

import re
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Any

logger = logging.getLogger(__name__)


class SecuritySeverity(Enum):
    """Severity levels for security findings."""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


@dataclass
class SecurityFinding:
    """Represents a security-related finding."""
    rule_id: str
    message: str
    severity: SecuritySeverity
    file_path: str
    line_start: int
    line_end: int | None = None
    code_snippet: str | None = None
    suggestion: str | None = None
    cwe_id: str | None = None
    metadata: dict[str, Any] | None = None
    
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "rule_id": self.rule_id,
            "message": self.message,
            "severity": self.severity.value,
            "file_path": self.file_path,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "code_snippet": self.code_snippet,
            "suggestion": self.suggestion,
            "cwe_id": self.cwe_id,
            "metadata": self.metadata or {},
        }


class SecurityAnalyzer:
    """
    Analyzer for security vulnerabilities in code.
    
    Detects:
    - Hardcoded secrets and credentials
    - Sensitive data in logs
    - Unsafe deserialization
    - Path traversal vulnerabilities
    - XSS patterns
    - SSRF patterns
    - Insecure cryptography
    """
    
    def __init__(self):
        self._findings: list[SecurityFinding] = []
    
    async def analyze(self, content: str, file_path: str) -> list[SecurityFinding]:
        """
        Analyze file content for security issues.
        
        Args:
            content: File content
            file_path: Path to the file
            
        Returns:
            List of security findings
        """
        self._findings.clear()
        lines = content.split('\n')
        
        self._check_hardcoded_secrets(content, file_path, lines)
        self._check_sensitive_data_logging(content, file_path, lines)
        self._check_unsafe_deserialization(content, file_path, lines)
        self._check_path_traversal(content, file_path, lines)
        self._check_xss_patterns(content, file_path, lines)
        self._check_ssrf_patterns(content, file_path, lines)
        self._check_insecure_crypto(content, file_path, lines)
        self._check_command_injection(content, file_path, lines)
        self._check_insecure_random(content, file_path, lines)
        
        return self._findings.copy()
    
    def _add_finding(
        self,
        rule_id: str,
        message: str,
        severity: SecuritySeverity,
        file_path: str,
        line_start: int,
        line_end: int | None = None,
        code_snippet: str | None = None,
        suggestion: str | None = None,
        cwe_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a finding to the list."""
        self._findings.append(SecurityFinding(
            rule_id=rule_id,
            message=message,
            severity=severity,
            file_path=file_path,
            line_start=line_start,
            line_end=line_end,
            code_snippet=code_snippet,
            suggestion=suggestion,
            cwe_id=cwe_id,
            metadata=metadata,
        ))
    
    def _check_hardcoded_secrets(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for hardcoded secrets and credentials."""
        if 'test' in file_path.lower() or 'mock' in file_path.lower() or 'example' in file_path.lower():
            return
        
        secret_patterns = [
            (re.compile(r'api[_-]?key\s*[=:]\s*[\'"][A-Za-z0-9_\-]{20,}[\'"]', re.I), "API key"),
            (re.compile(r'secret\s*[=:]\s*[\'"][A-Za-z0-9_\-]{10,}[\'"]', re.I), "Secret"),
            (re.compile(r'password\s*[=:]\s*[\'"][^\'"]{8,}[\'"]', re.I), "Password"),
            (re.compile(r'token\s*[=:]\s*[\'"][A-Za-z0-9_\-\.]{20,}[\'"]', re.I), "Token"),
            (re.compile(r'private[_-]?key\s*[=:]\s*[\'"]', re.I), "Private key"),
            (re.compile(r'aws[_-]?access[_-]?key\s*[=:]\s*[\'"]AKIA', re.I), "AWS access key"),
            (re.compile(r'-----BEGIN\s+(RSA\s+)?PRIVATE\s+KEY-----'), "Private key block"),
            (re.compile(r'ghp_[A-Za-z0-9]{36}'), "GitHub personal access token"),
            (re.compile(r'gho_[A-Za-z0-9]{36}'), "GitHub OAuth token"),
            (re.compile(r'sk-[A-Za-z0-9]{48}'), "OpenAI API key"),
        ]
        
        for i, line in enumerate(lines, start=1):
            for pattern, secret_type in secret_patterns:
                if pattern.search(line):
                    self._add_finding(
                        rule_id="SEC001",
                        message=f"Potential hardcoded {secret_type} detected",
                        severity=SecuritySeverity.CRITICAL,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=self._mask_secret(line.strip()),
                        suggestion="Use environment variables or secret manager instead",
                        cwe_id="CWE-798",
                    )
                    break
    
    def _mask_secret(self, line: str) -> str:
        """Mask potential secrets in code snippets."""
        masked = re.sub(r'([\'"])[A-Za-z0-9_\-\.]{10,}([\'"])', r'\1***MASKED***\2', line)
        return masked
    
    def _check_sensitive_data_logging(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for sensitive data being logged."""
        sensitive_log_patterns = [
            (re.compile(r'log.*password', re.I), "password"),
            (re.compile(r'log.*token', re.I), "token"),
            (re.compile(r'log.*secret', re.I), "secret"),
            (re.compile(r'log.*credit.?card', re.I), "credit card"),
            (re.compile(r'log.*ssn', re.I), "SSN"),
            (re.compile(r'console\.(log|info|debug).*password', re.I), "password"),
            (re.compile(r'console\.(log|info|debug).*token', re.I), "token"),
        ]
        
        for i, line in enumerate(lines, start=1):
            for pattern, data_type in sensitive_log_patterns:
                if pattern.search(line):
                    self._add_finding(
                        rule_id="SEC002",
                        message=f"Potential {data_type} being logged",
                        severity=SecuritySeverity.HIGH,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion=f"Remove {data_type} from log output or use masking",
                        cwe_id="CWE-532",
                    )
                    break
    
    def _check_unsafe_deserialization(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for unsafe deserialization patterns."""
        unsafe_patterns = [
            (re.compile(r'eval\s*\('), "eval()"),
            (re.compile(r'Function\s*\('), "Function constructor"),
            (re.compile(r'unserialize\s*\('), "PHP unserialize()"),
            (re.compile(r'pickle\.loads?\s*\('), "Python pickle"),
            (re.compile(r'yaml\.load\s*\([^)]*\)(?!.*Loader)'), "YAML load without safe loader"),
            (re.compile(r'JSON\.parse\s*\([^)]*\)\s*\)'), "Nested JSON.parse"),
        ]
        
        for i, line in enumerate(lines, start=1):
            for pattern, func_name in unsafe_patterns:
                if pattern.search(line):
                    self._add_finding(
                        rule_id="SEC003",
                        message=f"Unsafe deserialization: {func_name}",
                        severity=SecuritySeverity.CRITICAL,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion="Avoid deserializing untrusted data. Use safe alternatives.",
                        cwe_id="CWE-502",
                    )
                    break
    
    def _check_path_traversal(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for path traversal vulnerabilities."""
        path_patterns = [
            (re.compile(r'(readFile|writeFile|unlink|rmdir)\s*\([^)]*\+'), "File operation with concatenation"),
            (re.compile(r'(readFile|writeFile)\s*\([^)]*\$\{'), "File operation with template literal"),
            (re.compile(r'path\.join\s*\([^)]*req\.(params|query|body)'), "path.join with user input"),
            (re.compile(r'fs\.\w+\s*\([^)]*req\.(params|query|body)'), "fs operation with user input"),
            (re.compile(r'\.\.\/'), "Relative path traversal pattern"),
        ]
        
        for i, line in enumerate(lines, start=1):
            for pattern, description in path_patterns:
                if pattern.search(line):
                    self._add_finding(
                        rule_id="SEC004",
                        message=f"Potential path traversal: {description}",
                        severity=SecuritySeverity.HIGH,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion="Validate and sanitize file paths. Use path.resolve() and check against allowed directories.",
                        cwe_id="CWE-22",
                    )
                    break
    
    def _check_xss_patterns(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for XSS vulnerabilities."""
        xss_patterns = [
            (re.compile(r'innerHTML\s*='), "innerHTML assignment"),
            (re.compile(r'outerHTML\s*='), "outerHTML assignment"),
            (re.compile(r'document\.write\s*\('), "document.write()"),
            (re.compile(r'dangerouslySetInnerHTML'), "React dangerouslySetInnerHTML"),
            (re.compile(r'\$\(\s*[\'"]<'), "jQuery HTML injection"),
        ]
        
        for i, line in enumerate(lines, start=1):
            for pattern, description in xss_patterns:
                if pattern.search(line):
                    self._add_finding(
                        rule_id="SEC005",
                        message=f"Potential XSS vulnerability: {description}",
                        severity=SecuritySeverity.HIGH,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion="Sanitize user input before rendering. Use textContent instead of innerHTML.",
                        cwe_id="CWE-79",
                    )
                    break
    
    def _check_ssrf_patterns(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for SSRF vulnerabilities."""
        ssrf_patterns = [
            (re.compile(r'(fetch|axios|request)\s*\([^)]*\+'), "HTTP request with concatenation"),
            (re.compile(r'(fetch|axios|request)\s*\([^)]*\$\{'), "HTTP request with template literal"),
            (re.compile(r'(fetch|axios|request)\s*\([^)]*req\.(params|query|body)'), "HTTP request with user input"),
            (re.compile(r'http\.get\s*\([^)]*\+'), "http.get with concatenation"),
        ]
        
        for i, line in enumerate(lines, start=1):
            for pattern, description in ssrf_patterns:
                if pattern.search(line):
                    self._add_finding(
                        rule_id="SEC006",
                        message=f"Potential SSRF vulnerability: {description}",
                        severity=SecuritySeverity.HIGH,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion="Validate and whitelist URLs. Don't allow user-controlled URLs to internal services.",
                        cwe_id="CWE-918",
                    )
                    break
    
    def _check_insecure_crypto(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for insecure cryptographic patterns."""
        crypto_patterns = [
            (re.compile(r'createHash\s*\(\s*[\'"]md5[\'"]'), "MD5 hash"),
            (re.compile(r'createHash\s*\(\s*[\'"]sha1[\'"]'), "SHA1 hash"),
            (re.compile(r'createCipher\s*\(\s*[\'"]des', re.I), "DES encryption"),
            (re.compile(r'createCipher\s*\(\s*[\'"]rc4', re.I), "RC4 encryption"),
            (re.compile(r'Math\.random\s*\(\s*\).*password', re.I), "Math.random for security"),
            (re.compile(r'Math\.random\s*\(\s*\).*token', re.I), "Math.random for tokens"),
        ]
        
        for i, line in enumerate(lines, start=1):
            for pattern, description in crypto_patterns:
                if pattern.search(line):
                    self._add_finding(
                        rule_id="SEC007",
                        message=f"Insecure cryptography: {description}",
                        severity=SecuritySeverity.MEDIUM,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion="Use secure algorithms: SHA-256+, AES-256, crypto.randomBytes()",
                        cwe_id="CWE-327",
                    )
                    break
    
    def _check_command_injection(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for command injection vulnerabilities."""
        cmd_patterns = [
            (re.compile(r'exec\s*\([^)]*\+'), "exec with concatenation"),
            (re.compile(r'exec\s*\([^)]*\$\{'), "exec with template literal"),
            (re.compile(r'spawn\s*\([^)]*\+'), "spawn with concatenation"),
            (re.compile(r'system\s*\([^)]*\$'), "PHP system with variable"),
            (re.compile(r'shell_exec\s*\([^)]*\$'), "PHP shell_exec with variable"),
            (re.compile(r'subprocess\.(run|call|Popen)\s*\([^)]*\+'), "Python subprocess with concatenation"),
        ]
        
        for i, line in enumerate(lines, start=1):
            for pattern, description in cmd_patterns:
                if pattern.search(line):
                    self._add_finding(
                        rule_id="SEC008",
                        message=f"Potential command injection: {description}",
                        severity=SecuritySeverity.CRITICAL,
                        file_path=file_path,
                        line_start=i,
                        code_snippet=line.strip(),
                        suggestion="Avoid shell commands with user input. Use parameterized commands or libraries.",
                        cwe_id="CWE-78",
                    )
                    break
    
    def _check_insecure_random(self, content: str, file_path: str, lines: list[str]) -> None:
        """Check for insecure random number generation."""
        random_patterns = [
            (re.compile(r'Math\.random\s*\(\s*\)'), "Math.random()"),
            (re.compile(r'random\.random\s*\(\s*\)'), "Python random.random()"),
            (re.compile(r'rand\s*\(\s*\)'), "PHP rand()"),
        ]
        
        security_context_patterns = [
            re.compile(r'(token|secret|password|key|salt|nonce|iv)', re.I),
        ]
        
        for i, line in enumerate(lines, start=1):
            for pattern, func_name in random_patterns:
                if pattern.search(line):
                    context = '\n'.join(lines[max(0, i-3):min(len(lines), i+3)])
                    if any(p.search(context) for p in security_context_patterns):
                        self._add_finding(
                            rule_id="SEC009",
                            message=f"Insecure random number generator ({func_name}) used in security context",
                            severity=SecuritySeverity.HIGH,
                            file_path=file_path,
                            line_start=i,
                            code_snippet=line.strip(),
                            suggestion="Use crypto.randomBytes() (Node.js), secrets module (Python), or random_bytes() (PHP)",
                            cwe_id="CWE-330",
                        )
                        break


_analyzer: SecurityAnalyzer | None = None


def get_security_analyzer() -> SecurityAnalyzer:
    """Get the global security analyzer instance."""
    global _analyzer
    if _analyzer is None:
        _analyzer = SecurityAnalyzer()
    return _analyzer
