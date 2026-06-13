"""
Disabled legacy SerpAPI debug script.

Do not hardcode or print provider keys. Use Secret Manager-backed diagnostics
only after the approved stage gate.
"""

raise SystemExit("debug_serp.py is disabled; do not hardcode secrets.")
