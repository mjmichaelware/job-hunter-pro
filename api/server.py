# Vercel serverless entrypoint.
#
# Serves the EXACT same app as Cloud Run (Procfile: `gunicorn app:app`): the
# web/ cockpit UI plus the /api proxy to the legacy backend. Previously Vercel
# routed everything to api/index.py, which served a divergent dead legacy
# frontend (static/js/main.js). Pointing Vercel here keeps both deployments
# identical and on the canonical cockpit.
from app import app  # noqa: F401  (Vercel's @vercel/python serves this `app`)
