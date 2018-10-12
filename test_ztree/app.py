from flask import Flask, render_template, jsonify, request
from flask_bootstrap import Bootstrap

app = Flask(__name__)
bootstrap = Bootstrap().init_app(app)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/base')
def base_page():
    return render_template('base.html')


@app.route('/nodes', methods=['POST'])
def nodes():
    data = request.get_json(force=True)
    id = str(data["id"])
    print(id)
    ret_dict = {
        "1": [{"name": "Table I--1", "id": "I_1", "pid": "1"},
              {"name": "Table I--2", "id": "I_2", "pid": "1"},
              {"name": "Table I--3", "id": "I_3", "pid": "1"}],
        "2": [{"name": "Table II--1", "id": "II_1", "pid": "2"},
              {"name": "Table II--2", "id": "II_2", "pid": "2"}],
        "3": [{"name": "Table III--1", "id": "III_1", "pid": "3",
               "children": [
                   {"name": "Table III--11", "id": "III_1_1", "pid": "III_1"},
                   {"name": "Table III--12", "id": "III_1_2", "pid": "III_1"},
                   {"name": "Table III--13", "id": "III_1_3", "pid": "III_1"}]}]
    }
    return jsonify(ret_dict.get(id))


if __name__ == '__main__':
    app.run(debug=True)
