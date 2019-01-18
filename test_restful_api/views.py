from flask_restful import reqparse, abort, Resource
from .models import Task


def abort_if_not_exist(task_id):
    if not Task.get_task_by_id(task_id):
        abort(404, message="Task {} doesn't exist".format(task_id))


parser = reqparse.RequestParser()
parser.add_argument('title')
parser.add_argument('description')
parser.add_argument('expiration')


class TaskHandler(Resource):

    def get(self, task_id):
        abort_if_not_exist(task_id)
        res = Task.get_task_by_id(task_id)
        return res, 200

    def put(self, task_id):
        abort_if_not_exist(task_id)
        args = parser.parse_args()
        Task.update_task_by_id(task_id, args)
        return {"status": "success"}, 200

    def delete(self, task_id):
        abort_if_not_exist(task_id)
        Task.delete_task_by_id(task_id)
        return {"status": "success"}, 200

    def post(self, task_id):
        return self.get(task_id)


class TasksListHandler(Resource):

    def get(self):
        res = Task.get_tasks_list()
        return res, 200

    def post(self):
        args = parser.parse_args()
        Task.insert_task(args)
        return {"status": "success"}, 200
