import os
import sys

from flask.ext.script import Manager, Server, Shell
from flask.ext.migrate import Migrate, MigrateCommand, upgrade

from app import create_app, db, cache, create_celery_app
from app.caches import SessionCache
from app.models import *

import unittest

app = create_app(os.environ.get("ENV", "prod"))
celery = create_celery_app(app)
manager = Manager(app)
migrate = Migrate(app, db)

manager.add_command("db", MigrateCommand)
manager.add_command("runserver", Server(host="0.0.0.0", port=80))
manager.add_command("runtestserver", Server(host="127.0.0.1", port=8080))

# Set flask-restful to be utf-8
reload(sys)
sys.setdefaultencoding("utf-8")

@app.teardown_appcontext
def shutdown_session(exception=None):
    if app.config["SQLALCHEMY_COMMIT_ON_TEARDOWN"]:
        db.session.commit()
    db.session.remove()


def make_shell_context():
    return dict(app=app,
                db=db,
                User=User,
                Organization=Organization,
                Location=Location,
                Role=Role,
                Schedule2=Schedule2,
                Shift2=Shift2,
                RecurringShift=RecurringShift,
                RoleToUser=RoleToUser,
                Preference=Preference,
                cache=cache,
                SessionCache=SessionCache,
                Timeclock=Timeclock,
                TimeOffRequest=TimeOffRequest,
                ApiKey=ApiKey)


manager.add_command("shell", Shell(make_context=make_shell_context))


@manager.command
def test():
    """Run the unit tests."""

    tests = unittest.TestLoader().discover('tests/unit')
    unittest.TextTestRunner(verbosity=2).run(tests)


@manager.command
def deploy():
    """Run deployment tasks."""

    # migrate database to latest revision
    upgrade()


if __name__ == '__main__':
    manager.run()
