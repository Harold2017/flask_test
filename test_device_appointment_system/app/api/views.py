from ..models import User, AppointmentEvents, Device, user_device
from .. import db
from . import api
from flask import request, jsonify
from datetime import datetime
from sqlalchemy import and_
import re


@api.route('/v1.0/data/<device_id>', methods=['POST'])
def return_data(device_id):
    if device_id is None:
        return "No valid device ID", 401
    device_id = int(device_id)
    r = (request.stream.read()).decode("utf-8")
    r = re.findall(r'\d*-\d*-\d*', r)
    start = datetime.strptime(r[0], '%Y-%m-%d')
    end = datetime.strptime(r[1], '%Y-%m-%d')
    events = AppointmentEvents.query.filter(
        and_(AppointmentEvents.device_id == device_id,
             AppointmentEvents.start.between(start, end))
    ).all()
    response = []
    for event in events:
        if not event.is_finished:
            response.append({"title": event.name + ' Event ID: ' + str(event.id) + ' Remark: ' + str(event.remark),
                             "start": event.start,
                             "end": event.end,
                             "id": event.id})
        else:
            response.append({"title": event.name + ' Event ID: ' + str(event.id) + ' Remark: ' + str(event.remark),
                             "start": event.start,
                             "end": event.end,
                             "id": event.id,
                             "color": 'black',
                             "textColor": 'white'})
    return jsonify(response), 200


@api.route('/v1.0/add/<token>/<device_id>', methods=['POST'])
def add_data(token, device_id):
    if token is None:
        return "No valid token", 401
    if device_id is None:
        return "No valid device ID", 401
    user = User.query.filter_by(avatar_hash=token).first_or_404()
    # devices = user.devices.all()
    device_id = int(device_id)
    # not available?
    # ud = user_device.query.join(User, Device).filter(User.id == user.id,
    #                                                  Device.id == device_id).first()
    # if device_id not in devices:
    # if ud is None:
    device = Device.query.filter_by(id=device_id).first_or_404()
    if user not in device.users:
        return "No permission to access {0}".format(device_id), 401
    r = request.get_json(force=True)

    if r['title'] == '' or r['remark'] == '' or r['start'] == '' or r['end'] == '':
        return jsonify({"blocked": 2})

    start_date = datetime.strptime(r['start'], '%Y-%m-%dT%H:%M:%S.%fZ')
    end_date = datetime.strptime(r['end'], '%Y-%m-%dT%H:%M:%S.%fZ')
    title = r['title']
    remark = r['remark']
    # print(start_date.time())
    # print(type(title))
    # print(title == '')
    events = AppointmentEvents.query.filter(
        and_(AppointmentEvents.device_id == device_id,
             AppointmentEvents.start.between(start_date, end_date))
    ).all()

    if len(events) == 0:
        event_new = AppointmentEvents(name=title, user_id=user.id, device_id=device_id, start=start_date, end=end_date,
                                      remark=remark)
        db.session.add(event_new)
        db.session.commit()
    else:
        for event in events:
            if not event.is_finished:
                return jsonify({"blocked": 3})
            else:
                continue

        event_new = AppointmentEvents(name=title, user_id=user.id, device_id=device_id, start=start_date, end=end_date,
                                      remark=remark)
        db.session.add(event_new)
        db.session.commit()

    return jsonify({"blocked": 0, "id": event_new.id}), 200


@api.route('/v1.0/remove/<token>/<device_id>', methods=['POST'])
def remove_data(token, device_id):
    if token is None:
        return "No valid token", 401
    if device_id is None:
        return "No valid device ID", 401
    user = User.query.filter_by(avatar_hash=token).first()
    # privilege = list(map(int, user.privilege.split(',')))
    device_id = int(device_id)
    device = Device.query.filter_by(id=device_id).first_or_404()
    if user not in device.users:
        return "No permission to access {0}".format(device_id), 401
    r = request.get_json(force=True)
    event_id = r['event_id']
    event = AppointmentEvents.query.filter_by(id=event_id).first_or_404()
    if user.id == event.user_id and not event.is_finished:
        db.session.delete(event)
        db.session.commit()
        return jsonify({"id": event.id}), 200
    elif user.id != event.user_id:
        return "No permission to access this event", 401
    else:
        return "You can Not remove a complete event", 401
