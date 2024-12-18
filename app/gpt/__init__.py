from flask import Blueprint

bp = Blueprint('gpt',__name__)

from app.gpt import routes