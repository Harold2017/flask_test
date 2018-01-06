from flask import Flask
from flask import render_template
from flask import request
import json


app = Flask(__name__)


@app.route('/')
def welcome():
    return "Welcome to Test!"


@app.route('/signup')
def signup():
    return render_template('signup.html')


@app.route('/signupuser', methods=['POST'])
def signupuser():
    user = request.form['username']
    password = request.form['password']
    return json.dumps({'status': 'OK', 'user': user, 'pass': password})


if __name__ == '__main__':
    app.run()
