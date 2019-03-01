# Simple Todo project structure:
## Backend
.
├── README
├── __init__.py
├── app
│   ├── __init__.py         # create_app factory function
│   ├── api
│   │   ├── __init__.py     # set blueprint
│   │   ├── routes.py       # add api routes
│   │   └── views.py        # handle requests
│   ├── main
│   │   ├── __init__.py     # set blueprint
│   │   └── views.py        # simple hello world test for launching the server
│   ├── models.py           # task model with some simple operation methods
│   └── utils.py            # several utils functions
├── config.py               # app config file
└── manage.py               # execute entrance


## React fontend
.
├── package.json
├── package-lock.json
├── public
│   ├── favicon.ico
│   ├── index.html
│   └── manifest.json
├── README.md
└── src
    ├── actions		    # actions for reducers
    │   └── taskActions.js
    ├── components	    # components of this simple todo app UI
    │   ├── TaskInput.js    # TaskInput -> TaskList -> Task
    │   ├── Task.js
    │   └── TaskList.js
    ├── containers
    │   ├── TaskApp.js      # TaskApp = TaskInput + TaskList
    │   ├── TaskInput.js
    │   └── TaskList.js
    ├── index.css
    ├── index.js
    ├── reducers
    │   └── tasks.js
    └── serviceWorker.js


************************************************************************************************

# RESTful Task API
## Task: GET (POST): 200, PUT: 201, DELETE: 204
## TaskList: GET, POST 

## Use Mariadb to store tasks data
### Task model:
	{
            "id": 1,
            "title": "test_0",
            "description": "this is a test description",
            "expiration": "2019-02-28T11:10:00",
            "task_uuid": "263e00c3-835c-43ae-a32b-1bae2e879e40",
            "is_finished": false
        }
## Use celery with rabbitmq to send notification 15 minutes before task expiration
## Use Flasgger to add Swagger UI, it can be accessed at `/apispec_1.json` endpoint


## GET to obtain one task
GET: http://localhost:8080/api/task/7/

### Receive and handle GET request at server side
127.0.0.1 - - [01/Mar/2019:09:57:47 +0800] "GET /api/task/7/ HTTP/1.1" 200 212 "-" "PostmanRuntime/7.6.0"

### Return data to client
{
    "id": 7,
    "title": "test_6",
    "description": "this is a test description",
    "expiration": "2019-03-01T10:15:00",
    "task_uuid": "ff7018e2-b805-4ee4-abd0-8ffd4b8b1bb2",
    "is_finished": false
}
************************************************************************************************

## GET to obtain all tasks
GET: http://localhost:8080/api/tasks/

### Receive and handle GET request at server side
2019-01-19 23:23:19,614 - 127.0.0.1 - - [19/Jan/2019 23:23:19] "GET /api/tasks/ HTTP/1.1" 200 -

### Return data to client
    "tasks": [
        {
            "id": 7,
            "title": "test_6",
            "description": "this is a test description",
            "expiration": "2019-03-01T10:15:00",
            "task_uuid": "ff7018e2-b805-4ee4-abd0-8ffd4b8b1bb2",
            "is_finished": false
        },
        {
            "id": 8,
            "title": "test_7",
            "description": "this is a test description",
            "expiration": "2019-03-01T10:20:00",
            "task_uuid": "e7523546-9386-4dba-88d2-9fcbed1126f4",
            "is_finished": false
        }
    ]
}

************************************************************************************************

## PUT to update task with certain task_id
PUT: http://localhost:8080/api/task/15/
body:
	{
		"title": "put to change title",
		"description": "put to change description",
    		"is_finished": true
	}

### Receive and handle PUT request at server side
127.0.0.1 - - [01/Mar/2019:10:11:34 +0800] "PUT /api/task/15/ HTTP/1.1" 201 49 "-" "PostmanRuntime/7.6.0"

### Return success data to client
{
    "message": "The task 15 has been updated",
    "task": {
        "id": 15,
        "title": "put to change title",
        "description": "put to change description",
        "task_uuid": "5d12bd27-8995-4ee8-9d88-0bc6c79ab158",
        "expiration": "2019-03-01T11:20:00",
        "is_finished": true
    }
}

************************************************************************************************

## DELETE to delete task with certain task_id
DELETE: http://localhost:8080/api/task/2/

### Receive and handle DELETE request at server side
127.0.0.1 - - [01/Mar/2019:10:13:31 +0800] "DELETE /api/task/2/ HTTP/1.1" 204 0 "-" "PostmanRuntime/7.6.0"

### Return success message to client
{
    "message": "The task 2 has been deleted"
}

************************************************************************************************

## Post to add task at client side
POST: http://localhost:8080/api/tasks/
HEADERS: Content-Type: application/json
BODY:
{
	"title": "test_6",
	"description": "this is a test description",
	"expiration": "2019-3-01T10:15:00"
}

### Receive and handle POST request at server side
127.0.0.1 - - [01/Mar/2019:09:56:42 +0800] "POST /api/tasks/ HTTP/1.1" 201 47 "-" "PostmanRuntime/7.6.0"

### Add task to celery mq
[2019-03-01 10:36:48,820: INFO/MainProcess] Received task: app.utils.alert_logger[fd8504c6-3909-4737-b73b-a8ad74a1b25b]  ETA:[2019-03-01 02:40:00.005505+00:00]  expires:[2019-03-01 02:55:00.005505+00:00]
### celery execute task at scheduled time
### celery use UTC time and my server and client use Asia/Shanghai timezone
### simply show the warning info through logging
[2019-03-01 10:40:00,237: WARNING/ForkPoolWorker-5] Task {'id': 13, 'title': 'test_12', 'description': 'this is a test description', 'task_uuid': 'fd8504c6-3909-4737-b73b-a8ad74a1b25b', 'expiration': '2019-03-01T10:55:00', 'is_finished': False} executed!
[2019-03-01 10:40:00,238: INFO/ForkPoolWorker-5] Task {'id': 13, 'title': 'test_12', 'description': 'this is a test description', 'task_uuid': 'fd8504c6-3909-4737-b73b-a8ad74a1b25b', 'expiration': '2019-03-01T10:55:00', 'is_finished': False} of will expire in 15 mins
[2019-03-01 10:40:00,238: WARNING/ForkPoolWorker-5] Task 'fd8504c6-3909-4737-b73b-a8ad74a1b25b' successfully done!
[2019-03-01 10:40:00,238: INFO/ForkPoolWorker-5] Task app.utils.alert_logger[fd8504c6-3909-4737-b73b-a8ad74a1b25b] succeeded in 0.0013924500090070069s: None

## Return success message to client
{
    "message": "The task 11 has been created"
}


# React fontend
## Problems occurred:
	- Redux does not accept async actions -> use XHR sync
	- CORS -> set headers and successfully request but response body without data -> try localStorage...
### App with localStorage performs OK now, next try middleware of redux to enable async actions