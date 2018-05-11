import unittest
import json
import re
from flask import url_for
from app import create_app, db
from app.models import User, AppointmentEvents, Device, user_device
import datetime


def add_fake_date():
    u = User(name="test_user", email="test@test.com", role_id=2)
    d = Device(name="test_device")
    d.users.append(u)
    try:
        db.session.add(u)
        db.session.add(d)
        db.session.commit()
    except Exception as e:
        print(e)
        db.session.roll_back()
        db.session.flush()
    return {
        "user": u,
        "device": d
    }


class APITestCase(unittest.TestCase):
    def setUp(self):
        """
        setup test environment
        :return: None
        """
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        # add fake data to db
        self.data = add_fake_date()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_404(self):
        response = self.client.get('/wrong/url')
        self.assertTrue(response.status_code == 404)

    def test_posts_add_data(self):
        # add a appointment event
        user = self.data["user"]
        device = self.data["device"]
        # add a user with no auth to device
        user_no_auth = User(name="test_no_auth", email="t@t.com", role_id=2)
        db.session.add(user_no_auth)
        db.session.commit()

        data_dict = {'title': 'test',
                     'start': (datetime.datetime.utcnow() -
                                                         datetime.timedelta(seconds=7200)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                     'end': (datetime.datetime.utcnow() +
                                                       datetime.timedelta(seconds=7200)).strftime('%Y-%m-%dT%H:%M:%S.%fZ'),
                     'remark': 'test'
                     }
        data = json.dumps(data_dict)

        # without token or without device_id
        response = self.client.post(
            url_for('api.add_data', token='a', device_id=device.id),
            data=data
        )
        self.assertTrue(response.status_code == 401)

        response = self.client.post(
            url_for('api.add_data', token=user.avatar_hash, device_id=''),
            data=data
        )
        self.assertTrue(response.status_code == 404)

        # user with auth to device
        response = self.client.post(
            url_for('api.add_data', token=user.avatar_hash, device_id=device.id),
            data=data
        )
        ae = AppointmentEvents.query.filter_by(device_id=device.id).filter_by(user_id=user.id).all()
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['blocked'] == 0)
        self.assertTrue(json_response['id'] == ae[-1].id)

        # user with no auth to device
        response = self.client.post(
            url_for('api.add_data', token=user_no_auth.avatar_hash, device_id=device.id),
            data=data
        )
        self.assertTrue(response.status_code == 401)

        # user with auth but request data not fulfill
        data_fail_list = []
        for key, value in data_dict.items():
            tmp = data_dict
            tmp[key] = ''
            data_fail_list.append(tmp)
        for data_fail in data_fail_list:
            response = self.client.post(
                url_for('api.add_data', token=user.avatar_hash, device_id=device.id),
                data=data_fail
            )
            json_response = json.loads(response.data.decode('utf-8'))
            self.assertTrue(json_response['blocked'], 2)

        # user with auth but request data conflict with existed data
        response = self.client.post(
            url_for('api.add_data', token=user.avatar_hash, device_id=device.id),
            data=data
        )
        json_response = json.loads(response.data.decode('utf-8'))
        self.assertTrue(json_response['blocked'] == 3)

    def test_posts_remove_data(self):
        # no data is required for this api
        data = ''

        # add a event for testing
        user = self.data['user']
        device = self.data['device']
        ae = AppointmentEvents(name=user.name,
                               user_id=user.id,
                               start=datetime.datetime.utcnow(),
                               end=datetime.datetime.utcnow() + datetime.timedelta(seconds=7200)
                               )
        # add a user with no auth to device
        user_no_auth = User(name="test_no_auth_2", email="tt@tt.com", role_id=2)
        db.session.add(ae)
        db.session.add(user_no_auth)
        db.session.commit()

        # without token or without device_id
        response = self.client.post(
            url_for('api.remove_data', token='a', device_id=device.id),
            data=data
        )
        self.assertTrue(response.status_code == 401)

        response = self.client.post(
            url_for('api.remove_data', token=user.avatar_hash, device_id=''),
            data=data
        )
        self.assertTrue(response.status_code == 404)

        # device_id not exist
        response = self.client.post(
            url_for('api.remove_data', token=user.avatar_hash, device_id=100),
            data=data
        )
        self.assertTrue(response.status_code == 404)

        # user with no auth to device
        response = self.client.post(
            url_for('api.remove_data', token=user_no_auth.avatar_hash, device_id=device.id),
            data=data
        )
        self.assertTrue(response.status_code == 401)

        # user with auth
        response = self.client.post(
            url_for('api.remove_data', token=user.avatar_hash, device_id=device.id),
            data=data
        )
        self.assertTrue(response.status_code == 200)
