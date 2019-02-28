from flask_restful import reqparse, abort, Resource, fields, marshal_with
from ..models import Task
from datetime import datetime


class ExpirationDateTimeCase(fields.Raw):
    """
    Handle the condition expiration does NOT exist
    """
    def format(self, value):
        try:
            print(value)
            return datetime.strftime(value, '%Y-%m-%dT%H:%M:%S') if value else str(value)
        except Exception:
            raise fields.MarshallingException


# confine response structure
response_fields = {
    'id': fields.Integer,
    'title': fields.String,
    'description': fields.String,
    'expiration': ExpirationDateTimeCase,
    'task_uuid': fields.String,
    'is_finished': fields.Boolean
}

response_fields_list = {
    'tasks': fields.List(fields.Nested(response_fields))
}


# debug
'''
from . import api_bp
from flask import request


@api_bp.before_request
def before_request():
    headers = request.headers
    method = request.method
    ip = request.remote_addr
    url = request.url
    form = request.form  # post body
    args = request.args  # query string in url
    values = request.values
    path = request.path
    base_url = request.base_url
    url_root = request.url_root
    res = {'headers': headers, 'method': method, 'ip': ip, 'url': url, 'form': form, 'args': args, 'values': values}
    # print(res)
    # print(request.get_json())  # json
'''


def abort_if_not_exist(task_id):
    """
    Handle 404 Error
    :param task_id: int
    :return: abort info
    """
    if not Task.get_task_by_id(task_id):
        abort(404, message="Task {} doesn't exist".format(task_id))


class TaskHandler(Resource):
    """
    Task handler for RUD, Create will be handled by TasksListHandler
    """

    def req_parse(self):
        """
        Handle incoming request
        :return: parsed args
        """
        parser = reqparse.RequestParser()
        # title, description required but expiration optional
        parser.add_argument('title', type=str, help='task title', location='json', required=True)
        parser.add_argument('description', type=str, help='task description', location='json', required=True)
        parser.add_argument('expiration', type=str, help='expiration time', location='json')
        args = parser.parse_args()
        return args

    @marshal_with(response_fields)
    def get(self, task_id):
        """
        Get particular task by its ID
        ---
        tags:
            - restful
        parameters:
            - in: path
              name: task_id
              required: true
              description: The ID of the task, Integer
              type: integer
        responses:
            200:
              description: Task details
              schema:
                id: Task
                properties:
                  id:
                    type: integer
                    default: 0
                  title:
                    type: string
                    default: My task
                  description:
                    type: string
                    default: My task description
                  expiration:
                    type: string
                    default: 2019-02-28T11:10:00
                  task_uuid:
                    type: string
                    default: 263e00c3-835c-43ae-a32b-1bae2e879e40
                  is_finished:
                    type: bool
                    default: false
        """
        abort_if_not_exist(task_id)
        res = Task.get_task_by_id(task_id)
        return res, 200

    def put(self, task_id):
        """
        Edit particular task by its ID
        ---
        tags:
            - restful
        parameters:
            - in: body
              name: body
              schema:
                $ref: '#/definitions/Task'
            - in: path
              name: task_id
              required: true
              description: The ID of the task, Integer
              type: integer
        responses:
            201:
              description: The task `task_id` has been updated
              schema:
                $ref: '#/definitions/Task'
        """
        abort_if_not_exist(task_id)
        args = self.req_parse()
        Task.update_task_by_id(task_id, args)
        return {"message": "The task " + task_id + " has been updated"}, 201

    def delete(self, task_id):
        """
        Delete particular task by its ID
        ---
        tags:
            - restful
        parameters:
            - in: path
              name: task_id
              required: true
              description: The ID of the task, Integer
              type: integer
        responses:
            204:
              description: The task `task_id` has been deleted
        """
        abort_if_not_exist(task_id)
        Task.delete_task_by_id(task_id)
        return {"message": "The task " + task_id + " has been deleted"}, 204

    def post(self, task_id):
        """
        The same with GET method
        """
        return self.get(task_id)


class TasksListHandler(Resource):
    """
    Tasks handler for CR, Update and Delete is handled by TaskHandler
    """

    def req_parse(self):
        parser = reqparse.RequestParser()
        parser.add_argument('title', type=str, help='task title', location='json', required=True)
        parser.add_argument('description', type=str, help='task description', location='json', required=True)
        parser.add_argument('expiration', type=str, help='expiration time', location='json')
        args = parser.parse_args()
        return args

    @marshal_with(response_fields_list)
    def get(self):
        """
        Get all tasks
        ---
        tags:
            - restful
        responses:
            200:
              description: All tasks data in JSON array
              schema:
                id: Tasks
                properties:
                  tasks:
                    type: array
                    items:
                      $ref: '#/definitions/Task'
        """
        res = Task.get_tasks_list()
        return {'tasks': res}, 200

    def post(self):
        """
        Add task to tasks list
        ---
        tags:
            - restful
        parameters:
            - in: body
              name: body
              schema:
                $ref: '#/definitions/Task'
        responses:
            201:
              description: The task has been created
              schema:
                $ref: '#/definitions/Task'
        """
        args = self.req_parse()
        Task.insert_task(args)
        return {"message": "The task has been created"}, 201
