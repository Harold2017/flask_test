from flask import request, render_template, jsonify
from . import main
from .. import db
from ..models import User, Device, Permission
from flask_login import login_required, current_user
from ..decorators import admin_required, permission_required


@main.route('/')
def index():
    return render_template("index.html")


@main.route('/calendar', methods=['GET', 'POST'])
def calendar():
    return render_template("calendar.html")


@main.route('/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit():
    pass
