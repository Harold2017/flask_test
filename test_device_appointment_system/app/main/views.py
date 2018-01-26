from flask import request, render_template, jsonify
from . import main
from .. import db
from ..models import User, Device, Permission
from flask_login import login_required, current_user
from ..decorators import admin_required, permission_required
from .forms import EditUserForm


@main.route('/', methods=['GET', 'POST'])
def index():
    show_edit = False
    if current_user.is_authenticated:
        show_edit = bool(request.cookies.get('show_edit', ''))
    if show_edit:
        pass
    return render_template("index.html", show_edit=show_edit)


@main.route('/calendar', methods=['GET', 'POST'])
def calendar():
    return render_template("calendar.html")


@main.route('/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit():
    form = EditUserForm()
    if form.validate_on_submit():
        pass
