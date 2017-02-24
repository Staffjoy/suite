from app import db


class RoleToUser(db.Model):
    __tablename__ = 'roles_to_users'
    id = db.Column(db.Integer, primary_key=True, nullable=False)
    role_id = db.Column(
        "role_id", db.Integer, db.ForeignKey("roles.id"), index=True)
    user_id = db.Column(
        "user_id", db.Integer, db.ForeignKey("users.id"), index=True)
    min_half_hours_per_workweek = db.Column(
        db.Integer, default=40, server_default="40", nullable=False)
    max_half_hours_per_workweek = db.Column(
        db.Integer, default=80, server_default="80", nullable=False)
    internal_id = db.Column(db.String(256), index=True, nullable=True)
    working_hours = db.Column(db.LargeBinary)
    archived = db.Column(
        db.Boolean, default=False, server_default="0", nullable=False)
