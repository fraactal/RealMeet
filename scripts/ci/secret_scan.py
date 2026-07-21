from __future__ import annotations

import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


ALLOWLIST_VALUES = {
    "",
    "change-me-in-production",
    "realmeet",
    "secret",
    "test",
    "ci-test-secret-with-at-least-32-characters",
    "ci-smoke-secret-with-at-least-32-characters",
    "local-test-secret-with-at-least-32-chars",
    "staging-secret-with-at-least-32-chars",
}
ASSIGNMENT_SCAN_SUFFIXES = {
    ".env",
    ".example",
    ".ini",
    ".json",
    ".toml",
    ".yaml",
    ".yml",
}
ASSIGNMENT_SCAN_NAMES = {
    "Dockerfile",
}
SKIP_PARTS = {
    ".git",
    "node_modules",
    ".venv",
    "__pycache__",
    ".pytest_cache",
    "dist",
    "build",
}
SECRET_ASSIGNMENT = re.compile(
    r"(?i)\b(password|secret|token|api[_-]?key|client[_-]?secret|private[_-]?key|authorization)\b\s*[:=]\s*['\"]?([^'\"\s#]+)"
)
KNOWN_TOKEN_PATTERNS = {
    "aws_access_key": re.compile(r"AKIA[0-9A-Z]{16}"),
    "github_token": re.compile(r"gh[pousr]_[A-Za-z0-9_]{30,}"),
    "slack_token": re.compile(r"xox[baprs]-[A-Za-z0-9-]{20,}"),
    "private_key": re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----"),
    "mercado_pago_token": re.compile(r"(?:APP_USR|TEST)-[0-9A-Za-z_-]{20,}"),
}
REFERENCE_PATTERN = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    kind: str


def git_files() -> list[Path]:
    output = subprocess.check_output(["git", "ls-files"], text=True)
    return [Path(line) for line in output.splitlines() if line.strip()]


def should_skip(path: Path) -> bool:
    return any(part in SKIP_PARTS for part in path.parts)


def scan_text(path: Path, text: str) -> list[Finding]:
    findings: list[Finding] = []
    for line_number, line in enumerate(text.splitlines(), start=1):
        for kind, pattern in KNOWN_TOKEN_PATTERNS.items():
            if pattern.search(line):
                findings.append(Finding(str(path), line_number, kind))
        if should_scan_assignments(path):
            match = SECRET_ASSIGNMENT.search(line)
            if match:
                key = match.group(1).lower()
                value = match.group(2).strip().strip("'\"")
                if _assignment_is_allowed(key, value):
                    continue
                findings.append(Finding(str(path), line_number, "sensitive_assignment"))
    return findings


def should_scan_assignments(path: Path) -> bool:
    suffixes = set(path.suffixes)
    return path.name in ASSIGNMENT_SCAN_NAMES or bool(suffixes & ASSIGNMENT_SCAN_SUFFIXES)


def _assignment_is_allowed(key: str, value: str) -> bool:
    normalized = value.lower()
    if normalized in ALLOWLIST_VALUES:
        return True
    if key.endswith("token") and value.startswith("VERIFY_TOKEN_"):
        return True
    if "reference" in key and REFERENCE_PATTERN.fullmatch(value):
        return True
    if REFERENCE_PATTERN.fullmatch(value) and any(part in key for part in ("token", "secret", "password")):
        return True
    return False


def scan_worktree() -> list[Finding]:
    findings: list[Finding] = []
    for path in git_files():
        if should_skip(path) or not path.exists():
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        findings.extend(scan_text(path, text))
    return findings


def main() -> int:
    findings = scan_worktree()
    if findings:
        print("Potential secret findings detected. Values are intentionally suppressed.")
        for finding in findings:
            print(f"{finding.path}:{finding.line}: {finding.kind}")
        return 1
    print("No high-confidence secrets found.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
