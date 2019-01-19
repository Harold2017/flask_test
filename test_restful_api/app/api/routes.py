from .views import TaskHandler, TasksListHandler
from . import api


# define api routes
api.add_resource(TasksListHandler, '/tasks/')
api.add_resource(TaskHandler, '/task/<string:task_id>/')
