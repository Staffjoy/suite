import os

from app import create_app, db
from app.models import User

"""
Populates a test database with a root user
"""
app = create_app("test")
with app.app_context():
    root = User.query.filter_by(email="sudo@staffjoy.com").first()
    if root is None:
        root = User(
            username="sudo",
            email="sudo@staffjoy.com",
            name="Lenny Euler (Root)",
            active=True,
            confirmed=True,
            sudo=True,
        )
        db.session.add(root)

    db.session.commit()

