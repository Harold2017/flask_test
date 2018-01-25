from flask import request, render_template, jsonify
from . import main
from .. import db
from ..models import User, Device


@main.route('/')
def index():
    return render_template("index.html")


@main.route('/calendar', methods=['GET', 'POST'])
def calendar():
    return render_template("calendar.html")
