---
name: security-audit
description: Use when performing security audits. Covers vulnerability assessment, penetration testing, threat modeling, and compliance.
---

# Security Audit Skill

## Instructions

A security audit is a systematic evaluation of the security posture of an application, system, or organization. It involves identifying vulnerabilities, assessing risks, verifying compliance with security standards, and recommending remediation measures. This skill covers vulnerability assessment, penetration testing, threat modeling, security code review, and compliance auditing.

### Types of Security Audits

| Type | Focus | Methodology |
|------|-------|-------------|
| Vulnerability Assessment | Identifying known vulnerabilities | Automated scanning |
| Penetration Testing | Exploiting vulnerabilities | Manual + automated |
| Code Review | Source code security analysis | Manual review + SAST |
| Architecture Review | Design-level security | Threat modeling |
| Compliance Audit | Regulatory compliance | Checklist + evidence |
| Red Team | Full-scope attack simulation | Adversarial simulation |

### Security Audit Process

1. **Scope Definition**: Define what is in scope (systems, applications, data)
2. **Reconnaissance**: Gather information about the target
3. **Threat Modeling**: Identify potential threats and attack vectors
4. **Vulnerability Analysis**: Identify and classify vulnerabilities
5. **Exploitation (optional)**: Attempt to exploit vulnerabilities
6. **Reporting**: Document findings with severity ratings
7. **Remediation**: Fix identified vulnerabilities
8. **Verification**: Confirm fixes are effective

### Common Security Frameworks

| Framework | Purpose |
|-----------|---------|
| OWASP Top 10 | Web application security risks |
| NIST SP 800-53 | Security and privacy controls |
| ISO 27001 | Information security management |
| CIS Benchmarks | System configuration guidelines |
| PCI DSS | Payment card industry security |
| SOC 2 | Service organization controls |
| MITRE ATT&CK | Adversary tactics and techniques |

## Examples

### Example 1: Threat Modeling with STRIDE

```python
"""
Threat modeling using the STRIDE methodology.
STRIDE: Spoofing, Tampering, Repudiation, Information Disclosure,
        Denial of Service, Elevation of Privilege
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional


class ThreatCategory(Enum):
    SPOOFING = "Spoofing"
    TAMPERING = "Tampering"
    REPUDIATION = "Repudiation"
    INFORMATION_DISCLOSURE = "Information Disclosure"
    DENIAL_OF_SERVICE = "Denial of Service"
    ELEVATION_OF_PRIVILEGE = "Elevation of Privilege"


class Severity(Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


@dataclass
class Threat:
    id: str
    category: ThreatCategory
    title: str
    description: str
    affected_component: str
    severity: Severity
    likelihood: int  # 1-5
    impact: int      # 1-5
    mitigations: List[str] = field(default_factory=list)

    @property
    def risk_score(self) -> int:
        """Calculate risk score (likelihood * impact)."""
        return self.likelihood * self.impact


@dataclass
class DataFlow:
    source: str
    destination: str
    protocol: str
    data_types: List[str]
    authentication: Optional[str] = None
    encryption: Optional[str] = None


class ThreatModel:
    """Complete threat model for a system."""

    def __init__(self, system_name: str, version: str):
        self.system_name = system_name
        self.version = version
        self.data_flows: List[DataFlow] = []
        self.threats: List[Threat] = []
        self.assumptions: List[str] = []

    def add_data_flow(self, flow: DataFlow):
        self.data_flows.append(flow)

    def add_threat(self, threat: Threat):
        self.threats.append(threat)

    def add_assumption(self, assumption: str):
        self.assumptions.append(assumption)

    def analyze_flows(self):
        """Analyze data flows for potential threats."""
        for flow in self.data_flows:
            # Check authentication
            if not flow.authentication:
                self.add_threat(Threat(
                    id=f"T-{len(self.threats) + 1}",
                    category=ThreatCategory.SPOOFING,
                    title=f"Unauthenticated flow: {flow.source} -> {flow.destination}",
                    description=f"The data flow from {flow.source} to {flow.destination} "
                                f"lacks authentication",
                    affected_component=f"{flow.source}-{flow.destination}",
                    severity=Severity.HIGH,
                    likelihood=4,
                    impact=4,
                    mitigations=["Add authentication (TLS mutual auth, API key, JWT)"],
                ))

            # Check encryption
            if flow.encryption and flow.encryption.lower() == 'none':
                sensitive_data = [d for d in flow.data_types
                                  if d in ['password', 'credit_card', 'ssn', 'token']]
                if sensitive_data:
                    self.add_threat(Threat(
                        id=f"T-{len(self.threats) + 1}",
                        category=ThreatCategory.INFORMATION_DISCLOSURE,
                        title=f"Unencrypted sensitive data: {flow.source} -> {flow.destination}",
                        description=f"Sensitive data ({', '.join(sensitive_data)}) "
                                    f"transmitted without encryption",
                        affected_component=f"{flow.source}-{flow.destination}",
                        severity=Severity.CRITICAL,
                        likelihood=5,
                        impact=5,
                        mitigations=["Implement TLS 1.3 encryption"],
                    ))

    def generate_report(self) -> str:
        """Generate threat modeling report."""
        risk_scores = [t.risk_score for t in self.threats]
        average_risk = sum(risk_scores) / len(risk_scores) if risk_scores else 0

        report = [
            f"Threat Model: {self.system_name} v{self.version}",
            "=" * 60,
            "",
            f"Total Threats Identified: {len(self.threats)}",
            f"Average Risk Score: {average_risk:.1f}",
            "",
            "Risk Distribution:",
        ]

        for severity in Severity:
            count = sum(1 for t in self.threats if t.severity == severity)
            report.append(f"  {severity.value}: {count}")

        report.extend([
            "",
            "Threat Details:",
            "-" * 60,
        ])

        # Sort by risk score descending
        sorted_threats = sorted(self.threats,
                                key=lambda t: t.risk_score,
                                reverse=True)

        for threat in sorted_threats:
            report.extend([
                f"\n[{threat.id}] {threat.title}",
                f"  Category: {threat.category.value}",
                f"  Severity: {threat.severity.value}",
                f"  Risk Score: {threat.risk_score} (L:{threat.likelihood} x I:{threat.impact})",
                f"  Component: {threat.affected_component}",
                f"  Description: {threat.description}",
                "  Mitigations:",
            ])
            for mitigation in threat.mitigations:
                report.append(f"    - {mitigation}")

        report.extend([
            "",
            "Assumptions:",
            "-" * 60,
        ])
        for assumption in self.assumptions:
            report.append(f"  - {assumption}")

        return "\n".join(report)


# Example usage
model = ThreatModel("E-Commerce Platform", "2.0.0")

# Add data flows
model.add_data_flow(DataFlow(
    source="User Browser",
    destination="Web Application",
    protocol="HTTPS",
    data_types=["credentials", "personal_info", "payment"],
    authentication="Session cookie",
    encryption="TLS 1.3",
))

model.add_data_flow(DataFlow(
    source="Web Application",
    destination="Payment Gateway",
    protocol="HTTPS",
    data_types=["credit_card", "amount"],
    authentication="API key",
    encryption="TLS 1.3",
))

model.add_data_flow(DataFlow(
    source="Web Application",
    destination="Database",
    protocol="PostgreSQL",
    data_types=["orders", "users", "products"],
    authentication="Password",
    encryption="TLS 1.2",
))

model.add_data_flow(DataFlow(
    source="Internal Admin",
    destination="Admin Panel",
    protocol="HTTPS",
    data_types=["all_data", "logs"],
    authentication="SSO + MFA",
    encryption="TLS 1.3",
))

# Add assumptions
model.add_assumption("All hosts have host-based firewalls enabled")
model.add_assumption("Database is in private subnet without direct internet access")
model.add_assumption("Employees use company-managed devices with endpoint protection")

# Analyze and generate report
model.analyze_flows()
print(model.generate_report())
```

### Example 2: Web Application Security Audit Checklist

```python
"""
Web application security audit checklist with evidence collection.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict
from enum import Enum
import json
from datetime import datetime


class FindingStatus(Enum):
    PASS = "Pass"
    FAIL = "Fail"
    NOT_APPLICABLE = "N/A"
    NOT_TESTED = "Not Tested"


@dataclass
class Finding:
    id: str
    category: str
    check: str
    status: FindingStatus
    evidence: Optional[str] = None
    severity: Optional[str] = None
    recommendation: Optional[str] = None


class SecurityAuditor:
    """Web application security auditor."""

    def __init__(self, app_name: str, app_version: str, url: str):
        self.app_name = app_name
        self.app_version = app_version
        self.url = url
        self.findings: List[Finding] = []
        self.audit_date = datetime.utcnow()

    def add_finding(self, finding: Finding):
        self.findings.append(finding)

    def check_http_headers(self, response_headers: Dict[str, str]):
        """Check security-related HTTP headers."""
        checks = {
            'Strict-Transport-Security': {
                'description': 'HTTP Strict Transport Security (HSTS)',
                'expected': 'max-age=31536000; includeSubDomains',
                'critical': True,
            },
            'Content-Security-Policy': {
                'description': 'Content Security Policy',
                'expected': 'script-src, object-src, etc.',
                'critical': True,
            },
            'X-Content-Type-Options': {
                'description': 'MIME type sniffing protection',
                'expected': 'nosniff',
                'critical': True,
            },
            'X-Frame-Options': {
                'description': 'Clickjacking protection',
                'expected': 'DENY or SAMEORIGIN',
                'critical': True,
            },
            'X-XSS-Protection': {
                'description': 'Cross-site scripting filter',
                'expected': '1; mode=block',
                'critical': False,
            },
            'Referrer-Policy': {
                'description': 'Referrer header policy',
                'expected': 'strict-origin-when-cross-origin',
                'critical': False,
            },
            'Permissions-Policy': {
                'description': 'Permissions policy',
                'expected': 'Defined permissions',
                'critical': False,
            },
        }

        for header, config in checks.items():
            if header in response_headers:
                status = FindingStatus.PASS
                evidence = f"{header}: {response_headers[header]}"
            else:
                status = FindingStatus.FAIL
                evidence = f"Missing header: {header}"

            self.add_finding(Finding(
                id=f"HDR-{header}",
                category="HTTP Headers",
                check=config['description'],
                status=status,
                evidence=evidence,
                severity="High" if config['critical'] else "Medium",
                recommendation=f"Add {header} header: {config['expected']}"
                    if status == FindingStatus.FAIL else None,
            ))

    def check_authentication(self):
        """Check authentication-related security controls."""
        auth_checks = [
            Finding(
                id="AUTH-1",
                category="Authentication",
                check="Password minimum length policy",
                status=FindingStatus.PASS,
                evidence="Minimum 12 characters enforced",
            ),
            Finding(
                id="AUTH-2",
                category="Authentication",
                check="Account lockout after failed attempts",
                status=FindingStatus.PASS,
                evidence="5 failed attempts triggers 15-minute lockout",
            ),
            Finding(
                id="AUTH-3",
                category="Authentication",
                check="Multi-factor authentication available",
                status=FindingStatus.FAIL,
                severity="High",
                evidence="MFA not implemented for admin accounts",
                recommendation="Implement TOTP or WebAuthn MFA for all admin accounts",
            ),
            Finding(
                id="AUTH-4",
                category="Authentication",
                check="Session timeout after inactivity",
                status=FindingStatus.PASS,
                evidence="30-minute idle timeout enforced",
            ),
            Finding(
                id="AUTH-5",
                category="Authentication",
                check="Password complexity requirements",
                status=FindingStatus.PASS,
                evidence="Enforces uppercase, lowercase, number, special character",
            ),
        ]

        for check in auth_checks:
            self.add_finding(check)

    def check_authorization(self):
        """Check authorization controls."""
        authz_checks = [
            Finding(
                id="AUTHZ-1",
                category="Authorization",
                check="Role-based access control (RBAC) implemented",
                status=FindingStatus.PASS,
                evidence="RBAC with admin, manager, user roles",
            ),
            Finding(
                id="AUTHZ-2",
                category="Authorization",
                check="API endpoints enforce authorization",
                status=FindingStatus.FAIL,
                severity="Critical",
                evidence="POST /api/admin/users endpoint returns data without admin role check",
                recommendation="Add authorization middleware to admin endpoints",
            ),
            Finding(
                id="AUTHZ-3",
                category="Authorization",
                check="Least privilege principle applied",
                status=FindingStatus.PASS,
                evidence="Default role has minimal permissions",
            ),
            Finding(
                id="AUTHZ-4",
                category="Authorization",
                check="Vertical access controls enforced",
                status=FindingStatus.NOT_TESTED,
                recommendation="Test all admin endpoints with non-admin session",
            ),
        ]

        for check in authz_checks:
            self.add_finding(check)

    def check_input_validation(self):
        """Check input validation and output encoding."""
        input_checks = [
            Finding(
                id="INP-1",
                category="Input Validation",
                check="SQL injection prevention (parameterized queries)",
                status=FindingStatus.PASS,
                evidence="All queries use parameterized statements or ORM",
            ),
            Finding(
                id="INP-2",
                category="Input Validation",
                check="Cross-site scripting (XSS) prevention",
                status=FindingStatus.FAIL,
                severity="High",
                evidence="User comment field reflects HTML without sanitization",
                recommendation="Implement context-aware output encoding",
            ),
            Finding(
                id="INP-3",
                category="Input Validation",
                check="Cross-site request forgery (CSRF) tokens",
                status=FindingStatus.PASS,
                evidence="CSRF tokens on all state-changing forms",
            ),
            Finding(
                id="INP-4",
                category="Input Validation",
                check="File upload validation",
                status=FindingStatus.PASS,
                evidence="File type, size, and content validation implemented",
            ),
            Finding(
                id="INP-5",
                category="Input Validation",
                check="Server-side input validation (not just client-side)",
                status=FindingStatus.FAIL,
                severity="High",
                evidence="Email format only validated on client side",
                recommendation="Add server-side validation for all inputs",
            ),
        ]

        for check in input_checks:
            self.add_finding(check)

    def generate_report(self) -> str:
        """Generate comprehensive audit report."""
        total = len(self.findings)
        passed = sum(1 for f in self.findings if f.status == FindingStatus.PASS)
        failed = sum(1 for f in self.findings if f.status == FindingStatus.FAIL)
        na = sum(1 for f in self.findings if f.status == FindingStatus.NOT_APPLICABLE)
        nt = sum(1 for f in self.findings if f.status == FindingStatus.NOT_TESTED)

        critical = sum(1 for f in self.findings
                       if f.severity == "Critical" and f.status == FindingStatus.FAIL)
        high = sum(1 for f in self.findings
                   if f.severity == "High" and f.status == FindingStatus.FAIL)
        medium = sum(1 for f in self.findings
                     if f.severity == "Medium" and f.status == FindingStatus.FAIL)

        report = [
            f"Security Audit Report: {self.app_name} v{self.app_version}",
            f"Date: {self.audit_date.isoformat()}",
            f"Target: {self.url}",
            "=" * 60,
            "",
            "Executive Summary",
            "-" * 60,
            f"Total Checks: {total}",
            f"Passed: {passed}",
            f"Failed: {failed}",
            f"Not Applicable: {na}",
            f"Not Tested: {nt}",
            "",
            "Failed Findings by Severity:",
            f"  Critical: {critical}",
            f"  High: {high}",
            f"  Medium: {medium}",
            "",
            f"Pass Rate: {(passed / (total - na) * 100):.1f}%",
            "",
        ]

        # Group findings by category
        categories = {}
        for finding in self.findings:
            categories.setdefault(finding.category, []).append(finding)

        for category, cat_findings in categories.items():
            report.extend([
                f"\n{category}",
                "-" * 40,
            ])

            for finding in cat_findings:
                status_symbol = {
                    FindingStatus.PASS: "✓",
                    FindingStatus.FAIL: "✗",
                    FindingStatus.NOT_APPLICABLE: "-",
                    FindingStatus.NOT_TESTED: "?",
                }[finding.status]

                report.append(f"\n  {status_symbol} [{finding.id}] {finding.check}")
                report.append(f"    Status: {finding.status.value}")

                if finding.severity:
                    report.append(f"    Severity: {finding.severity}")

                if finding.evidence:
                    report.append(f"    Evidence: {finding.evidence}")

                if finding.recommendation:
                    report.append(f"    Recommendation: {finding.recommendation}")

        return "\n".join(report)


# Example usage
auditor = SecurityAuditor(
    "E-Commerce Platform",
    "2.0.0",
    "https://app.example.com"
)

# Simulate response headers
response_headers = {
    'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
    'X-Content-Type-Options': 'nosniff',
    'X-Frame-Options': 'DENY',
    'Referrer-Policy': 'strict-origin-when-cross-origin',
}

auditor.check_http_headers(response_headers)
auditor.check_authentication()
auditor.check_authorization()
auditor.check_input_validation()

print(auditor.generate_report())
```

### Example 3: Dependency Vulnerability Scanning

```python
"""
Dependency vulnerability scanning and analysis.
"""

import json
import subprocess
from dataclasses import dataclass, field
from typing import List, Dict, Optional
from datetime import datetime


@dataclass
class Vulnerability:
    id: str                  # CVE or GHSA identifier
    package: str
    severity: str            # CRITICAL, HIGH, MEDIUM, LOW
    title: str
    description: str
    fixed_in: Optional[str]
    cvss_score: Optional[float]
    affected_versions: str
    exploitability: str      # "proof_of_concept", "functional", "none"


@dataclass
class ScanResult:
    scanner: str
    scan_date: datetime
    total_vulnerabilities: int
    critical: int = 0
    high: int = 0
    medium: int = 0
    low: int = 0
    vulnerabilities: List[Vulnerability] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)


class DependencyScanner:
    """Scan project dependencies for known vulnerabilities."""

    def __init__(self, project_path: str):
        self.project_path = project_path

    def scan_npm(self) -> ScanResult:
        """Scan npm dependencies using npm audit."""
        try:
            result = subprocess.run(
                ['npm', 'audit', '--json'],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode > 1:  # 0 = no vulns, 1 = vulns found
                return ScanResult(
                    scanner='npm audit',
                    scan_date=datetime.utcnow(),
                    total_vulnerabilities=0,
                    errors=[result.stderr],
                )

            audit_data = json.loads(result.stdout)
            vulnerabilities = []
            critical = high = medium = low = 0

            for advisory_id, advisory in audit_data.get('advisories', {}).items():
                severity = advisory.get('severity', 'unknown').upper()
                if severity == 'CRITICAL':
                    critical += 1
                elif severity == 'HIGH':
                    high += 1
                elif severity == 'MODERATE':
                    medium += 1
                elif severity == 'LOW':
                    low += 1

                vulnerabilities.append(Vulnerability(
                    id=advisory_id,
                    package=advisory['module_name'],
                    severity=severity,
                    title=advisory['title'],
                    description=advisory['overview'],
                    fixed_in=advisory.get('patched_versions'),
                    cvss_score=advisory.get('cvss', {}).get('score'),
                    affected_versions=advisory['vulnerable_versions'],
                    exploitability=advisory.get('exploitability', 'none'),
                ))

            return ScanResult(
                scanner='npm audit',
                scan_date=datetime.utcnow(),
                total_vulnerabilities=len(vulnerabilities),
                critical=critical,
                high=high,
                medium=medium,
                low=low,
                vulnerabilities=vulnerabilities,
            )

        except subprocess.TimeoutExpired:
            return ScanResult(
                scanner='npm audit',
                scan_date=datetime.utcnow(),
                total_vulnerabilities=0,
                errors=['Scan timed out'],
            )

    def scan_python(self) -> ScanResult:
        """Scan Python dependencies using pip-audit or safety."""
        try:
            result = subprocess.run(
                ['pip', 'list', '--format=json'],
                cwd=self.project_path,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode != 0:
                return ScanResult(
                    scanner='pip audit',
                    scan_date=datetime.utcnow(),
                    total_vulnerabilities=0,
                    errors=[result.stderr],
                )

            packages = json.loads(result.stdout)
            # Use safety or pyannote for actual vulnerability checking
            # This is a simplified version

            return ScanResult(
                scanner='pip audit',
                scan_date=datetime.utcnow(),
                total_vulnerabilities=0,
            )

        except Exception as e:
            return ScanResult(
                scanner='pip audit',
                scan_date=datetime.utcnow(),
                total_vulnerabilities=0,
                errors=[str(e)],
            )

    def generate_scan_report(self, results: List[ScanResult]) -> str:
        """Generate a dependency vulnerability report."""
        report = [
            "Dependency Vulnerability Scan Report",
            f"Date: {datetime.utcnow().isoformat()}",
            f"Project: {self.project_path}",
            "=" * 60,
        ]

        for result in results:
            report.extend([
                f"\nScanner: {result.scanner}",
                f"Scan Date: {result.scan_date.isoformat()}",
                f"Total Vulnerabilities: {result.total_vulnerabilities}",
                f"  Critical: {result.critical}",
                f"  High: {result.high}",
                f"  Medium: {result.medium}",
                f"  Low: {result.low}",
            ])

            if result.errors:
                report.extend([
                    "",
                    "Errors:",
                ])
                for error in result.errors:
                    report.append(f"  - {error}")

            if result.vulnerabilities:
                report.extend([
                    "",
                    "Vulnerability Details (sorted by severity):",
                    "-" * 40,
                ])

                # Sort by severity
                severity_order = {'CRITICAL': 0, 'HIGH': 1, 'MEDIUM': 2, 'LOW': 3}
                sorted_vulns = sorted(
                    result.vulnerabilities,
                    key=lambda v: severity_order.get(v.severity, 99)
                )

                for vuln in sorted_vulns:
                    report.extend([
                        f"\n[{vuln.severity}] {vuln.id}",
                        f"  Package: {vuln.package}",
                        f"  Title: {vuln.title}",
                        f"  Description: {vuln.description[:200]}...",
                        f"  Affected: {vuln.affected_versions}",
                        f"  Fixed in: {vuln.fixed_in or 'No fix available'}",
                        f"  CVSS: {vuln.cvss_score or 'N/A'}",
                        f"  Exploitability: {vuln.exploitability}",
                    ])

        return "\n".join(report)

    def generate_fix_recommendations(self, results: List[ScanResult]) -> str:
        """Generate fix recommendations for vulnerabilities."""
        recommendations = [
            "Remediation Plan",
            "=" * 60,
        ]

        for result in results:
            critical_high = [v for v in result.vulnerabilities
                             if v.severity in ('CRITICAL', 'HIGH')]

            if critical_high:
                recommendations.extend([
                    f"\nImmediate Actions ({result.scanner}):",
                ])

                for vuln in critical_high:
                    if vuln.fixed_in:
                        recommendations.append(
                            f"  1. Update {vuln.package} to {vuln.fixed_in}"
                        )
                    else:
                        recommendations.append(
                            f"  1. {vuln.package}: No fix available - "
                            f"assess impact and consider removing dependency"
                        )

        recommendations.extend([
            "",
            "General Recommendations:",
            "  1. Run dependency scanning in CI/CD pipeline",
            "  2. Enable Dependabot or Renovate for automatic updates",
            "  3. Review and update dependencies regularly (monthly)",
            "  4. Remove unused dependencies",
            "  5. Pin dependency versions in production",
            "  6. Use lockfiles (package-lock.json, yarn.lock, etc.)",
            "  7. Monitor security advisories for critical dependencies",
        ])

        return "\n".join(recommendations)
```

### Example 4: API Security Testing

```python
"""
Automated API security testing.
"""

import requests
from dataclasses import dataclass, field
from typing import List, Dict, Optional
import json


@dataclass
class SecurityTestResult:
    test_name: str
    endpoint: str
    method: str
    status: str  # "pass" or "fail"
    details: str
    severity: str = "Medium"


class APISecurityTester:
    """Test API endpoints for common security vulnerabilities."""

    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.session = requests.Session()
        if api_key:
            self.session.headers.update({'Authorization': f'Bearer {api_key}'})
        self.results: List[SecurityTestResult] = []

    def test_sql_injection(self, endpoint: str, method: str = "GET",
                           param: str = "id", payloads: List[str] = None):
        """Test for SQL injection vulnerabilities."""
        if payloads is None:
            payloads = [
                "' OR '1'='1",
                "' UNION SELECT * FROM users--",
                "' OR 1=1--",
                "'; DROP TABLE users--",
                "' OR '1'='1' /*",
                "1' AND 1=1--",
                "1' AND 1=2--",
            ]

        for payload in payloads:
            try:
                if method.upper() == "GET":
                    response = self.session.get(
                        f"{self.base_url}{endpoint}",
                        params={param: payload},
                        timeout=5,
                    )
                else:
                    response = self.session.post(
                        f"{self.base_url}{endpoint}",
                        json={param: payload},
                        timeout=5,
                    )

                # Check for SQL error messages in response
                sql_errors = [
                    "sql syntax", "mysql_fetch", "ORA-", "PostgreSQL",
                    "SQLite", "unclosed quotation", "Microsoft OLE DB",
                ]

                response_text = response.text.lower()
                found_errors = [e for e in sql_errors if e.lower() in response_text]

                if found_errors:
                    self.results.append(SecurityTestResult(
                        test_name="SQL Injection",
                        endpoint=endpoint,
                        method=method,
                        status="fail",
                        details=f"SQL error detected with payload: {payload}. "
                                f"Errors: {found_errors}",
                        severity="Critical",
                    ))
                    return

            except requests.exceptions.RequestException as e:
                self.results.append(SecurityTestResult(
                    test_name="SQL Injection",
                    endpoint=endpoint,
                    method=method,
                    status="pass",
                    details=f"Request failed (may be blocked): {e}",
                ))

        self.results.append(SecurityTestResult(
            test_name="SQL Injection",
            endpoint=endpoint,
            method=method,
            status="pass",
            details="No SQL injection vulnerabilities detected",
        ))

    def test_xss(self, endpoint: str, param: str = "q"):
        """Test for cross-site scripting vulnerabilities."""
        xss_payloads = [
            "<script>alert('XSS')</script>",
            "<img src=x onerror=alert(1)>",
            "<svg onload=alert(1)>",
            "javascript:alert('XSS')",
            "\"><script>alert(1)</script>",
            "'; alert(1); '",
        ]

        for payload in xss_payloads:
            try:
                response = self.session.get(
                    f"{self.base_url}{endpoint}",
                    params={param: payload},
                    timeout=5,
                )

                if payload in response.text:
                    self.results.append(SecurityTestResult(
                        test_name="Cross-Site Scripting (XSS)",
                        endpoint=endpoint,
                        method="GET",
                        status="fail",
                        details=f"XSS payload reflected in response: {payload}",
                        severity="High",
                    ))
                    return

            except requests.exceptions.RequestException:
                pass

        self.results.append(SecurityTestResult(
            test_name="Cross-Site Scripting (XSS)",
            endpoint=endpoint,
            method="GET",
            status="pass",
            details="No reflected XSS vulnerabilities detected",
        ))

    def test_idor(self, endpoints: List[str], authenticated_session=None):
        """Test for Insecure Direct Object References."""
        if authenticated_session:
            session = authenticated_session
        else:
            session = self.session

        for endpoint in endpoints:
            # Try accessing another user's resource
            test_ids = ["1", "2", "99999", "admin", "../etc/passwd"]

            for test_id in test_ids:
                try:
                    url = f"{self.base_url}{endpoint}/{test_id}"
                    response = session.get(url, timeout=5)

                    if response.status_code == 200 and test_id != "99999":
                        # Need to verify if the response contains data we shouldn't have access to
                        self.results.append(SecurityTestResult(
                            test_name="Insecure Direct Object Reference (IDOR)",
                            endpoint=endpoint,
                            method="GET",
                            status="fail",
                            details=f"Accessed resource with ID {test_id}",
                            severity="High",
                        ))
                        return

                except requests.exceptions.RequestException:
                    pass

        self.results.append(SecurityTestResult(
            test_name="Insecure Direct Object Reference (IDOR)",
            endpoint=str(endpoints),
            method="GET",
            status="pass",
            details="No IDOR vulnerabilities detected",
        ))

    def test_rate_limiting(self, endpoint: str, method: str = "POST",
                          requests_count: int = 100):
        """Test for rate limiting."""
        responses = []

        for i in range(requests_count):
            try:
                if method.upper() == "GET":
                    response = self.session.get(
                        f"{self.base_url}{endpoint}",
                        timeout=5,
                    )
                else:
                    response = self.session.post(
                        f"{self.base_url}{endpoint}",
                        json={"test": f"request_{i}"},
                        timeout=5,
                    )
                responses.append(response.status_code)

            except requests.exceptions.RequestException:
                responses.append(0)

        # Check if any requests were rate-limited
        rate_limited = [r for r in responses if r in (429, 503)]

        if rate_limited:
            self.results.append(SecurityTestResult(
                test_name="Rate Limiting",
                endpoint=endpoint,
                method=method,
                status="pass",
                details=f"Rate limiting detected after {len(responses) - len(rate_limited)} requests",
            ))
        else:
            self.results.append(SecurityTestResult(
                test_name="Rate Limiting",
                endpoint=endpoint,
                method=method,
                status="fail",
                details=f"No rate limiting detected after {requests_count} requests",
                severity="Medium",
            ))

    def generate_report(self) -> str:
        """Generate API security test report."""
        report = [
            "API Security Test Report",
            "=" * 60,
            f"Target: {self.base_url}",
            f"Tests Conducted: {len(self.results)}",
            "",
        ]

        passed = [r for r in self.results if r.status == "pass"]
        failed = [r for r in self.results if r.status == "fail"]

        report.extend([
            f"Passed: {len(passed)}",
            f"Failed: {len(failed)}",
            "",
        ])

        if failed:
            report.extend([
                "Failed Tests:",
                "-" * 40,
            ])
            for result in failed:
                report.extend([
                    f"\n  [{result.severity}] {result.test_name}",
                    f"  Endpoint: {result.method} {result.endpoint}",
                    f"  Details: {result.details}",
                ])

        return "\n".join(report)
```

### Example 5: Secrets Detection

```python
"""
Detect exposed secrets in source code.
"""

import re
import os
from dataclasses import dataclass, field
from typing import List, Optional, Set


@dataclass
class SecretFinding:
    file_path: str
    line_number: int
    secret_type: str
    snippet: str
    severity: str  # Critical, High, Medium
    recommendation: str


class SecretsDetector:
    """Detect hardcoded secrets, API keys, and credentials."""

    # Patterns for common secret types
    PATTERNS = {
        'AWS Access Key ID': {
            'pattern': r'(?<![A-Z0-9])[A-Z0-9]{20}(?![A-Z0-9])',
            'severity': 'Critical',
            'context_required': True,
            'context_patterns': [r'aws', r'akid', r'access.?key'],
        },
        'AWS Secret Access Key': {
            'pattern': r'(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])',
            'severity': 'Critical',
            'context_required': True,
            'context_patterns': [r'aws', r'secret', r'sak'],
        },
        'GitHub Token': {
            'pattern': r'(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9_]{36,}',
            'severity': 'Critical',
            'context_required': False,
        },
        'GitLab Token': {
            'pattern': r'glpat-[A-Za-z0-9\-_]{20,}',
            'severity': 'Critical',
            'context_required': False,
        },
        'Slack Token': {
            'pattern': r'xox[abprs]-[A-Za-z0-9\-]{10,}',
            'severity': 'Critical',
            'context_required': False,
        },
        'JWT Token': {
            'pattern': r'eyJ[A-Za-z0-9\-_=]+\.eyJ[A-Za-z0-9\-_=]+\.[A-Za-z0-9\-_=]+',
            'severity': 'High',
            'context_required': True,
            'context_patterns': [r'jwt', r'token', r'bearer'],
        },
        'Private Key': {
            'pattern': r'-----BEGIN\s?(RSA|DSA|EC|OPENSSH|PRIVATE)\s?KEY-----',
            'severity': 'Critical',
            'context_required': False,
        },
        'Password Field': {
            'pattern': r'(?:password|passwd|pwd)\s*[:=]\s*["\'][^"\']+["\']',
            'severity': 'High',
            'context_required': False,
        },
        'API Key Generic': {
            'pattern': r'(?:api[_-]?key|apikey|api[_-]?secret)\s*[:=]\s*["\'][^"\']+["\']',
            'severity': 'High',
            'context_required': False,
        },
        'Connection String': {
            'pattern': r'(?:mongodb|postgres|mysql|redis)://[^@]+@',
            'severity': 'Critical',
            'context_required': False,
        },
        'Google API Key': {
            'pattern': r'AIza[A-Za-z0-9\-_]{35}',
            'severity': 'Critical',
            'context_required': False,
        },
        'Heroku API Key': {
            'pattern': r'[hH][eE][rR][oO][kK][uU]\s*[:=]\s*[A-Za-z0-9\-_]{36,}',
            'severity': 'High',
            'context_required': False,
        },
    }

    # Files to exclude
    EXCLUDE_PATTERNS = [
        r'\.git/',
        r'node_modules/',
        r'vendor/',
        r'\.venv/',
        r'__pycache__/',
        r'\.next/',
        r'dist/',
        r'build/',
        r'\.tox/',
        r'\.eggs/',
        r'\.mypy_cache/',
        r'\.pytest_cache/',
    ]

    def __init__(self, repo_path: str):
        self.repo_path = repo_path
        self.findings: List[SecretFinding] = []

    def scan_file(self, file_path: str):
        """Scan a single file for secrets."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()

            for line_num, line in enumerate(lines, 1):
                for secret_type, config in self.PATTERNS.items():
                    matches = re.finditer(config['pattern'], line)

                    for match in matches:
                        value = match.group()

                        # Check context requirement
                        if config.get('context_required'):
                            context_patterns = config.get('context_patterns', [])
                            has_context = any(
                                re.search(cp, line, re.IGNORECASE)
                                for cp in context_patterns
                            )
                            if not has_context:
                                continue

                        # Skip obvious test/example values
                        if self._is_false_positive(value, line):
                            continue

                        self.findings.append(SecretFinding(
                            file_path=file_path,
                            line_number=line_num,
                            secret_type=secret_type,
                            snippet=line.strip()[:100],
                            severity=config['severity'],
                            recommendation=self._get_recommendation(secret_type),
                        ))

        except Exception:
            pass

    def _is_false_positive(self, value: str, line: str) -> bool:
        """Check if a match is likely a false positive."""
        false_patterns = [
            r'example\.',
            r'your-',
            r'xxxx',
            r'test',
            r'placeholder',
            r'changeme',
            r'1234567890',
            r'deadbeef',
        ]

        line_lower = line.lower()

        # Skip if line contains false positive indicators
        for pattern in false_patterns:
            if re.search(pattern, line_lower):
                return True

        # Skip generated/lock files
        if any(p in line_lower for p in ['package-lock.json', 'yarn.lock', 'composer.lock']):
            return True

        return False

    def _get_recommendation(self, secret_type: str) -> str:
        """Get remediation recommendation for a secret type."""
        recommendations = {
            'AWS Access Key ID': 'Rotate the AWS access key and use IAM roles instead of hardcoded keys',
            'AWS Secret Access Key': 'Rotate the AWS secret key and use IAM roles or AWS Secrets Manager',
            'GitHub Token': 'Revoke the token and use GitHub Actions secrets or environment variables',
            'GitLab Token': 'Revoke the token and use CI/CD variables instead',
            'Slack Token': 'Revoke the token and use environment variables',
            'JWT Token': 'Rotate the signing key and use environment variables',
            'Private Key': 'Revoke and reissue the certificate; use a secrets manager',
            'Password Field': 'Remove hardcoded password; use environment variables or vault',
            'API Key Generic': 'Rotate the API key and use environment variables or secrets manager',
            'Connection String': 'Use environment variables with credentials from secrets manager',
        }
        return recommendations.get(secret_type, 'Remove the secret and use environment variables')

    def scan_repository(self) -> List[SecretFinding]:
        """Scan the entire repository for secrets."""
        for root, dirs, files in os.walk(self.repo_path):
            # Skip excluded directories
            dirs[:] = [d for d in dirs
                       if not any(re.search(p, d) for p in self.EXCLUDE_PATTERNS)]

            for file in files:
                file_path = os.path.join(root, file)

                # Skip binary and large files
                try:
                    if os.path.getsize(file_path) > 1024 * 1024:  # 1MB
                        continue
                except OSError:
                    continue

                self.scan_file(file_path)

        return self.findings

    def generate_report(self) -> str:
        """Generate secrets scan report."""
        report = [
            "Secrets Detection Report",
            "=" * 60,
            f"Repository: {self.repo_path}",
            f"Secrets Found: {len(self.findings)}",
            "",
        ]

        if not self.findings:
            report.append("No secrets detected.")
            return "\n".join(report)

        # Group by severity
        for severity in ['Critical', 'High', 'Medium']:
            severity_findings = [f for f in self.findings if f.severity == severity]
            if severity_findings:
                report.extend([
                    f"\n{severity} Severity Findings:",
                    "-" * 40,
                ])
                for finding in severity_findings:
                    report.extend([
                        f"\n  Type: {finding.secret_type}",
                        f"  File: {finding.file_path}:{finding.line_number}",
                        f"  Snippet: {finding.snippet}",
                        f"  Recommendation: {finding.recommendation}",
                    ])

        return "\n".join(report)
```

### Example 6: Compliance Checklist (PCI DSS)

```python
"""
PCI DSS compliance checklist.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class ComplianceStatus(Enum):
    COMPLIANT = "Compliant"
    NON_COMPLIANT = "Non-Compliant"
    NOT_APPLICABLE = "N/A"
    NOT_ASSESSED = "Not Assessed"


@dataclass
class Requirement:
    id: str
    description: str
    status: ComplianceStatus
    evidence: Optional[str] = None
    notes: Optional[str] = None


class PCIDSSAuditor:
    """Auditor for PCI DSS compliance."""

    def __init__(self, organization: str, scope: str):
        self.organization = organization
        self.scope = scope
        self.requirements: List[Requirement] = []

    def add_requirements(self):
        """Add PCI DSS v4.0 requirements."""
        pci_requirements = [
            # Requirement 1: Install and maintain network security controls
            Requirement("1.1", "Firewall configuration standards documented", ComplianceStatus.COMPLIANT),
            Requirement("1.2", "Network diagram current and approved", ComplianceStatus.COMPLIANT),
            Requirement("1.3", "Firewall rules restrict inbound/outbound traffic", ComplianceStatus.COMPLIANT),
            Requirement("1.4", "Personal firewall on portable devices", ComplianceStatus.NOT_APPLICABLE),
            Requirement("1.5", "Security controls on all network devices", ComplianceStatus.COMPLIANT),

            # Requirement 2: Apply secure configurations
            Requirement("2.1", "Configuration standards for all system components", ComplianceStatus.COMPLIANT),
            Requirement("2.2", "Change default passwords and settings", ComplianceStatus.COMPLIANT),
            Requirement("2.3", "Unnecessary services and protocols disabled", ComplianceStatus.NON_COMPLIANT,
                        evidence="Telnet service still enabled on legacy server",
                        notes="Schedule decommission of legacy server Q3"),
            Requirement("2.4", "System configuration reviewed periodically", ComplianceStatus.COMPLIANT),

            # Requirement 3: Protect stored cardholder data
            Requirement("3.1", "Data retention and disposal policy documented", ComplianceStatus.COMPLIANT),
            Requirement("3.2", "Full track data, CVV, and PIN not stored after authorization", ComplianceStatus.COMPLIANT),
            Requirement("3.3", "Sensitive data rendered unreadable (encryption, masking, etc.)", ComplianceStatus.COMPLIANT),
            Requirement("3.4", "PAN masked when displayed", ComplianceStatus.COMPLIANT,
                        evidence="All dashboards show only last 4 digits"),
            Requirement("3.5", "Encryption keys properly managed", ComplianceStatus.NON_COMPLIANT,
                        evidence="Key rotation policy exists but not documented in writing",
                        notes="Document the key rotation procedure"),

            # Requirement 4: Encrypt transmission of cardholder data
            Requirement("4.1", "Strong cryptography for data in transit", ComplianceStatus.COMPLIANT),
            Requirement("4.2", "TLS implementation follows best practices", ComplianceStatus.COMPLIANT),

            # Requirement 5: Protect all systems from malware
            Requirement("5.1", "Anti-malware deployed on all systems", ComplianceStatus.COMPLIANT),
            Requirement("5.2", "Anti-malware definitions kept current", ComplianceStatus.COMPLIANT),
            Requirement("5.3", "Anti-malware logs reviewed per policy", ComplianceStatus.COMPLIANT),

            # Requirement 6: Develop and maintain secure systems
            Requirement("6.1", "Vulnerability management process documented", ComplianceStatus.COMPLIANT),
            Requirement("6.2", "Critical security patches applied within 30 days", ComplianceStatus.NON_COMPLIANT,
                        evidence="Two critical patches older than 30 days",
                        notes="Expedite patch application for CVE-2024-XXXX"),
            Requirement("6.3", "Secure coding practices documented", ComplianceStatus.COMPLIANT),
            Requirement("6.4", "Code review process for security", ComplianceStatus.COMPLIANT),
            Requirement("6.5", "Security testing performed annually", ComplianceStatus.COMPLIANT),

            # Requirement 7: Restrict access to cardholder data
            Requirement("7.1", "Access control policy documented", ComplianceStatus.COMPLIANT),
            Requirement("7.2", "Access granted on need-to-know basis", ComplianceStatus.COMPLIANT),
            Requirement("7.3", "Access reviews every 6 months", ComplianceStatus.COMPLIANT),

            # Requirement 8: Identify and authenticate access
            Requirement("8.1", "Unique IDs for all users", ComplianceStatus.COMPLIANT),
            Requirement("8.2", "Strong password policy implemented", ComplianceStatus.COMPLIANT),
            Requirement("8.3", "MFA for remote access to CDE", ComplianceStatus.COMPLIANT),
            Requirement("8.4", "MFA for all non-console admin access", ComplianceStatus.COMPLIANT),

            # Requirement 9: Restrict physical access
            Requirement("9.1", "Physical access controls for facilities", ComplianceStatus.COMPLIANT),
            Requirement("9.2", "Visitors logged and escorted", ComplianceStatus.COMPLIANT),

            # Requirement 10: Log and monitor all access
            Requirement("10.1", "Audit trails enabled for all system components", ComplianceStatus.COMPLIANT),
            Requirement("10.2", "Audit logs include user ID, event type, date/time", ComplianceStatus.COMPLIANT),
            Requirement("10.3", "Logs retained for at least 12 months", ComplianceStatus.COMPLIANT),
            Requirement("10.4", "Log review process documented", ComplianceStatus.COMPLIANT),

            # Requirement 11: Test security regularly
            Requirement("11.1", "ASV scanning performed quarterly", ComplianceStatus.COMPLIANT),
            Requirement("11.2", "Internal vulnerability scans quarterly", ComplianceStatus.COMPLIANT),
            Requirement("11.3", "Penetration testing annually", ComplianceStatus.COMPLIANT),
            Requirement("11.4", "IDS/IPS deployed and monitored", ComplianceStatus.COMPLIANT),

            # Requirement 12: Information security policy
            Requirement("12.1", "Information security policy documented", ComplianceStatus.COMPLIANT),
            Requirement("12.2", "Risk assessment performed annually", ComplianceStatus.COMPLIANT),
            Requirement("12.3", "Security awareness training provided", ComplianceStatus.COMPLIANT),
            Requirement("12.4", "Incident response plan documented", ComplianceStatus.COMPLIANT),
        ]

        self.requirements = pci_requirements

    def calculate_compliance_rate(self) -> float:
        """Calculate compliance percentage."""
        assessed = [r for r in self.requirements
                    if r.status in (ComplianceStatus.COMPLIANT, ComplianceStatus.NON_COMPLIANT)]
        if not assessed:
            return 0.0
        compliant = sum(1 for r in assessed if r.status == ComplianceStatus.COMPLIANT)
        return (compliant / len(assessed)) * 100

    def generate_report(self) -> str:
        """Generate PCI DSS compliance report."""
        rate = self.calculate_compliance_rate()
        non_compliant = [r for r in self.requirements
                         if r.status == ComplianceStatus.NON_COMPLIANT]

        report = [
            "PCI DSS Compliance Report",
            "=" * 60,
            f"Organization: {self.organization}",
            f"Scope: {self.scope}",
            f"Date: {datetime.utcnow().isoformat()}",
            "",
            f"Overall Compliance Rate: {rate:.1f}%",
            f"Total Requirements: {len(self.requirements)}",
            f"Non-Compliant: {len(non_compliant)}",
            "",
        ]

        if non_compliant:
            report.extend([
                "Non-Compliant Findings:",
                "-" * 40,
            ])
            for req in non_compliant:
                report.extend([
                    f"\n  [{req.id}] {req.description}",
                    f"  Evidence: {req.evidence or 'None provided'}",
                    f"  Notes: {req.notes or 'No notes'}",
                ])

        report.extend([
            "",
            "Remediation Priorities:",
            "-" * 40,
        ])

        for i, req in enumerate(non_compliant[:5], 1):
            report.append(f"  {i}. {req.id}: {req.description}")

        return "\n".join(report)
```

## Best Practices

### Audit Methodology

- Define clear scope and rules of engagement before starting
- Get written authorization before any testing
- Use a combination of automated tools and manual testing
- Document all findings with evidence and reproduction steps
- Prioritize findings by risk (severity × likelihood)
- Validate fixes after remediation

### Secure Development

- Implement security in the design phase (shift left)
- Use SAST tools in CI/CD pipelines
- Conduct regular dependency vulnerability scanning
- Perform threat modeling for new features
- Train developers on secure coding practices
- Maintain a security champions program

### Compliance

- Understand which regulations apply to your system
- Map controls to compliance requirements
- Maintain evidence of compliance continuously
- Automate compliance checks where possible
- Conduct internal audits before external audits
- Document remediation plans for gaps

## Common Mistakes

- **Only using automated scanners**: Automated tools miss business logic flaws and complex attack chains. Manual testing is essential.
- **Testing in production without authorization**: Unauthorized testing can disrupt services and violate laws. Always get written permission.
- **Not fixing root causes**: Patching individual vulnerabilities without addressing the systemic issue leads to recurring problems.
- **Ignoring the human factor**: Social engineering and insider threats are often overlooked in technical audits.
- **No threat modeling**: Without understanding how an attacker thinks, you are defending blindly.
- **Stale compliance certificates**: Compliance is not a one-time achievement. Continuous monitoring is required.
- **Over-relying on WAF**: Web Application Firewalls are bypassable and should not be the only defense layer.

## Libraries

### Security Tools

| Tool | Purpose |
|------|---------|
| OWASP ZAP | Web application security scanner |
| Burp Suite | Web security testing platform |
| Nmap | Network discovery and scanning |
| Metasploit | Penetration testing framework |
| Nuclei | Vulnerability scanner based on templates |
| Trivy | Vulnerability scanner for containers |
| Semgrep | Static analysis with custom rules |
| Bandit | Python security linter |
| Safety | Python dependency security checker |
| Gitleaks | Git repository secrets scanning |

### SAST Tools

| Tool | Languages | Purpose |
|------|-----------|---------|
| SonarQube | Multi-language | Code quality and security |
| ESLint security plugin | JavaScript | Security linting |
| Pyre/Pyright | Python | Type checking and security |
| Brakeman | Ruby | Rails security scanner |
| FindBugs/SpotBugs | Java | Bug and vulnerability detection |
| Semgrep | Multi-language | Custom security rules |

## Design Principles

### Defense in Depth

No single security control is sufficient. Multiple layers of defense ensure that if one layer is breached, subsequent layers still provide protection. Examples: WAF + input validation + parameterized queries + least privilege database accounts.

### Least Privilege

Every user, process, and system component should have only the permissions necessary to perform its function. No more, no less. This limits the blast radius of any compromise.

### Secure by Default

Systems should be secure in their default configuration. Security should not be optional or opt-in. Default-deny for access control, encryption enabled by default, and the most secure settings as defaults.

### Never Trust, Always Verify

Zero Trust architecture assumes that no actor, system, or network is inherently trustworthy. Verify every request, authenticate every access, encrypt every transmission, and validate every input.

## Coding Standards

### Security Documentation Structure

```
security/
  threat-models/           # Threat model documents
    payment-flow.md
    authentication-flow.md
  audit-reports/           # Audit findings
    penetration-test-q1-2024.md
    vulnerability-scan-2024-06.md
  policies/                # Security policies
    access-control.md
    incident-response.md
  compliance/              # Compliance evidence
    pci-dss-v4-evidence/
    soc2-evidence/
```

### Vulnerability Severity Classification

```yaml
Severity: CVSS Score Range
  Critical: 9.0 - 10.0
  High: 7.0 - 8.9
  Medium: 4.0 - 6.9
  Low: 0.1 - 3.9

Timeline for Remediation:
  Critical: 24-48 hours
  High: 72 hours - 7 days
  Medium: 30 days
  Low: 90 days
```
