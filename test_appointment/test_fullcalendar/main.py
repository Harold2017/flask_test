from flask import Flask
from flask import request, render_template, jsonify
import json
from flask_bootstrap import Bootstrap
import time
from flask_sqlalchemy import SQLAlchemy
import os
from datetime import datetime, date, timedelta


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard to guess string'
    SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
                              ('mysql://flask_test:123456@localhost/flask_test')


app = Flask(__name__)
# app.config.from_object(Config)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://flask_test:123456@localhost/flask_test'
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
bootstrap = Bootstrap()
bootstrap.init_app(app)
db = SQLAlchemy(app)
# db.init_app(app)  # to create table first, cannot use db.init_app(app), why???


class Event(db.Model):
    __tablename__ = 'events'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), index=True)
    start = db.Column(db.DateTime(), default=datetime.utcnow)
    end = db.Column(db.DateTime())

    def __init__(self, name, start, end):
        self.name = name
        self.start = start
        self.end = end

    def __repr__(self):
        return '<Event %r>' % self.id


@app.route('/')
def calendar():
    return render_template("calendar.html")


@app.route('/data', methods=['GET', 'POST'])
def return_data():
    '''start_date = request.args.get('start', '')
    end_date = request.args.get('end', '')
    # You'd normally use the variables above to limit the data returned
    # you don't want to return ALL events like in this code
    # but since no db or any real storage is implemented I'm just
    # returning data from a text file that contains json elements
    print(start_date)

    with open("test.json", "r") as input_data:
        # you should use something else here than just plaintext
        # check out jsonfiy method or the built in json module
        # http://flask.pocoo.org/docs/0.10/api/#module-flask.json
        return "[" + input_data.read() + "]"'''
    # r = request.args.get('start')
    # print(r)
    now = datetime.today().date()
    # print(now)
    end = now + timedelta(days=14)
    events = Event.query.filter(Event.start.between(now, end)).all()
    response = []
    for event in events:
        response.append({"title": event.name + ' Event ID: ' + str(event.id), "start": event.start, "end": event.end, "id": event.id})
    return jsonify(response)


'''date_handler = lambda obj: (
    obj.isoformat()
    if isinstance(obj, (datetime, date))
    else None
)
json.dumps(datetime.now(), default=date_handler)'''


@app.route('/add', methods=['POST'])
def add_data():
    r = request.get_json(force=True)
    start_date = datetime.strptime(r['start'], '%Y-%m-%dT%H:%M:%S.%fZ')  # transfer to datetime type to compare
    end_date = datetime.strptime(r['end'], '%Y-%m-%dT%H:%M:%S.%fZ')
    title = r['title']
    events = Event.query.all()
    for event in events:
        if start_date <= event.start <= event.end:  # TypeError: unorderable types: str() <= datetime.datetime()
            print("Invalid")
            # print(jsonify({"blocked": 1}))
            return jsonify({"blocked": 1})
    print(title, start_date, end_date)
    event_new = Event(name=title, start=start_date, end=end_date)
    db.session.add(event_new)
    db.session.commit()
    return jsonify({"blocked": 0})


@app.route('/remove', methods=['POST'])
def remove_data():
    r = request.get_json(force=True)
    event_id = r['event_id']
    event = Event.query.filter_by(id=event_id).first()
    db.session.delete(event)
    db.session.commit()
    return jsonify({"id": event.id})


if __name__ == '__main__':
    # db.create_all()  # execute from python console but still failed...
    app.debug = True
    app.run()
