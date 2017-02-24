import os

from flask import Flask, make_response
from flask import render_template, request
from flask_limiter import Limiter
from flask.ext.assets import Environment
from flask.ext.bootstrap import Bootstrap
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.login import LoginManager
from flask.ext.redis import Redis
from celery import Celery
import phonenumbers

from config import config  # pylint: disable=relative-import
import loader  # pylint: disable=relative-import
import stylesheets  # pylint: disable=relative-import
# yapf: disable
from helpers import date_duration, sorted_sessions  # pylint: disable=relative-import
# yapf: enable

bootstrap = Bootstrap()
assets = Environment()
db = SQLAlchemy()

login_manager = LoginManager()
login_manager.session_protection = "basic"
login_manager.login_view = "auth.login"
limiter = Limiter(
    global_limits=["300 per minute"],
    key_func=lambda: request.headers.get("CF-Connecting-IP", request.remote_addr),
)

cache = Redis()

# Asset Packages
js_default_req = loader.default()
js_vendor_single_page_req = loader.vendor_single_page()
js_shared_single_page_req = loader.shared_single_page()
js_euler_app_req = loader.euler_app()
js_manager_app_req = loader.manager_app()
js_myschedules_app_req = loader.myschedules_app()
css_default = stylesheets.css_default()
css_blog = stylesheets.css_blog()


def create_celery_app(app=None):
    """Return a celery app in app context"""
    app = app or create_app(
        os.environ.get("ENV", "prod"), register_blueprints=False)
    celery = Celery(
        app.import_name,
        backend=app.config['CELERY_RESULT_BACKEND'],
        broker=app.config['CELERY_BROKER_URL'])

    celery.conf.update(app.config)
    TaskBase = celery.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery.Task = ContextTask
    return celery


def create_app(config_name, register_blueprints=True):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    bootstrap.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)

    # Redis
    cache.init_app(app)

    # Rate Limit
    limiter.init_app(app)

    # Logging
    app.logger.setLevel(app.config.get("LOG_LEVEL"))

    # if not in debug mode, configure papertrail
    if not app.debug:
        # mostly copied from papertrail config
        import logging
        from logging.handlers import SysLogHandler

        class ContextFilter(logging.Filter):
            hostname = "staffjoy-app-%s" % app.config.get("ENV")

            def filter(self, record):
                record.hostname = ContextFilter.hostname
                return True

        f = ContextFilter()
        app.logger.addFilter(f)

        papertrail_tuple = app.config.get("PAPERTRAIL").split(":")

        syslog = SysLogHandler(
            address=(papertrail_tuple[0], int(papertrail_tuple[1])))

        formatter = logging.Formatter(
            '%(asctime)s %(hostname)s staffjoy-app %(levelname)s %(message)s',
            datefmt='%Y-%m-%dT%H:%M:%S')

        syslog.setFormatter(formatter)
        syslog.setLevel(logging.INFO)
        app.logger.addHandler(syslog)

    assets.register("js_default_req", js_default_req)
    assets.register("js_vendor_single_page_req", js_vendor_single_page_req)
    assets.register("js_shared_single_page_req", js_shared_single_page_req)
    assets.register("js_euler_app_req", js_euler_app_req)
    assets.register("js_manager_app_req", js_manager_app_req)
    assets.register("js_myschedules_app_req", js_myschedules_app_req)

    assets.register("css_default", css_default)
    assets.register("css_blog", css_blog)

    assets.init_app(app)

    # Build each asset so, in distributed environment, each one can have cache
    with app.app_context():
        js_default_req.build()
        js_vendor_single_page_req.build()
        js_shared_single_page_req.build()
        js_euler_app_req.build()
        js_manager_app_req.build()
        js_myschedules_app_req.build()
        css_blog.build()
        css_default.build()

    # Doing this prevents circular celery imports
    # http://shulhi.com/celery-integration-with-flask/
    if register_blueprints:
        from .main import main as main_blueprint
        app.register_blueprint(main_blueprint)

        from .auth import auth as auth_blueprint
        app.register_blueprint(auth_blueprint, url_prefix="/auth")

        from .euler import euler as euler_blueprint
        app.register_blueprint(euler_blueprint, url_prefix="/euler")

        from .manager import manager as manager_blueprint
        app.register_blueprint(manager_blueprint, url_prefix="/manager")

        from .myschedules import myschedules as myschedules_blueprint
        app.register_blueprint(
            myschedules_blueprint, url_prefix="/myschedules")

        from .apiv2 import apiv2 as apiv2_blueprint
        app.register_blueprint(apiv2_blueprint, url_prefix="/api/v2")

        from .ivr import ivr as ivr_blueprint
        app.register_blueprint(ivr_blueprint, url_prefix="/api/ivr")

    @app.errorhandler(401)
    def unauthorized(e):  # pylint: disable=unused-variable
        return render_template("401.html"), 401

    @app.errorhandler(403)
    def forbidden(e):  # pylint: disable=unused-variable
        return render_template("403.html"), 403

    @app.errorhandler(404)
    def page_not_found(e):  # pylint: disable=unused-variable
        resp = make_response(render_template("404.html"))

        no_cache_path = "/static/compiled"
        if len(request.path) > len(
                no_cache_path) and no_cache_path == request.path[:len(
                    no_cache_path)]:
            # Cloudflare caches 404 pages for 3 min, which is bad for stylesheets
            # - so tell them not to do this!
            resp.headers["Cache-Control"] = "no-cache"

        return resp, 404

    @app.errorhandler(429)
    def rate_limited(e):  # pylint: disable=unused-variable
        return render_template("429.html"), 429

    @app.errorhandler(500)
    def internal_server_error(e):  # pylint: disable=unused-variable
        return render_template("500.html"), 500

    @app.context_processor
    def jinja_functions():  # pylint: disable=unused-variable
        from .caches import IncidentCache
        active_incident = IncidentCache.get("") == True
        return dict(active_incident=active_incident)

    return app
