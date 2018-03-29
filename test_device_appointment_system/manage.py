#!/usr/bin/env python
import os
from app import create_app, db, scheduler
from app.models import User, Device, Role, AppointmentEvents, DeviceUsageLog, GloveBoxLog, JobLog
from flask_script import Manager, Shell
from flask_migrate import Migrate, MigrateCommand
from datetime import datetime
from math import floor
from sqlalchemy import desc
from apscheduler import events


app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)


def check_log():
    with db.app.app_context():
        devices = Device.query.all()
        ids = []
        for device in devices:
            if device.device_inuse is True:
                ids.append(device.id)
        #  print(ids)
        for i in ids:
            d = DeviceUsageLog.query.filter_by(device_id=i).order_by(desc(DeviceUsageLog.id)).first()
            g = GloveBoxLog.query.filter_by(device_id=i).order_by(desc(GloveBoxLog.id)).first()
            l = g if d is None else d
            if l is not None:
                t = datetime.utcnow()
                dt = t - l.start_time
                if floor(dt.seconds / 3600) >= 8 or dt.days >= 1:
                    device = Device.query.filter_by(id=i).first()
                    device.device_inuse = False
                    l.end_time = t
                    l.remarks = 'Not logout'
                    try:
                        db.session.commit()
                    except:
                        db.session.rollback()
                        db.session.flush()


def job_listener(event):
    if event.exception:
        joblog = JobLog(job_name=event.job_id, excute_status=False, result=event.exception)
    else:
        joblog = JobLog(job_name=event.job_id)
    try:
        db.session.add(joblog)
        db.session.commit()
    except:
        db.session.rollback()
        db.session.flush()


def make_shell_context():
    return dict(app=app, db=db, User=User, Device=Device, AppointmentEvents=AppointmentEvents)


manager.add_command("shell", Shell(make_context=make_shell_context))
manager.add_command('db', MigrateCommand)


@manager.command
def test():
    """Run the unit tests."""
    import unittest
    tests = unittest.TestLoader().discover('tests')
    unittest.TextTestRunner(verbosity=2).run(tests)


if __name__ == '__main__':
    scheduler.add_job(func=check_log, id='check_log', trigger='interval', minutes=1)
    scheduler.add_listener(job_listener, events.EVENT_JOB_EXECUTED | events.EVENT_JOB_MISSED | events.EVENT_JOB_ERROR)
    manager.run()
