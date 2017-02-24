import os

from flask import render_template, make_response, abort, jsonify
from flask.ext.login import current_user, login_required

from app.euler import euler


@euler.before_request
@login_required
def before_request():
    if not current_user.is_sudo():
        abort(403)


@euler.route("/", methods=["GET"])
def index():
    resp = make_response(
        render_template(
            "euler.html", api_token=current_user.generate_api_token()))
    resp.headers["Cache-Control"] = "no-store"
    return resp


@euler.route("/templates.json", methods=["GET"])
def ich_templates():
    """ JSON used by icanhaz.js """
    # TODO - this currently hits disk on every load. Memory does not
    # perisist between docker container reloads, so perhaps we can
    # cache this in memory with http://pythonhosted.org/Flask-Cache/
    template_folder = "%s/%s/static/mustache-templates/" % (
        os.path.dirname(os.path.abspath(__file__)), euler.template_folder)

    output = {}
    for filename in os.listdir(template_folder):
        name = os.path.splitext(filename)[0]
        f = file(template_folder + filename)
        template = f.read()

        output[name] = template

    return jsonify(output)
