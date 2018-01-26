import unittest
from app import create_app, db
from app.models import User, Device, Role


class DeviceModelTestCase(unittest.TestCase):
    def setUp(self):
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        Role.insert_roles()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_duplicate_name(self):
        d1 = Device(name='d1')
        d2 = Device(name='d2')
        db.session.add(d1)
        db.session.add(d2)
        db.session.commit()
        self.assertTrue(d2.name == 'd2')

    def test_coprimarykey(self):
        u1 = User(email='john@example.com', password='cat')
        u2 = User(email='susan@example.org', password='dog')
        db.session.add(u1)
        db.session.add(u2)
        d1 = Device(name='d1')
        d1.users.append(u1)
        d1.users.append(u2)
        db.session.add(d1)
        db.session.commit()
        self.assertTrue(d1.users[1].email == 'susan@example.org')
