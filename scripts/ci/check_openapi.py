from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
BACKEND = ROOT / "backend"
sys.path.insert(0, str(BACKEND))

from app.main import app  # noqa: E402


def main() -> int:
    schema = app.openapi()
    json.dumps(schema)

    operation_ids: list[str] = []
    for path, methods in schema.get("paths", {}).items():
        if not isinstance(methods, dict):
            continue
        for method, operation in methods.items():
            if method.lower() not in {"get", "post", "put", "patch", "delete", "options", "head"}:
                continue
            if not isinstance(operation, dict):
                continue
            operation_id = operation.get("operationId")
            if not operation_id:
                print(f"Missing operationId for {method.upper()} {path}", file=sys.stderr)
                return 1
            operation_ids.append(str(operation_id))

    duplicates = sorted(item for item, count in Counter(operation_ids).items() if count > 1)
    if duplicates:
        print("Duplicate OpenAPI operationId values found:", file=sys.stderr)
        for operation_id in duplicates:
            print(f"- {operation_id}", file=sys.stderr)
        return 1

    print(f"OpenAPI schema valid: {len(operation_ids)} operations, no duplicate operationId values")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
