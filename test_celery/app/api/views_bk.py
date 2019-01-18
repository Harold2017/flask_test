from ..models import User
from . import api
from flask import request, jsonify, current_app
from .. import utils


@api.route('/v1.0/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return jsonify({"token": "Your token is invalid or expired!"})
    r = request.get_json(force=True)
    if r is None:
        return "No Data Posted", 400
    username = r['username']
    password = r['password']
    user = User.query.filter_by(email=username).first()
    if user is not None and user.verify_password(password):
        token = utils.generate_access_token(current_app, user)
        return jsonify({"token": token}), 200
    else:
        return jsonify({"token": "Your username / password is invalid!"})


@api.route('v1.0/get_apples/<token>', methods=['GET'])
def get_apples(token):
    if not token:
        return jsonify({"token": "Your token is invalid or expired!"})
    # utils.verify_access_token(current_app, )
