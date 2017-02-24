import os

from flask import render_template, make_response, \
    abort, jsonify
from flask.ext.login import current_user, login_required

from app.myschedules import myschedules
from app.models import Organization, Location, RoleToUser, Role


@myschedules.route(
    "/organizations/<int:org_id>/locations/<int:location_id>/roles/<int:role_id>/users/<int:user_id>",
    methods=["GET"])
@login_required
def myschedules_app(org_id, location_id, role_id, user_id):

    # verify route exists
    user = RoleToUser.query.join(Role).join(Location).join(
        Organization).filter(RoleToUser.user_id == user_id, Role.id == role_id,
                             Location.id == location_id,
                             Organization.id == org_id).first()

    RoleToUser.query.filter_by(
        role_id=role_id, user_id=user_id, archived=False).first_or_404()

    if user is None:
        abort(404)

    # check if sudo or logged in as user
    if not (current_user.is_sudo() or current_user.id == user_id):
        return abort(403)

    current_user.track_event("visited_myschedules")
    current_user.ping(org_id=org_id)
    resp = make_response(
        render_template(
            "myschedules.html",
            api_token=current_user.generate_api_token(),
            org_id=org_id,
            location_id=location_id,
            role_id=role_id,
            user_id=user_id))
    resp.headers["Cache-Control"] = "no-store"
    return resp


@myschedules.route("/templates.json", methods=["GET"])
@login_required
def ich_templates():
    """ JSON used by icanhaz.js """
    # TODO - this currently hits disk on every load. Memory does not
    # perisist between docker container reloads, so perhaps we can
    # cache this in memory with http://pythonhosted.org/Flask-Cache/

    # add html specific to this blueprint
    template_folder = "%s/%s/static/mustache-templates/" % (
        os.path.dirname(os.path.abspath(__file__)),
        myschedules.template_folder)

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
