from flask import Blueprint

appointment = Blueprint('appointment', __name__)

from . import views
