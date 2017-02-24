from datetime import datetime
from sqlalchemy import ForeignKey

from app import db


class Preference(db.Model):
    __tablename__ = "preferences"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(
        db.Integer, ForeignKey("users.id"), index=True, nullable=False)
    schedule_id = db.Column(
        db.Integer, ForeignKey("schedules2.id"), index=True, nullable=False)
    created_at = db.Column(db.DateTime(), default=datetime.utcnow)
    last_update = db.Column(db.DateTime(), onupdate=datetime.utcnow)
    preference = db.Column(db.LargeBinary)
