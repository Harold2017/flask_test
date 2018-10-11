from flask import Flask, render_template, jsonify, request
from flask_bootstrap import Bootstrap


app = Flask(__name__)
bootstrap = Bootstrap().init_app(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/nodes')
def nodes():
    return None


if __name__ == '__main__':
    app.run(debug=True)
