from ..models import Task
from . import api
from flask import request, jsonify, current_app
from datetime import datetime, timedelta
from sqlalchemy import and_
from .. import utils
from celery import uuid
from celery.task.control import revoke


@api.route('/v1.0/tasks/<user_id>/<token>', methods=['GET'])
def return_data(user_id, token):
    if not user_id or not token:
        return "Invalid user ID or token", 400
    user_id = int(user_id)
    # print(user_id, token)
    if not utils.verify_access_token(current_app, user_id, token):
        return "Invalid user ID or token", 400
    # print(request.args)
    # print(request.args['start'][:10])
    start = datetime.strptime(request.args['start'][:10], '%Y-%m-%d')
    end = datetime.strptime(request.args['end'][:10], '%Y-%m-%d')
    Task.query.filter_by(user_id=user_id).first_or_404()
    tasks = Task.query.filter(
        and_(Task.user_id == user_id,
             Task.start.between(start, end))
    ).all()
    response = []
    for task in tasks:
        if not task.is_finished:
            if task.end > datetime.utcnow():
                response.append(
                    {"title": task.title + ' Task ID: ' + str(task.id) + ' Description: ' + str(task.description),
                     "start": task.start,
                     "end": task.end,
                     "id": task.id})
            else:
                task.is_finished = True
                task.save()
                response.append(
                    {"title": task.title + ' Task ID: ' + str(task.id) + ' Description: ' + str(task.description),
                     "start": task.start,
                     "end": task.end,
                     "id": task.id,
                     "color": 'black',
                     "textColor": 'white'})
        else:
            response.append(
                {"title": task.title + ' Task ID: ' + str(task.id) + ' Description: ' + str(task.description),
                 "start": task.start,
                 "end": task.end,
                 "id": task.id,
                 "color": 'black',
                 "textColor": 'white'})
    return jsonify(response), 200


@api.route('/v1.0/add/<user_id>/<token>', methods=['POST'])
def add_task(user_id, token):
    if not user_id or not token:
        return "Invalid user ID or token", 400
    user_id = int(user_id)
    if not utils.verify_access_token(current_app, user_id, token):
        return "Invalid user ID or token", 400

    r = request.get_json(force=True)
    if r['title'] == '' or r['description'] == '' or r['start'] == '' or r['end'] == '':
        return jsonify({"blocked": 2})

    start_date = datetime.strptime(r['start'], '%Y-%m-%dT%H:%M:%S.%fZ')
    end_date = datetime.strptime(r['end'], '%Y-%m-%dT%H:%M:%S.%fZ')
    title = r['title']
    description = r['description']
    events = Task.query.filter(
        and_(Task.user_id == user_id,
             Task.start.between(start_date, end_date))
    ).all()

    if len(events) == 0:
        task_new = Task(title=title, user_id=user_id, start=start_date, end=end_date, description=description)
    else:
        for event in events:
            if not event.is_finished:
                return jsonify({"blocked": 3})
            else:
                continue

        task_new = Task(title=title, user_id=user_id, start=start_date, end=end_date, description=description)

    task_new.task_uuid = uuid()
    task_new.save()

    countdown = (end_date - timedelta(0, 60 * 15, 0) - datetime.utcnow()).total_seconds()
    # print(countdown)

    # task reminder 15 mins before expiration
    utils.alert_logger.apply_async(args=[user_id, task_new.to_json()], countdown=countdown,
                                   expires=countdown + 15 * 60, task_id=task_new.task_uuid)

    return jsonify({"blocked": 0, "id": task_new.id}), 200


@api.route('/v1.0/remove/<user_id>/<token>', methods=['POST'])
def remove_task(user_id, token):
    if not user_id or not token:
        return "Invalid user ID or token", 400
    user_id = int(user_id)
    if not utils.verify_access_token(current_app, user_id, token):
        return "Invalid user ID or token", 400

    r = request.get_json(force=True)
    task_id = r['task_id']
    task = Task.query.filter_by(id=task_id).first_or_404()
    if user_id == task.user_id and not task.is_finished:
        revoke(task.task_uuid, terminate=True)
        task.delete()
        return jsonify({"id": task.id}), 200
    elif user_id != task.user_id:
        return "No permission to access this task", 402
    else:
        return "You can Not remove a complete event", 402
