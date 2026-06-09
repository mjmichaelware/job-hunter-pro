import sys
import json
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

try:
    from app import app
except Exception as e:
    print(f"FAIL: could not import app: {e}")
    sys.exit(1)

c = app.test_client()

def get(path, expect=200):
    r = c.get(path)
    label = "OK" if r.status_code == expect else "FAIL"
    print(f"[{label}] GET {path} -> {r.status_code}")
    if r.status_code != expect:
        sys.exit(1)
    return r

get("/")
get("/api/providers")
get("/api/health")

dry = get("/api/jobs?dry_run=1").get_json()
if not dry or dry.get("dry_run") is not True:
    print("FAIL: /api/jobs?dry_run=1 did not return dry_run=true")
    print(json.dumps(dry, indent=2)[:500])
    sys.exit(1)
print("[OK] dry_run=true confirmed")

surface = c.get("/api/_surface")
if surface.status_code == 200:
    data = surface.get_json() or {}
    if data.get("placeholder_blueprint_registered") is True:
        print("FAIL: placeholder blueprint shadow detected")
        sys.exit(1)
    print(f"[OK] _surface placeholder_blueprint_registered={data.get('placeholder_blueprint_registered')}")
else:
    print(f"WARN: /api/_surface unavailable -> {surface.status_code}")

print("PASS safe local proof")
