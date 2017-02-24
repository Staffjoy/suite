import os

from flask import render_template, make_response, abort, jsonify
from flask.ext.login import current_user, login_required

from app.manager import manager
from app.models import Organization


@manager.route("/organizations/<int:org_id>", methods=["GET"])
@login_required
def manager_app(org_id):
    # Auth - are they sudo?
    organization = Organization.query.get_or_404(org_id)

    if current_user.is_sudo() or organization in current_user.manager_accounts(
    ):
        current_user.track_event("visited_manager")
        current_user.ping(org_id=org_id)
        resp = make_response(
            render_template(
                "manager.html",
                organization=organization,
                api_token=current_user.generate_api_token()))
        resp.headers["Cache-Control"] = "no-store"
        return resp

    return abort(403)


@manager.route("/templates.json", methods=["GET"])
@login_required
def ich_templates():
    """ JSON used by icanhaz.js """
    # TODO - this currently hits disk on every load. Memory does not
    # perisist between docker container reloads, so perhaps we can
    # cache this in memory with http://pythonhosted.org/Flask-Cache/

    # add html specific to this blueprint
    template_folder = "%s/%s/static/mustache-templates/" % (
        os.path.dirname(os.path.abspath(__file__)), manager.template_folder)

    output = {}
    for filename in os.listdir(template_folder):
        name = os.path.splitext(filename)[0]
        f = file(template_folder + filename)
        template = f.read()

        output[name] = template

    # now add html for shared views
    shared_folder = "%s/../static/html/shared/" % (
        os.path.dirname(os.path.abspath(__file__)))

    for filename in os.listdir(shared_folder):
        name = os.path.splitext(filename)[0]
        f = file(shared_folder + filename)
        template = f.read()

        output[name] = template

    return jsonify(output)
