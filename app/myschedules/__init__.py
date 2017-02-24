from flask import Blueprint

myschedules = Blueprint('myschedules', __name__, template_folder='templates')

from . import views
