import os

from app import create_app, db
from app.models import User

"""
Populates a dev database with cool information :-)
"""
app = create_app("dev")
PASSWORD = "staffjoydev"
FILE = "/vagrant/user.txt"
with app.app_context():
    if not os.path.isfile(FILE):
        print "READ THE README! You're missing a user.txt file"
        os.exit(1)

    with open(FILE, "r") as f:
        user_email = f.read().strip()

    if len(user_email) == 0:
        print "You did not provide your email!"
        print "READ THE README! Put it in user.txt!"
        os.exit(1)

    if "@" not in user_email:
        print "Invalid email."
        print "READ THE README!"
        os.exit(1)

    # See if the user exists. If not, make it and make it sudo.
    user = User.query.filter_by(email=user_email.lower()).first()
    # otherwise invite by email
    if user is None:
        user = User.create_and_invite(
            user_email,
            "%s" % user_email.split("@")[0]
        )
    user.sudo = True
    
    # We use this fake email account for cron jobs. 
    root = User.query.filter_by(email="sudo@staffjoy.com").first()		
    dev_key = "staffjoydev"		
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
    print "Check your email to activate your sudo account, then use free trial to set up an org"

