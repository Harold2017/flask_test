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
from app.email import send_email

app = create_app(os.getenv('FLASK_CONFIG') or 'default')
manager = Manager(app)
migrate = Migrate(app, db)

EMAIL_RECEIVER = 'jimmywlhon@nami.org.hk'


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
                if floor(dt.seconds / 3600) >= 10 or dt.days >= 1:
                    device = Device.query.filter_by(id=i).first()
                    device.device_inuse = False
                    l.end_time = t
                    l.remarks = 'Not logout'
                    try:
                        db.session.commit()
                    except:
                        db.session.rollback()
                        db.session.flush()
                    try:
                        send_email(EMAIL_RECEIVER, 'Not Logout',
                                   'log/email/not_logout',
                                   user_name=l.user_name,
                                   device_name=device.name)
                    except Exception as e:
                        print(str(e))


def check_device_state():
    with db.app.app_context():
        devices = Device.query.all()
        for device in devices:
            if device.state_transfer is True:
                try:
                    send_email(EMAIL_RECEIVER, 'Device Status Changed',
                               'log/email/status_change',
                               device_name=device.name,
                               device_status=device.status)
                    device.state_transfer = False
                    db.session.commit()
                except Exception as e:
                    print(str(e))
                    db.session.rollback()
                    db.session.flush()


def send_alert_email():
    try:
        send_email(EMAIL_RECEIVER, 'Glovebox Regeneration',
                   'log/email/glovebox_regeneration')
    except Exception as e:
        print(str(e))


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


@manager.command
def profile(length=25, profile_dir=None):
    """
    Start the application under the code profiler.
    :param length: number of displaying functions in report
    :param profile_dir: folder to save requests' analysis data
    :return: None
    """
    from werkzeug.contrib.profiler import ProfilerMiddleware
    app.wsgi_app = ProfilerMiddleware(app.wsgi_app, restrictions=[length],
                                      profile_dir=profile_dir)
    app.run()


@manager.command
def deploy():
    """Run deployment tasks."""
    from flask_migrate import upgrade
    from app.models import Role

    # upgrade database to newest version
    upgrade()

    # insert roles into db
    Role.insert_roles()


scheduler.add_job(func=check_log, id='check_log', trigger='interval', hours=1)

scheduler.add_job(func=check_device_state, id='check_device_state', trigger='interval', hours=1)

scheduler.add_job(func=send_alert_email, id='send_alert_email', trigger='cron', day=28)

scheduler.add_listener(job_listener, events.EVENT_JOB_EXECUTED | events.EVENT_JOB_MISSED | events.EVENT_JOB_ERROR)

if __name__ == '__main__':
    manager.run()
