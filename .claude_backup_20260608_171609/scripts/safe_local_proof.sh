#!/usr/bin/env bash
set -euo pipefail
python3 -m py_compile $(git ls-files "*.py")
python3 - <<'LOCALPROOF'
from app import app
c = app.test_client()
for path in ["/", "/api/health", "/api/usage", "/api/jobs?dry_run=1", "/api/providers"]:
    r = c.get(path)
    print(path, r.status_code, r.content_type)
    assert r.status_code == 200
dry = c.get("/api/jobs?dry_run=1").get_json()
assert dry.get("dry_run") is True
print("PASS safe local proof")
LOCALPROOF
git diff --check
git diff --stat
