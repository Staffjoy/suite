from flask import render_template, flash, make_response, \
    redirect, url_for, request, jsonify, current_app
from flask.ext.login import login_user, logout_user, login_required, \
    current_user
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from sqlalchemy import desc

from datetime import datetime, timedelta
from app.auth import auth
from app.auth.free_trial import provision
from app import db, limiter
from app.auth.forms import SignUpForm, LoginForm, RequestPasswordResetForm, \
        PasswordResetForm, ChangePasswordForm, ChangeEmailForm, ChangeNameForm, \
        ChangeUsernameForm, ActivateForm, ApiKeyForm, FreeTrialForm, SessionsForm, \
        NativeLoginForm, ChangeNotificationsForm, NewPhoneNumberForm, \
        VerifyPhoneNumberForm, RemovePhoneNumberForm
from app.models import User, ApiKey, Organization

from app.email import send_email
from app.plans import plans
from app.helpers import is_native
from app.constants import PHONE_COUNTRY_CODE_TO_COUNTRY

# Used for controlling notifications on user account
# Register a notification on user model and the ChangeNotificationsForm
# to let users change it.
NOTIFICATION_ATTRS = [
    "enable_notification_emails", "enable_timeclock_notification_sms"
]


@auth.before_app_request
def before_request():
    if current_user.is_authenticated:
        current_user.ping()  # last_seen
        if not (current_user.confirmed and current_user.active) \
                and request.endpoint not in ["auth.unconfirmed",
                    "auth.resend_confirmation", "auth.logout", "auth.confirm"] \
                and request.endpoint != "static":
            return redirect(url_for("auth.unconfirmed"))


@auth.route("/unconfirmed")
def unconfirmed():
    if current_user.is_anonymous or current_user.confirmed:
        return redirect(url_for("main.index"))
    return render_template("unconfirmed.html")


@auth.route("/sign-up", methods=["GET", "POST"])
@limiter.limit("30/minute")
def sign_up():
    """sign up for the Staffjoy application"""
    if is_native():
        return redirect(url_for("auth.native_login"))

    if not current_app.config.get("ALLOW_COMPANY_SIGNUPS"):
        return redirect(url_for("main.index"))

    form = SignUpForm()
    if form.validate_on_submit():
        user = User(
            email=form.email.data.lower().strip(),
            username=form.username.data.lower().strip(),
            password=form.password.data,
            name=form.name.data.strip())

        try:
            db.session.add(user)
            db.session.commit()
        except:
            db.session.rollback()
            raise Exception("Dirty session")

        user.flush_associated_shift_caches()
        token = user.generate_confirmation_token()
        user.send_email("Confirm Your Account",
                        render_template(
                            "email/confirm-account.html",
                            user=user,
                            token=token), True)

        flash("A confirmation email has been sent to you by email.", "success")
        return redirect(url_for("auth.login"))
    return render_template("auth.html", form_title="Sign Up", form=form)


@auth.route("/confirm/<token>")
def confirm(token):
    s = Serializer(current_app.config["SECRET_KEY"])
    try:
        data = s.loads(token)
    except:
        flash("The confirmation link is invalid or has expired.", "danger")
        return redirect(url_for("auth.unconfirmed"))

    u = User.query.get(data.get("confirm"))
    if u is None:
        flash("The confirmation link is invalid or has expired.", "danger")
        return redirect(url_for("auth.unconfirmed"))

    if not u.confirm(token):
        flash("The confirmation link is invalid or has expired.", "danger")
        return redirect(url_for("auth.unconfirmed"))

    # Confirmation complete!
    # Login:
    login_user(u)

    # Tell them they are good:
    flash("You have confirmed your account!", "success")

    return redirect(url_for("main.index"))


@auth.route("/confirm")
@login_required
def resend_confirmation():
    if not current_user.confirmed:
        token = current_user.generate_confirmation_token()
        current_user.send_email("Confirm Your Account",
                                render_template(
                                    "email/confirm-account.html",
                                    user=current_user,
                                    token=token), True)

        flash("A new confirmation email has been sent to you by email.",
              "success")
    return redirect(url_for("auth.portal"))


@auth.route("/login", methods=["GET", "POST"])
@limiter.limit("30/minute")
def login():
    """login page for the Staffjoy application"""
    if is_native():
        return redirect(url_for("auth.native_login", **request.args))

    if current_user.is_authenticated:
        return redirect(url_for("auth.portal"))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(
            email=form.email.data.lower().strip()).first()
        if user is None:
            # Otherwise - see if they entered a username. Not labeled, but support it.
            user = User.query.filter_by(
                username=form.email.data.lower().strip()).first()

        if user is not None and user.active and user.verify_password(
                form.password.data.strip()):
            login_user(user, form.remember_me.data)

            # Intelligently try to put users in the correct app upon login
            if request.args.get("next"):
                # User is following a link to the correct destination
                return redirect(request.args.get("next"))
            return redirect(url_for("main.index"))  # This will smart route

        flash("Invalid email or password", "danger")

    # Disable native cookie
    return make_response(render_template("login.html", form=form))


@auth.route("/native", methods=["GET", "POST"])
@limiter.limit("30/minute")
def native_login():
    """login page for the Staffjoy application on native"""
    REMEMBER_ME = True  # Always remember native users
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = NativeLoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(
            email=form.email.data.lower().strip()).first()
        if user is None:
            # Otherwise - see if they entered a username. Not labeled, but support it.
            user = User.query.filter_by(
                username=form.email.data.lower().strip()).first()

        if user is not None and user.active and user.verify_password(
                form.password.data.strip()):
            login_user(user, REMEMBER_ME)
            user.track_event("native_login")
            current_app.logger.info("Native login %s (id %s)" %
                                    (user.email, user.id))

            # Intelligently try to put users in the correct app upon login
            if request.args.get("next"):
                # User is following a link to the correct destination
                return redirect(request.args.get("next"))
            return redirect(url_for("main.index"))  # This will smart route

        flash("Invalid email or password", "danger")

    # Set a native cookie
    resp = make_response(render_template("nativelogin.html", form=form))
    resp.set_cookie(
        current_app.config.get("NATIVE_COOKIE_NAME"),
        "1",
        expires=(datetime.utcnow() + timedelta(
            days=current_app.config.get("NATIVE_COOKIE_LIFE_DAYS"))))
    return resp


@auth.route("/destroy-native", methods=["GET"])
def destroy_native():
    """Remove the native cookie. Used for testing."""
    resp = make_response(redirect(url_for("auth.login")))
    resp.set_cookie(
        current_app.config.get("NATIVE_COOKIE_NAME"), "", expires=0)
    return resp


@auth.route("/portal", methods=["GET"])
@login_required
def portal():
    keys = ApiKey.query.filter_by(user_id=current_user.id).count()

    # Data for showing whether notifications fully / partially / not enabled
    total_notifications = len(NOTIFICATION_ATTRS)
    enabled_notifications_count = 0
    for attr in NOTIFICATION_ATTRS:
        if getattr(current_user, attr):
            enabled_notifications_count += 1

    return render_template(
        "portal.html",
        api_keys=keys,
        enabled_notifications_count=enabled_notifications_count,
        total_notifications=total_notifications)


@auth.route("/logout")
@login_required
def logout():
    current_user.logout_session()
    logout_user()
    flash("You have been logged out", "success")
    return redirect(url_for("main.index"))


@auth.route("/reset", methods=["GET", "POST"])
@limiter.limit("20/minute")
def password_reset_request():
    """ Request a password reset """
    if not current_user.is_anonymous:
        return redirect(url_for("auth.portal"))
    form = RequestPasswordResetForm()

    if form.validate_on_submit():
        user = User.query.filter_by(
            email=form.email.data.lower().strip()).first()
        if user:
            # Check if account is active
            if not user.active:
                # Need to activate account
                User.send_activation_email(user)
            else:
                token = user.generate_reset_token()
                user.send_email("Reset Your Password",
                                render_template(
                                    "email/reset-password.html",
                                    user=user,
                                    token=token), True)
        # Never let the user know whether the account exists
        flash("An email with instructions on resetting your password has been "
              "sent to you", "success")
        return redirect(url_for("auth.login"))

    return render_template(
        "auth.html", form_title="Reset Your Password", form=form)


@auth.route("/reset/<token>", methods=["GET", "POST"])
def password_reset(token):
    if not current_user.is_anonymous:
        return redirect(url_for("auth.portal"))
    form = PasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(
            email=form.email.data.lower().strip()).first()
        if user is None:
            return redirect(url_for("main.index"))
        if user.reset_password(token, form.password.data):

            flash("Your password has been updated", "success")
            return redirect(url_for("auth.login"))
        else:
            flash(
                "We were unable to update your password. Please try again or contact support.",
                "danger")
            return redirect(url_for("main.index"))
    return render_template(
        "auth.html", form_title="Reset Your Password", form=form)


@auth.route("/change-password", methods=["GET", "POST"])
@login_required
def change_password():
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.old_password.data.strip()):
            current_user.password = form.password.data.strip()

            flash(
                "Your password has been updated. Please sign in with your new password.",
                "success")
            return redirect(url_for("auth.login"))
        else:
            flash("Current password was incorrect", "danger")
    return render_template(
        "auth.html", form_title="Change Your Password", form=form)


@auth.route("/change-name", methods=["GET", "POST"])
@login_required
def change_name():
    form = ChangeNameForm()

    if form.validate_on_submit():
        if current_user.name != form.name.data.strip():
            current_user.name = form.name.data.strip()
            db.session.add(current_user)
            current_user.flush_associated_shift_caches()
            flash("Your name has been updated", "success")
        return redirect(url_for("auth.portal"))

    form.name.data = current_user.name
    return render_template(
        "auth.html", form_title="Change Your Name", form=form)


@auth.route("/change-username", methods=["GET", "POST"])
@login_required
def change_username():
    form = ChangeUsernameForm(current_user)

    if form.validate_on_submit():
        if current_user.username != form.username.data.lower().strip():
            current_user.username = form.username.data.lower().strip()
            db.session.add(current_user)
            flash("Your username has been updated", "success")
        return redirect(url_for("auth.portal"))

    form.username.data = current_user.username
    return render_template(
        "auth.html", form_title="Change Your Username", form=form)


@auth.route("/change-email", methods=["GET", "POST"])
@login_required
def change_email_request():
    form = ChangeEmailForm(current_user)

    if form.validate_on_submit():
        if form.email.data.lower().strip() != current_user.email:
            new_email = form.email.data.lower().strip()
            token = current_user.generate_email_change_token(new_email)
            send_email(new_email, "Confirm Your Email Address",
                       render_template(
                           "email/confirm-change-email.html",
                           user=current_user,
                           token=token))

            flash(
                "To finish updating your email address, please click the link "
                "that we just sent to your new address")
        return redirect(url_for("auth.portal"))

    form.email.data = current_user.email
    return render_template(
        "auth.html", form_title="Change Your Email", form=form)


@auth.route("/change-email/<token>")
@login_required
def change_email(token):
    if current_user.change_email(token):
        flash("Your email address has been updated", "success")
    else:
        flash("Invalid request", "danger")
    return redirect(url_for("auth.portal"))


@auth.route("/api-token")
@login_required
def api_token():
    return jsonify(api_token=current_user.generate_api_token())


@auth.route("/activate/<token>", methods=["GET", "POST"])
def activate_account(token):
    """ Finish creating an account after activation """
    # No logged-in users
    if not current_user.is_anonymous:
        return redirect(url_for("auth.portal"))

    # Identify the user
    user_id = User.get_id_from_activate_token(token)

    # Not found?
    if user_id is False:
        flash(
            "Your activation link has expired. Please use the password reset link to get a new link."
        )
        return redirect(url_for("auth.password_reset_request"))

    # Pull up user
    user = User.query.get_or_404(user_id)
    if user.active:
        flash("Your account has already been activated", "success")
        return redirect(url_for("auth.login"))

    form = ActivateForm()
    if form.validate_on_submit():
        if user.activate_account(token, form.name.data, form.password.data,
                                 form.username.data):
            login_user(user)
            flash("Your account has been activated", "success")

            # Check if planner access, and if so redirect to onboarding videos
            adminships = user.admin_of.all()
            memberships = user.memberships()
            if len(memberships) > 0 and len(adminships) == 0:
                m = memberships[0]
                # Onboarding video! Which one?
                if Organization.query.get(
                        m.get("organization_id")).plan == "flex-v1":
                    return redirect(url_for("main.contractor_onboarding"))
                else:
                    return redirect(url_for("main.employee_onboarding"))

            # Generic router
            return redirect(url_for("main.index"))

        else:
            flash(
                "We were unable to activate your account. Please contact support.",
                "danger")
            return redirect(url_for("main.index"))

    # Otherwise show activation form
    form.name.data = user.name
    form.username.data = user.username  # in case it gets set elsewehre
    return render_template(
        "auth.html", form_title="Activate Your Account", form=form)


@auth.route("/api-key", methods=["GET", "POST"])
@login_required
def api_key():
    """ View and manage API keys. Use forms for CSRF. """

    plaintext_key = None
    key_label = None

    form = ApiKeyForm()
    if form.validate_on_submit():
        key_label = form.data.get("name")
        plaintext_key = ApiKey.generate_key(current_user.id, key_label)
        flash("API Key generated", "success")

    return render_template(
        "api_key.html",
        form_title="Issue a New API Key",
        form=form,
        key_label=key_label,
        plaintext_key=plaintext_key)


@auth.route("/api-keys", methods=["GET", "POST"])
@login_required
def api_keys():
    """ View and manage all api keys"""
    keys = ApiKey.query.filter_by(
        user_id=current_user.id).order_by(desc(ApiKey.last_used)).all()
    return render_template(
        "api_keys.html",
        api_keys=keys,
        api_token=current_user.generate_api_token())


@auth.route("/sessions", methods=["GET", "POST"])
@login_required
def sessions():
    """ View and manage all sessions"""
    form = SessionsForm()
    if form.validate_on_submit():
        current_user.logout_all_sessions()
        flash("All active sessions have been deleted.", "success")
        return redirect(url_for("auth.login"))

    return render_template(
        "sessions.html",
        form=form,
        api_token=current_user.generate_api_token())


@auth.route("/free-trial", methods=["GET", "POST"])
@limiter.limit("20/minute")
def free_trial():
    """sign up for the Staffjoy application and a free trial"""
    if current_user.is_authenticated:
        return redirect(url_for("auth.portal"))

    form = FreeTrialForm()
    if form.validate_on_submit():
        provision(form)
        # TODO - have a dedicated sign up confirmation page
        # "What Happens Next"
        return render_template("confirm_free_trial.html", form=form)

    # Check if the plan was passed
    plan = request.args.get("plan")
    if plan is not None and plan in plans.keys() and plans[plan]["active"]:
        form.plan.data = plan

    form.plan.enterprise_access = request.args.get("enterprise_access")

    return render_template(
        "sign_up.html", form_title="Begin Your Trial", form=form)


@auth.route("/notifications", methods=["GET", "POST"])
@login_required
def notifications():
    """Modify the notifications that Staffjoy sends"""

    form = ChangeNotificationsForm()
    if form.validate_on_submit():
        for attr in NOTIFICATION_ATTRS:
            setattr(current_user, attr, getattr(form, attr).data)

        flash("Your notification preferences have been updated", "success")
        return redirect(url_for("auth.portal"))

    for attr in NOTIFICATION_ATTRS:
        form_obj = getattr(form, attr)
        form_obj.data = getattr(current_user, attr)
    return render_template(
        "auth.html", form_title="Your Account Notifications", form=form)


@auth.route("/phone-number", methods=["GET", "POST"])
@login_required
def phone_number_router():
    """View and modify the phone number"""
    if not current_user.phone_number:
        if current_user.get_phone_data_pending_verification():
            return redirect(url_for("auth.phone_number_verify"))
        else:
            return redirect(url_for("auth.phone_number_add"))
    return redirect(url_for("auth.phone_number_remove"))


@auth.route("/phone-number/new", methods=["GET", "POST"])
@login_required
@limiter.limit("20/minute")
def phone_number_add():
    """Add a new phone number"""
    # Make sure this is correct page
    if current_user.phone_number or current_user.get_phone_data_pending_verification(
    ):
        # Not this step - send to router
        return redirect(url_for("auth.phone_number_router"))

    # Populate form choices
    choices = []
    for country_code in current_app.config["TWILIO_NUMBER"].keys():
        country_name = PHONE_COUNTRY_CODE_TO_COUNTRY.get(country_code)
        description = "+%s" % country_code
        if country_name:
            description += " (%s)" % country_name
        # tuple of (key, description)
        choices.append((country_code, description))

    form = NewPhoneNumberForm(country_code_choices=choices)

    if form.validate_on_submit():
        try:
            current_user.set_phone_number(form.phone_country_code.data,
                                          form.phone_national_number.data)
            success = True
        except Exception as e:
            # Don't tell user why due to security reasons
            success = False
            current_app.logger.info(
                "User %s (%s) entered phone number invalid due to %s" %
                (current_user.id, current_user.email, e))

        if success:
            flash("A confirmation pin has been sent via SMS to you", "success")
            return redirect(url_for("auth.phone_number_verify"))

        # Otherwise - invalid?
        flash("We were unable to validate this phone number", "danger")

    return render_template(
        "auth.html",
        form_title="Add Your Phone Number",
        help_text="Add your phone number to Staffjoy for SMS reminders and improved account security. If your country is unavailable, please contact support.",
        form=form)


@auth.route("/phone-number/verify", methods=["GET", "POST"])
@login_required
@limiter.limit("20/minute")
def phone_number_verify():
    """Add a new phone number"""
    if current_user.phone_number or not current_user.get_phone_data_pending_verification(
    ):
        # Not this step - send to router
        return redirect(url_for("auth.phone_number_router"))

    form = VerifyPhoneNumberForm()
    if form.validate_on_submit():
        success = current_user.verify_phone_number(form.pin.data)
        if success:
            flash("Your phone number has been confirmed", "success")
            return redirect(url_for("auth.portal"))

        flash("This pin is invalid", "danger")

    return render_template(
        "auth.html",
        form_title="Confirm Your Phone Number",
        help_text="Please enter the verification pin that we sent via SMS to your phone number. If you are unable to verify your number, please <a href=\"%s\">remove it</a> and start again."
        % url_for("auth.phone_number_remove"),
        form=form)


@auth.route("/phone-number/remove", methods=["GET", "POST"])
@login_required
def phone_number_remove():
    """View and modify the phone number"""
    if not current_user.phone_number and not current_user.get_phone_data_pending_verification(
    ):
        # Not this step - send to router
        return redirect(url_for("auth.phone_number_router"))

    form = RemovePhoneNumberForm()
    if form.validate_on_submit():
        current_user.remove_phone_number()
        flash("Your phone number has been removed", "success")
        return redirect(url_for("auth.portal"))
    return render_template(
        "auth.html",
        form_title="Remove Your Phone Number",
        help_text="Removing your phone number will stop all SMS communication from Staffjoy. If you wish to modify which notifications you receive, please <a href=\"%s\">modify your notifications</a>."
        % url_for("auth.notifications"),
        panel_body_class="dangerous-buttons",
        form=form)
