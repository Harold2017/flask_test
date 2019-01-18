from flask import render_template, current_app
from . import task
from flask_login import login_required, current_user
from .. import utils


@task.route('/calendar', methods=['GET', 'POST'])
@login_required
def calendar():
    token = utils.generate_access_token(current_app, current_user.id)
    return render_template("tasks/calendar.html", user_id=current_user.id, token=token)
