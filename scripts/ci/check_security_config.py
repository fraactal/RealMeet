from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def fail(message: str) -> None:
    raise SystemExit(f"security config check failed: {message}")


def read(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def main() -> int:
    workflow = read(".github/workflows/ci.yml")
    if "pull_request_target" in workflow:
        fail("workflow must not use pull_request_target")
    if "contents: read" not in workflow:
        fail("workflow must keep contents: read permission")
    if "secrets." in workflow:
        fail("CI workflow must not consume repository secrets for H1/H2 gates")
    if "security-check" not in workflow:
        fail("CI workflow must include the H2 security-check job")

    staging = read(".env.staging.example")
    for required in (
        "APP_ENV=staging",
        "DEBUG=false",
        "ENABLE_DOCS=false",
        "ENABLE_DEMO_SEED=false",
        "STAGING_ALLOW_LOCALHOST=false",
        "RATE_LIMIT_ENABLED=true",
        "WHATSAPP_WEBHOOK_REQUIRE_SIGNATURE=true",
    ):
        if required not in staging:
            fail(f".env.staging.example missing {required}")
    if "CORS_ORIGINS=*" in staging:
        fail("staging template cannot allow wildcard CORS")
    if "localhost" in staging:
        fail("staging template cannot include localhost defaults")

    frontend_env = read("frontend/.env.example")
    unexpected = [line for line in frontend_env.splitlines() if line and not line.startswith("#") and not line.startswith("VITE_API_URL=")]
    if unexpected:
        fail("frontend env template must expose only VITE_API_URL")

    gitignore = read(".gitignore")
    for pattern in (".env", ".env.*", "backups/", "*.dump", "*.backup"):
        if pattern not in gitignore:
            fail(f".gitignore missing sensitive artifact pattern {pattern}")

    print("Security configuration checks passed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
