from flask import Blueprint

api_bp = Blueprint('api', __name__, url_prefix='/api')

from . import health
from . import usage
from . import jobs
from . import opportunities
from . import history
from . import research
from . import providers
from . import industries
from . import applications
from . import ingest
from . import why_three
