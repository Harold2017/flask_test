from flask import request, render_template, jsonify
from . import main
from .. import db
from ..models import User, Device, Permission
from flask_login import login_required, current_user
from ..decorators import admin_required, permission_required
from .forms import EditUserForm, Item, ItemTable


@main.route('/', methods=['GET', 'POST'])
def index():
    show_edit = False
    if current_user.is_administrator:
        show_edit = True
    return render_template("index.html", show_edit=show_edit)


@main.route('/calendar', methods=['GET', 'POST'])
def calendar():
    return render_template("calendar.html")


@main.route('/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit():
    form = EditUserForm()
    user = None
    if form.validate_on_submit():
        email = form.email.data
        device = form.device.data
        print(device)
        name = form.email.name
        role = form.email.role
        user = User.query.get_or_404(email=email)
    return render_template('edit.html', form=form, user=user)
