from flask import Blueprint

ivr = Blueprint('ivr', __name__)

from . import views
