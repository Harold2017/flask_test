import re
import unittest
from flask import url_for
from app import create_app, db
from app.models import User, Role


class ClientTestCase(unittest.TestCase):
    def setUp(self):
        """
        setup test environment
        :return: None
        """
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.client = self.app.test_client()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_index(self):
        response = self.client.get(url_for('main.index'))
        self.assertTrue(response.status_code == 200)

    def test_register_and_login(self):
        # register a new account
        response = self.client.post(url_for('auth.register'),
                                    data={
                                        'email': 'register_test@test.com',
                                        'username': 'test',
                                        'password': 'cat',
                                        'password2': 'cat'
                                    })
        self.assertTrue(response.status_code == 200)

        ''''# login with the new account
        rv = self.client.get(url_for('auth.login'))
        m = re.search(b'(<input id="csrf_token" name="csrf_token" type="hidden" value=")([-A-Za-z.0-9_]+)', rv.data)
        print(m.group(2))
        response = self.client.post(url_for('auth.login'),
                                    data={
                                        'email': 'register_test@test.com',
                                        'password': 'cat',
                                        'csrf_token': m.group(2).decode("utf-8")
                                    },
                                    follow_redirects=True
                                    )
        print(response.data)
        alert = re.search(b'(<div class="alert alert-warning">(.*?)</div>)', response.data)
        print(alert)
        self.assertTrue(re.search(b'Welcome', response.data))

        # log out
        response = self.client.get(url_for('auth.logout'),
                                   follow_redirects=True)
        self.assertTrue(re.search(b'See you friend!'), response.data)'''
