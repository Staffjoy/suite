from datetime import datetime, timedelta
import json

from flask import render_template, make_response, current_app, \
    flash, url_for, redirect, jsonify, Response
from flask.ext.login import current_user, login_required

from app.main import main
from app.models import User
from app.helpers import is_native


@main.route("/", methods=["GET"])
def index():
    """Return a friendly HTTP greeting."""

    if current_user.is_authenticated:
        # If authenticated - push into app, not homepage
        if current_user.is_sudo():
            # Staffjoy user. Go to Euler.
            return redirect(url_for("euler.index"))

        admins = current_user.admin_of.all()
        if len(admins) > 0:
            # Go to manage app
            return redirect(
                url_for("manager.manager_app", org_id=admins[0].id))

        memberships = current_user.memberships()
        if len(memberships) > 0:
            # Go to planner
            m = memberships[0]
            return redirect(
                url_for(
                    "myschedules.myschedules_app",
                    org_id=m.get("organization_id"),
                    location_id=m.get("location_id"),
                    role_id=m.get("role_id"),
                    user_id=current_user.id))

        # Nothing left - default to portal
        return redirect(url_for("auth.portal"))

    if is_native():
        return redirect(url_for("auth.native_login"))

    return render_template("homepage.html")


@main.route("/sign-up/", methods=["GET"])
def sign_up():
    """ Lead capture page! """
    if current_user.is_authenticated:
        return redirect(url_for("auth.portal"))

    return redirect(url_for("auth.free_trial"))


@main.route("/bootstrap-demo/", methods=["GET"])
def strap_me():
    """Return a friendly HTTP greeting."""
    flash("This is a general flash")
    flash("This is an informative", "info")
    flash("This is an unhappy flash >.<", "danger")
    flash("but news can also be good :-)", "success")
    return render_template("bootstrap-demo.html")


@main.route("/sitemap.xml", methods=["GET"])
def sitemap():
    """Generate sitemap.xml. Makes a list of urls and date modified."""
    pages = []

    ten_days_ago = datetime.now() - timedelta(days=10)

    # static pages
    for rule in current_app.url_map.iter_rules():
        # TODO - can we filter by blueprint?
        # Right now the argumetn call seems to be fine.
        if "GET" in rule.methods \
                and len(rule.arguments) == 0 \
                and rule.endpoint not in ["main.robots", "main.sitemap", "main.strap_me"] \
                and (
                    rule.endpoint[0:5] == "main."
                    or rule.endpoint == "auth.login"
                ):
            pages.append([rule.rule, ten_days_ago.date().isoformat()])

    sitemap_xml = render_template("main/sitemap.xml", pages=pages)
    response = make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"
    return response


@main.route("/health", methods=["GET"])
def health_check():
    # Run through some basic checks. If any throw an exception, then endpoint will return "unhealthy"
    # Note that unhealthy instances will be terminated
    try:
        # count number of users to ensure that the database is online
        User.query.count()
    except Exception as e:
        current_app.logger.warning("app unhealthy - %s", e)
        return "unhealthy", 500, {'Content-Type': 'text/css; charset=utf-8'}

    return "healthy", 200, {'Content-Type': 'text/css; charset=utf-8'}


@main.route("/robots.txt", methods=["GET"])
def robots():
    template = render_template(current_app.config.get("ROBOTS_TEMPLATE"))
    response = make_response(template)
    response.headers["Content-type"] = "text/plain"
    return response, 200


@main.route("/brand-assets/", methods=["GET"])
def brand_assets():
    return render_template("brand-assets.html")


@login_required
@main.route("/onboarding/employee", methods=["GET"])
def employee_onboarding():
    youtube_video_id = "8Ug3ktbspok"
    return render_template(
        "worker-onboarding-video.html", youtube_video_id=youtube_video_id)


@login_required
@main.route("/onboarding/contractor", methods=["GET"])
def contractor_onboarding():
    youtube_video_id = "7T6AtmxNGcM"
    return render_template(
        "worker-onboarding-video.html", youtube_video_id=youtube_video_id)


@main.route("/mobile-config.json")
def mobile_config():
    """Used by iPhone and Android apps to determine what urls are "native" """
    # Be careful that double escapes work correctly in regex
    payload = json.dumps({
        "hideNavForURLsMatchingPattern":
        '^https?://(suite|dev|stage|www)\\.staffjoy\\.com',
    })
    return Response(response=payload, mimetype="application/json")


@main.route(
    "/api/v1/",
    defaults={"path": ""},
    methods=["GET", "POST", "DELETE", "PATCH"])
@main.route("/api/v1/<path:path>", methods=["GET", "POST", "DELETE", "PATCH"])
def apiv1_deprecate(path):
    return jsonify({
        "message":
        "Version 1 of the Staffjoy API has been deprecated." +
        " Details at help.staffjoy.com"
    }), 410


@main.route("/manage/", defaults={"path": ""})
@main.route("/manage/<path:path>")
def manage_deprecate(path):
    return redirect("/manager/%s" % path)


@main.route("/planner/", defaults={"path": ""})
@main.route("/planner/<path:path>")
def planner_deprecate(path):
    return redirect("/myschedules/%s" % path)
