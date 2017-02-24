from flask import Blueprint

euler = Blueprint(
    'euler', __name__, template_folder='templates', static_folder='static')

from . import views
