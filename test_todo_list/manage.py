from app import create_app, db
from app.models import User, Todo, Todo_list, Role
from flask_script import Manager, Shell


app = create_app('default')
manager = Manager(app)


def make_shell_context():
    return dict(app=app, db=db, User=User, Role=Role, Todo=Todo, Todo_list=Todo_list)


manager.add_command("shell", Shell(make_context=make_shell_context))


if __name__ == '__main__':
    manager.run()
