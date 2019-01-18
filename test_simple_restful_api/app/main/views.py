from flask import render_template
from . import main


@main.route('/', methods=['GET'])
def index():
    return render_template('index.html')


@main.route('/user', methods=['GET', 'POST'])
def user():
    pass
