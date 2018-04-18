from flask import Blueprint

apply = Blueprint('apply', __name__)

from . import views
