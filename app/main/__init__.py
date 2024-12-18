from flask import Blueprint

bp = Blueprint('main', __name__)

from app.main import routes

from app.models import Permission

@bp.app_context_processor
def inject_permissions():
    return dict(Permission=Permission)