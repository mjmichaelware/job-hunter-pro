from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

# These modular routes are preserved as per R9 requirements
from . import providers
from . import industries
from . import applications
from . import ingest

# These routes are now handled by the proxy to api.index in app.py
# to ensure live data parity:
# - health
# - usage
# - jobs
# - opportunities
# - history
# - research
# - why_three
# - batches
# - batch
