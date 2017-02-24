import os
import binascii
from datetime import datetime

from werkzeug.security import generate_password_hash, check_password_hash
from flask import current_app, render_template
from itsdangerous import JSONWebSignatureSerializer as Signer
from sqlalchemy import ForeignKey

from app import db
from app.models import user_model


class ApiKey(db.Model):
    __tablename__ = "apikeys"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, ForeignKey('users.id'))
    name = db.Column(db.String(256))  # User-defined
    key_hash = db.Column(db.String(128))
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)
    last_used = db.Column(db.DateTime(), default=datetime.utcnow)

    @property
    def key(self):
        raise AttributeError("key is not a readable attribute")

    @key.setter
    def key(self, key):
        self.key_hash = generate_password_hash(key)

    def verify_key(self, key):
        if check_password_hash(self.key_hash, key):
            self.last_used = datetime.utcnow()
            return True
        return False

    @classmethod
    def get_user(cls, token):
        """Use this function to validate tokens sent by users."""
        # Decode token, try to fetch and verify key, and if so return user

        # DEVELOPMENT ACCESS
        if current_app.config.get("DEBUG") == True:
            if token == current_app.config.get("DEV_CRON_API_KEY"):
                return user_model.User.query.filter_by(
                    email=current_app.config.get("DEV_CRON_EMAIL")).first()

        s = Signer(current_app.config["SECRET_KEY"])
        try:
            data = s.loads(token.strip())  # Remove whitespace
        except:
            return None

        if not data.get("id"):
            return None

        if not data.get("key"):
            return None

        apikey = ApiKey.query.get(data.get("id"))
        if apikey is not None:
            if apikey.verify_key(data.get("key")):
                return user_model.User.query.get(apikey.user_id)
        return None

    @staticmethod
    def generate_key(user_id, name):
        """Generate a new key and return the plaintext token"""
        apikey = ApiKey()
        apikey.user_id = user_id
        apikey.name = name

        # Generate key
        # Want 40 char string which is urandom 20.
        # urandom is cryptographically secure.
        key = binascii.hexlify(os.urandom(20))

        apikey.key = key
        db.session.add(apikey)
        db.session.commit()

        # Send an email about this action
        u = user_model.User.query.get(user_id)
        u.send_email(
            "[Alert] New API Key Issued",
            render_template(
                "email/new-api-key.html",
                name=name, ),
            force_send=True)

        # Generate token, which include the indexed id and key
        s = Signer(current_app.config["SECRET_KEY"])
        return s.dumps({"id": apikey.id, "key": key})
