from flask import Flask
from flask import request, render_template, jsonify
import json
from flask_bootstrap import Bootstrap


app = Flask(__name__)
bootstrap = Bootstrap()
bootstrap.init_app(app)


@app.route('/')
def calendar():
    return render_template("calendar.html")


@app.route('/data')
def return_data():
    start_date = request.args.get('start', '')
    end_date = request.args.get('end', '')
    # You'd normally use the variables above to limit the data returned
    # you don't want to return ALL events like in this code
    # but since no db or any real storage is implemented I'm just
    # returning data from a text file that contains json elements

    with open("events.json", "r") as input_data:
        # you should use something else here than just plaintext
        # check out jsonfiy method or the built in json module
        # http://flask.pocoo.org/docs/0.10/api/#module-flask.json
        return input_data.read()


@app.route('/add', methods=['POST'])
def add_data():
    r = request.get_json(force=True)
    start_date = r['start']
    end_date = r['end']
    print(start_date, end_date)
    return jsonify({'test': 1})


if __name__ == '__main__':
    app.debug = True
    app.run()
