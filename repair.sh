#!/usr/bin/env bash
set -euo pipefail

for f in app.py web/templates/index.html web/static/css/base.css web/static/css/layout.css web/static/js/ambient.js; do
  [ -f "$f" ] || { echo "MISSING: $f — wrong directory?"; exit 1; }
done

TS="$(date +%Y%m%d_%H%M%S)"
cp web/templates/index.html "web/templates/index.html.bak.$TS"
cp web/static/css/base.css "web/static/css/base.css.bak.$TS"
cp web/static/js/ambient.js "web/static/js/ambient.js.bak.$TS"

python3 - <<'PY'
from pathlib import Path
import re

b = Path("web/static/css/base.css")
t = b.read_text(encoding="utf-8")
loose = """font-family: system-ui, -apple-system, sans-serif;
background-color: var(--bg);
color: var(--text);
color-scheme: dark;
line-height: 1.6;
-webkit-font-smoothing: antialiased;
}"""
fixed = "body {\n  " + loose.replace("\n", "\n  ")
if loose in t:
    b.write_text(t.replace(loose, fixed, 1), encoding="utf-8")
    print("base.css: body block fixed")
elif "body {\n  font-family: system-ui" in t:
    print("base.css: already fixed")
else:
    print("base.css: loose block NOT found — left as-is, inspect manually")

h = Path("web/templates/index.html")
t = h.read_text(encoding="utf-8")
assert "<html" in t and "<body" in t, "index.html: no normal <html>/<body>"
t = "\n".join(l for l in t.splitlines() if not ("<canvas" in l and "ambient-canvas" in l))
t = re.sub(r'\s*<canvas\b[^>]*id=["\']webgpu-canvas["\'][^>]*></canvas>\s*', "\n", t, flags=re.IGNORECASE)
out = []
done = False
for l in t.splitlines():
    out.append(l)
    if not done and "<body" in l:
        out.append('    <canvas id="webgpu-canvas" aria-hidden="true"></canvas>')
        done = True
t = "\n".join(out).rstrip() + "\n"
assert done, "index.html: could not insert canvas after <body>"
assert t.count('id="webgpu-canvas"') == 1, "index.html: expected exactly one webgpu-canvas"
assert "ambient-canvas" not in t, "index.html: ambient-canvas still present"
h.write_text(t, encoding="utf-8")
print("index.html: canvas normalized")

j = Path("web/static/js/ambient.js")
t = j.read_text(encoding="utf-8")
if "ambient-canvas" in t:
    j.write_text(t.replace("ambient-canvas", "webgpu-canvas"), encoding="utf-8")
    print("ambient.js: id updated")
else:
    print("ambient.js: already correct")
PY

echo
echo "Compiling Python..."
python3 -m py_compile $(git ls-files '*.py')

echo
echo "Local proof..."
python3 - <<'PY'
from app import app
c = app.test_client()
r = c.get("/")
print("GET / =", r.status_code)
assert r.status_code == 200
html = r.get_data(as_text=True)
assert html.count('id="webgpu-canvas"') == 1, "canvas count != 1"
assert "ambient-canvas" not in html, "ambient-canvas still in HTML"
for p in ["/static/css/base.css", "/static/css/layout.css",
          "/static/css/components.css", "/static/css/charts.css",
          "/static/js/ambient.js"]:
    rr = c.get(p)
    print("GET", p, "=", rr.status_code)
    assert rr.status_code == 200, p + " did not serve 200"
js = c.get("/static/js/ambient.js").get_data(as_text=True)
assert "webgpu-canvas" in js and "ambient-canvas" not in js, "ambient.js id not aligned"
h = c.get("/api/health")
print("GET /api/health =", h.status_code, "(informational)")
print("LOCAL PROOF PASSED")
PY

echo
echo "DONE. Nothing deployed. Start your local server and refresh."
