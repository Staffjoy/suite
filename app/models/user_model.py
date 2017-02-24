from datetime import datetime
import time
import json
import string
import random

import hmac
import phonenumbers
import unirest
import hashlib
from werkzeug.security import generate_password_hash, check_password_hash
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from sqlalchemy import select
from flask import current_app, render_template, copy_current_request_context, \
    request
from flask.ext.login import UserMixin

from app import db, login_manager
from app.constants import SECONDS_PER_HOUR, SECONDS_PER_DAY
from app.caches import Shifts2Cache, SessionCache, PhoneVerificationCache
from app.email import send_email
from app.limiters import UserActivationReminderLimiter, PingLimiter
from app.sms import send_sms

import organization_model  # pylint: disable=relative-import
import schedule2_model  # pylint: disable=relative-import
from app.models.location_model import Location
from app.models.role_model import Role
from app.models.role_to_user_model import RoleToUser


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(256), unique=True, index=True)
    username = db.Column(db.String(64), unique=True, index=True)
    confirmed = db.Column(db.Boolean, default="0")
    sudo = db.Column(db.Boolean, default=False, server_default="0")
    name = db.Column(db.String(256))
    password_hash = db.Column(db.String(128))
    member_since = db.Column(db.DateTime(), default=datetime.utcnow)
    # The "ping" function updates this
    last_seen = db.Column(db.DateTime(), default=datetime.utcnow)
    active = db.Column(
        db.Boolean, default=True, server_default="1")  # used for invitation

    roles = db.relationship("RoleToUser", backref=db.backref("user"))
    enable_notification_emails = db.Column(
        db.Boolean, nullable=False, default=True, server_default="1")
    enable_timeclock_notification_sms = db.Column(
        db.Boolean, nullable=False, default=True, server_default="1")
    phone_country_code = db.Column(db.String(3), index=True)
    phone_national_number = db.Column(db.String(15), index=True)

    SMS_VERIFICATION_PIN_LENGTH = 6

    def __init__(self, **kwargs):
        super(User, self).__init__(**kwargs)
        self.session_id = None

    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    def __eq__(self, other):
        """Checks equality of user objects. Necessary to override UserMixin one."""
        return self.id == other.id

    @property
    def first_name(self):
        """Guess first name for friendly notifications"""
        name_list = self.name.partition(" ")
        return name_list[0]

    @password.setter
    def password(self, password):
        """Store plaintext password securely on the model, and send alerts + flush sessions"""

        # See whether there was a password before
        existing_password = self.password_hash is None

        # Actually update the password
        self.password_hash = generate_password_hash(password)
        db.session.commit()

        if self.id is not None:  # This is used before user is committed
            current_app.logger.info(
                "Password for user id %s (%s) has been updated" %
                (self.id, self.email))

        # If password is changed, lot user out of other
        if not existing_password:
            # Email users for security purposes
            self.send_email(
                "[Alert] Your Password Has Changed",
                render_template(
                    "email/password-changed.html",
                    user=self, ),
                force_send=True)

            # Logout all sessions
            self.logout_all_sessions()

    def ping(self, org_id=None):
        """Update the last-seen time, and send tracking info to intercom"""
        if not PingLimiter.allowed_to_send(self):
            return

        if not self.active or not self.confirmed:
            current_app.logger.debug(
                "Did not send tracking for inactive user %s" % self.id)
            return

        PingLimiter.mark_sent(self)
        self.last_seen = datetime.utcnow()
        db.session.add(self)

        # Now update intercom
        if current_app.config.get("ENV") == "dev":
            return

        @copy_current_request_context
        def async_callback(resp):
            if resp.code != 200:
                current_app.logger.info("Failed intercom update - header %s" %
                                        (resp.code))

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Stuff we want to tack on, so decode then reencode
        data = {
            "user_id": str(self.id),
            "name": self.name,
            "custom_attributes": {
                "sudo": self.sudo,
                "username": self.username,
                "phone_number": self.pretty_phone_number,
            },
            "email": self.email,
            "created_at": int(self.member_since.strftime("%s")),
            "last_request_at": int(time.time()),
            "new_session": True,
            "companies": [],
        }

        if org_id is not None and not self.is_sudo():
            # Don't add users to any org
            org = organization_model.Organization.query.get(org_id)
            if org is not None:
                data["companies"].append(org.intercom_settings())

        unirest.post(
            "https://api.intercom.io/users",
            params=json.dumps(data),
            headers=headers,
            auth=(current_app.config.get("INTERCOM_ID"),
                  current_app.config.get("INTERCOM_API_KEY"), ),
            callback=async_callback, )
        return

    def track_event(self, event):
        """ Send events to intercom """

        if event is None:
            current_app.logger.warning("Null event")
            return

        if not self.active or not self.confirmed:
            current_app.logger.debug(
                "Did not track event %s for inactive user %s" %
                (event, self.id))

        if current_app.config.get("ENV") == "dev":
            current_app.logger.debug("Intercepted event for user %s - %s" %
                                     (self.id, event))
            return

        @copy_current_request_context
        def async_callback(resp):
            if resp.code != 202:
                current_app.logger.info("bad intercom event - header %s" %
                                        (resp.code))

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        # Stuff we want to tack on, so decode then reencode
        data = {
            "user_id": str(self.id),
            "email": self.email,
            "created_at": int(time.time()),
            "event_name": event,
        }

        unirest.post(
            "https://api.intercom.io/events",
            params=json.dumps(data),
            headers=headers,
            auth=(current_app.config.get("INTERCOM_ID"),
                  current_app.config.get("INTERCOM_API_KEY"), ),
            callback=async_callback, )
        return

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def generate_confirmation_token(self,
                                    expiration=SECONDS_PER_DAY,
                                    trial=False):
        s = Serializer(current_app.config["SECRET_KEY"], expiration)
        return s.dumps({"confirm": self.id, "trial": trial})

    def generate_reset_token(self, expiration=SECONDS_PER_HOUR):
        s = Serializer(current_app.config["SECRET_KEY"], expiration)
        return s.dumps({"reset": self.id})

    def generate_activation_token(self, expiration=SECONDS_PER_DAY):
        """ Used for account invitations """
        s = Serializer(current_app.config["SECRET_KEY"], expiration)
        return s.dumps({"activation": self.id})

    def reset_password(self, token, new_password):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get("reset") != self.id:
            return False
        self.password = new_password
        self.logout_all_sessions()
        db.session.add(self)
        self.track_event("reset_password")
        return True

    @staticmethod
    def get_id_from_activate_token(token):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token)
        except:
            return False
        user_id = data.get("activation")
        if user_id is None:
            return False
        return user_id

    def activate_account(self, token, name, password, username):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get("activation") != self.id:
            return False
        self.password = password
        self.name = name
        self.username = username
        self.confirmed = True
        self.active = True
        db.session.add(self)
        current_app.logger.info("User account activated: user id %s (%s)" %
                                (self.id, self.email))
        self.track_event("activated_account")
        return True

    def __repr__(self):
        return "<User %r - %s - id %r>" % (self.email, self.name, self.id)

    def confirm(self, token):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get("confirm") != self.id:
            return False

        self.confirmed = True
        self.active = True
        db.session.add(self)
        db.session.commit()
        current_app.logger.info("User account confirmed: user id %s (%s)" %
                                (self.id, self.email))
        self.track_event("confirmed_account")
        if data.get("trial") is True:
            self.track_event("started_free_trial")
        return True

    def generate_email_change_token(self,
                                    new_email,
                                    expiration=SECONDS_PER_HOUR):
        s = Serializer(current_app.config["SECRET_KEY"], expiration)
        return s.dumps({"change_email": self.id, "new_email": new_email})

    def change_email(self, token):
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token)
        except:
            return False
        if data.get("change_email") != self.id:
            return False
        new_email = data.get("new_email")
        if new_email is None:
            return False
        if self.query.filter_by(email=new_email).first() is not None:
            return False
        self.email = new_email
        try:
            db.session.add(self)
            db.session.commit()
        except:
            db.session.rollback()
            raise Exception("Dirty session")

        self.track_event("changed_email")
        return True

    def is_sudo(self):
        """checks if sudo"""
        return self.sudo is True

    def is_org_admin_or_location_manager(self, org_id, location_id):
        """checks if an admin or manager in the org/location"""
        return self.is_org_admin(org_id) or self.is_location_manager(
            location_id)

    def is_org_admin(self, org_id):
        """checks if an org admin"""

        admin = User.query \
            .join(User.admin_of) \
            .filter(
                organization_model.Organization.id == org_id,
                User.id == self.id
            ) \
            .first()

        return admin is not None

    def is_manager_in_org(self, org_id):
        """checks if current user manages a location in the org"""

        manager = User.query \
            .join(User.manager_of) \
            .filter(
                User.id == self.id,
                Location.organization_id == org_id
            ) \
            .first()

        return manager is not None

    def is_location_manager(self, location_id):
        """checks if current user managers location in kwargs"""

        manager = User.query \
            .join(User.manager_of) \
            .filter(
                User.id == self.id,
                Location.id == location_id
            ) \
            .first()

        return manager is not None

    def is_location_worker(self, location_id):
        """checks if the user is a worker of a role in the location"""

        assoc = User.query \
            .join(User.roles) \
            .join(Role) \
            .filter(
                RoleToUser.user_id == self.id,
                RoleToUser.archived == False,
                RoleToUser.role_id == Role.id,
                Role.location_id == location_id
            ) \
            .first()

        return assoc is not None

    def is_active(self):
        return self.active

    def manager_accounts(self):
        """
        returns a list of all organizations that the user has Manager access to
        """

        # start with org admins
        result = self.admin_of.all()

        # add in additional location admins, but avoid duplicates
        for location in self.manager_of.all():
            org = location.organization
            if org not in result:
                result.append(org)

        return result

    def memberships(self):
        """ Return org ids that this user is an active member of """

        memberships = db.session.execute(
            select([organization_model.Organization.id, organization_model.Organization.name, Location.id, Location.name, RoleToUser.role_id, Role.name]).\
            where(RoleToUser.user_id == self.id).\
            where(RoleToUser.archived == False).\
            where(RoleToUser.role_id == Role.id).\
            where(Role.location_id == Location.id).\
            where(Location.organization_id == organization_model.Organization.id).\
            select_from(RoleToUser).\
            select_from(Role).\
            select_from(Location).\
            select_from(organization_model.Organization)
        ).fetchall()

        result = []
        for entry in memberships:

            # order is defined in select statement
            result.append({
                "organization_id": entry[0],
                "organization_name": entry[1],
                "location_id": entry[2],
                "location_name": entry[3],
                "role_id": entry[4],
                "role_name": entry[5],
            })

        return result

    def membership_ids(self):
        memberships = db.session.execute(
            select([organization_model.Organization.id, Location.id, RoleToUser.role_id]).\
            where(RoleToUser.user_id == self.id).\
            where(RoleToUser.archived == False).\
            where(RoleToUser.role_id == Role.id).\
            where(Role.location_id == Location.id).\
            where(Location.organization_id == organization_model.Organization.id).\
            select_from(RoleToUser).\
            select_from(Role).\
            select_from(Location).\
            select_from(organization_model.Organization)
        ).fetchall()

        result = []
        for entry in memberships:

            # order is defined in select statement
            result.append({
                "organization_id": entry[0],
                "location_id": entry[1],
                "role_id": entry[2],
                "user_id": self.id,
            })

        return result

    def intercom_settings(self, org_id=None):
        """ Data for Intercom, json-encoded """

        data = {
            "user_id":
            str(self.id),
            "name":
            self.name,
            "sudo":
            self.sudo,
            "username":
            self.username,
            "email":
            self.email,
            "created_at":
            int(self.member_since.strftime("%s")),
            "app_id":
            current_app.config.get("INTERCOM_ID"),
            "user_hash":
            hmac.new(
                current_app.config.get("INTERCOM_SECRET"),
                str(self.id),
                hashlib.sha256, ).hexdigest(),
            "is_org_admin": (len(self.admin_of.all()) > 0),
            "is_location_manager": (len(self.manager_of.all()) > 0),
            "is_org_member": (len(self.memberships()) > 0),
        }

        if org_id is not None and not self.is_sudo():
            # Don't add users to any org
            org = organization_model.Organization.query.get(org_id)
            if org is not None:
                data["companies"] = [
                    org.intercom_settings(),
                ]

        return json.dumps(data)

    def flush_associated_shift_caches(self):
        schedules2 = schedule2_model.Schedule2.query.join(Role).join(
            RoleToUser).filter(RoleToUser.user_id == self.id,
                               RoleToUser.archived == False).all()
        for schedule in schedules2:
            Shifts2Cache.delete(schedule.id)

    @staticmethod
    def create_and_invite(email, name="", inviter_name=None, silent=False):
        """ Create a new user and return that account """

        if "@" not in email:
            raise Exception("Invalid email %s passed to create function." %
                            email)

        user = User(
            email=email.lower().strip(),
            name=name,
            active=False,
            confirmed=False, )

        try:
            db.session.add(user)
            db.session.commit()
        except:
            db.session.rollback()
            raise Exception("Dirty session")

        if not silent:
            User.send_activation_email(user, inviter_name)
        return user

    @staticmethod
    def send_activation_reminder(user, inviter_name=None):
        if user.active:
            raise Exception("User %s is alredy active" % user.id)

        if UserActivationReminderLimiter.allowed_to_send(user):
            User.send_activation_email(user, inviter_name)

    @staticmethod
    def send_activation_email(user, inviter_name=None):
        if inviter_name is None or len(inviter_name) == 0:
            subject = "[Action Required] Activate your Staffjoy Account"
        else:
            subject = "[Action Required] Set up your %s shift scheduling account" % (
                inviter_name)

        token = user.generate_activation_token()

        user.send_email(subject,
                        render_template(
                            "email/activate-account.html",
                            user=user,
                            token=token), True)

        UserActivationReminderLimiter.mark_sent(user)

    def generate_api_token(self, expiration=None):
        """ Create a time-based token for single page apps"""
        if not self.is_authenticated:
            raise Exception("User not authenticated")

        s = Serializer(current_app.config["SECRET_KEY"],
                       current_app.config.get("SESSION_EXPIRATION"))

        session_id = self.session_id

        return s.dumps({
            "id": self.id,
            "session_id": session_id
        }).decode("ascii")

    @staticmethod
    def verify_api_token(token):
        """Validate a time-based token (from single page apps)"""
        s = Serializer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token)
        except:
            return None

        if not data.get("id") or not data.get("session_id"):
            return None

        if SessionCache.validate_session(
                data.get("id"), data.get("session_id")):
            user = User.query.get(data.get("id"))
            if user is not None:
                user.set_session_id(data.get("session_id"))
                return user

        return None

    def send_email(self, subject, html_body, force_send=False):
        """ Send the user an email if they are active
        Allow overriding for things like account activation
        """
        if self is None:
            current_app.logger.error(
                "Could not send email becuase could not find user - subject '%s'"
                % (subject))
            return

        if not (self.active and self.confirmed) and not force_send:
            current_app.logger.info(
                "Did not send email to id %s (%s) because account inactive - subject '%s'"
                % (self.id, self.email, subject))
            return

        if not self.enable_notification_emails and not force_send:
            current_app.logger.info(
                "Did not send email to id %s (%s) because account disabled notification emails - subject '%s'"
                % (self.id, self.email, subject))
            return

        send_email(self.email, subject, html_body)

    @staticmethod
    @login_manager.token_loader
    def load_session_token(token):
        """Load cookie session"""
        s = Serializer(current_app.config["SECRET_KEY"],
                       current_app.config.get("SESSION_EXPIRATION"))
        try:
            data = s.loads(token)
        except:
            return None

        if SessionCache.validate_session(
                data.get("user_id", -1), data.get("session_id", "-1")):
            user = User.query.get(data["user_id"])
            user.set_session_id(data["session_id"])
            current_app.logger.debug("Loading user %s from cookie session %s" %
                                     (user.id, user.session_id))
            return user
        return None

    def get_auth_token(self):
        """Cookie info. Must be secure."""
        s = Serializer(current_app.config["SECRET_KEY"],
                       current_app.config["COOKIE_EXPIRATION"])
        current_app.logger.debug("Generating auth token for user %s" % self.id)

        if not self.is_authenticated:
            raise Exception("User not authenticated")

        return s.dumps({
            "user_id":
            self.id,
            "session_id":
            SessionCache.create_session(
                self.id, expiration=current_app.config["COOKIE_EXPIRATION"])
        })

    def get_id(self, expiration=None):
        """Returns the id and session id used to identify a logged-in user"""
        # Used exclusively by flask-login

        if not expiration:
            expiration = current_app.config.get("SESSION_EXPIRATION")

        if not self.is_authenticated:
            current_app.logger.info(
                "Cannot generate token because user not authenticated")
            return None

        try:
            session_id = self.session_id
            if not session_id:
                session_id = SessionCache.create_session(
                    self.id,
                    expiration=current_app.config.get("SESSION_EXPIRATION"))
        except:
            session_id = SessionCache.create_session(
                self.id,
                expiration=current_app.config.get("SESSION_EXPIRATION"))

        # flask-login handles encryption of this
        token = "%(user_id)s-%(session_id)s" % {
            "user_id": self.id,
            "session_id": session_id
        }
        return token

    @staticmethod
    @login_manager.user_loader
    def load_session_id(token):
        """Load user session as opposite of get_id function"""
        # used exclusively by flask-login
        try:
            user_id, session_id = token.split("-")
        except:
            return None

        if not user_id or not session_id:
            return None

        if SessionCache.validate_session(user_id, session_id):
            user = User.query.get(user_id)
            user.set_session_id(session_id)
            return user
        return None

    def logout_session(self):
        """Delete user's current session and cookie"""
        # Delete the session from Redis
        try:
            if self.session_id:
                SessionCache.delete_session(self.id, self.session_id)
        except:
            current_app.logger.warning("User without session_id")

        # If there is a cookie, try deleting the session in redis
        cookie_data = request.cookies.get(
            current_app.config.get("REMEMBER_COOKIE_NAME"))
        if cookie_data:
            s = Serializer(current_app.config["SECRET_KEY"])
            try:
                data = s.loads(cookie_data)
                user_id = data["user_id"]
                session_id = data["session_id"]
            except:
                current_app.logger.info("Corrupt cookie for user %s" % self.id)
                return

            if user_id and session_id:
                SessionCache.delete_session(user_id, session_id)
                current_app.logger.debug("Deleted cookie session %s" %
                                         session_id)

    def logout_target_session(self, session_id):
        """Delete user's current session and cookie"""
        SessionCache.delete_session(self.id, session_id)

    def get_target_session(self, session_id):
        """Returns info from a target session key"""
        return SessionCache.get_session_info(self.id, session_id)

    def get_all_sessions(self):

        # {session_id => {"remote_ip": "str", "last_used": utctimestamp}}

        # Get keys
        keys = SessionCache.get_all_sessions(self.id)

        output = {}
        for key in keys:
            # Key not guaranteed to be unique across users
            output[key] = SessionCache.get_session_info(self.id, key)

        return output

    def logout_all_sessions(self):
        """Log out all user sessions"""
        current_app.logger.info("Logged user %s out of all sessions" % self.id)
        SessionCache.delete_all_sessions(self.id)

    def set_session_id(self, session_id):
        self.session_id = session_id

    @property
    def phone_number(self):
        """Return phone number for API and such"""

        if not (self.phone_country_code and self.phone_national_number):
            return None

        p = phonenumbers.parse("+" + self.phone_country_code +
                               self.phone_national_number)

        # Default to show it for computers - E164 format.
        return phonenumbers.format_number(p,
                                          phonenumbers.PhoneNumberFormat.E164)

    @property
    def pretty_phone_number(self):
        """Return phone number in a readable format"""
        if not self.phone_number:
            return None

        p = phonenumbers.parse(self.phone_number)
        return phonenumbers.format_number(
            p, phonenumbers.PhoneNumberFormat.INTERNATIONAL)

    @phone_number.setter
    def phone_number(self):
        raise Exception(
            "Use verify_phone_number instead of directly setting the phone number"
        )

    def send_sms(self, message):
        """Send an SMS to the user"""
        if not self.active:
            # Stop communications to inactive users
            return

        if not self.phone_country_code and self.phone_national_number:
            raise Exception("User lacks a verified phone number")

        current_app.logger.info("Sending sms to user %s : %s" %
                                (self, message))

        send_sms(self.phone_country_code, self.phone_national_number, message)

    def get_phone_data_pending_verification(self):
        return PhoneVerificationCache.get(self.id)

    def set_phone_number(self, phone_country_code, phone_national_number):
        """Send a verification pin for a new phone number"""
        if not self.active:
            raise Exception(
                "Cannot confirm a phone number for an inactive user")

        if self.phone_number:
            # This prevents race conditions
            raise Exception(
                "Remove existing phone number before setting a new one")

        # Filter to pure digits
        phone_country_code = ''.join(i for i in phone_country_code
                                     if i.isdigit())
        phone_national_number = ''.join(i for i in phone_national_number
                                        if i.isdigit())

        # First, verify that it's a valid phone number format
        p = phonenumbers.parse("+" + str(phone_country_code) + str(
            phone_national_number))
        if not phonenumbers.is_possible_number(p):
            raise Exception("Invalid phone number")

        # check if we registered this number with somebody else.
        if User.get_user_from_phone_number(phone_country_code,
                                           phone_national_number):
            current_app.logger.info(
                "Unable to verify user %s (%s) phone number because it already belongs to another user"
                % (self.id, self.email))
            raise Exception("Phone number already belongs to a user")

        current_app.logger.info(
            "User %s (%s) is attempting to verify phone number %s" % (
                self.id, self.email, phonenumbers.format_number(
                    p, phonenumbers.PhoneNumberFormat.E164)))

        # At this point, we think we can send a message to the number

        # Generate a verification pin
        # (comes as a string due to leading zeros)
        verification_pin = ''.join(
            random.choice(string.digits)
            for x in range(self.SMS_VERIFICATION_PIN_LENGTH))

        # Set cache (before sms)
        PhoneVerificationCache.set(self.id, {
            "verification_pin":
            verification_pin,
            "phone_country_code":
            phone_country_code,
            "phone_national_number":
            phone_national_number,
        })

        # Send verification pin
        message = "Hi %s! Your Staffjoy verification pin is %s" % (
            self.first_name, verification_pin)
        send_sms(phone_country_code, phone_national_number, message)

    def verify_phone_number(self, pin):
        """Return true if new phone set, otherwise returns false."""
        data = self.get_phone_data_pending_verification()
        if not data:
            # Probably an error - might be a race condition where
            # cache decided to drop the data after too long
            raise Exception("No data pending verification")

        if data["verification_pin"] != pin:
            current_app.logger.info(
                "User %s (%s) entered incorrect phone verification pin" %
                (self.id, self.email))
            return False

        # check if we registered this number with somebody else.
        if User.get_user_from_phone_number(data["phone_country_code"],
                                           data["phone_national_number"]):
            current_app.logger.info(
                "Unable to verify user %s (%s) phone number because it already belongs to another user"
                % (self.id, self.email))

        # Pin confirmed! Put it in the database
        self.phone_national_number = data["phone_national_number"]
        self.phone_country_code = data["phone_country_code"]
        db.session.commit()

        PhoneVerificationCache.delete(self.id)
        current_app.logger.info("User %s (%s) verified their phone number" %
                                (self.id, self.email))
        return True

    def remove_phone_number(self):
        """Null out phone number fields"""
        self.phone_national_number = None
        self.phone_country_code = None
        PhoneVerificationCache.delete(self.id)
        db.session.commit()

    @classmethod
    def get_user_from_phone_number(cls, phone_country_code,
                                   phone_national_number):
        return cls.query.filter_by(
            phone_country_code=phone_country_code,
            phone_national_number=phone_national_number, ).first()
