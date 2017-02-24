from flask import Blueprint

manager = Blueprint(
    'manager', __name__, template_folder='templates', static_folder='static')

from . import views
