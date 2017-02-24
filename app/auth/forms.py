from flask.ext.wtf import Form, RecaptchaField
from wtforms import StringField, PasswordField, BooleanField, \
    SubmitField, SelectField, HiddenField

from wtforms.fields.html5 import EmailField
from wtforms.validators import Required, Length, Email, Regexp, EqualTo
from wtforms import ValidationError

from app.models import User
from app.plans import plans


class SignUpForm(Form):
    # WTF doesn"t have default "placeholder", so we use "label" for that
    name = StringField(
        "Name",
        validators=[Required(), Length(1, 256)],
        description="Leonhard Euler")
    email = StringField(
        "Email",
        validators=[Required(), Length(1, 256), Email()],
        description="Lenny@7Bridg.es")
    username = StringField(
        "Username",
        validators=[
            Required(), Length(1, 64),
            Regexp("^[A-Za-z][A-Za-z0-9_.]*$", 0,
                   "Usernames must have only letters, "
                   "numbers, dots or underscores")
        ],
        description="7Bridges")
    password = PasswordField(
        "Password",
        validators=[Length(8, 256), Required()],
        description="??????")
    password2 = PasswordField(
        "Confirm password",
        validators=[
            Required(), EqualTo("password", message="Passwords must match")
        ],
        description="??????")
    recaptcha = RecaptchaField()
    submit = SubmitField("Submit")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError("Email already registered.")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data.lower().strip()).first():
            raise ValidationError("Username already in use.")


class FreeTrialForm(Form):
    # WTF doesn"t have default "placeholder", so we use "label" for that
    name = StringField(
        "Your Name",
        validators=[Required(), Length(1, 256)],
        description="Leonhard Euler")
    email = StringField(
        "Your Email",
        validators=[Required(), Length(1, 256), Email()],
        description="Lenny@7Bridg.es")
    password = PasswordField(
        "Password",
        validators=[Length(8, 256), Required()],
        description="??????")
    company_name = StringField(
        "Name of your company",
        validators=[Required(), Length(1, 256)],
        description="7 Bridges Coffee")

    plan = SelectField(
        "Type of Workers",
        choices=[(key, value["for"]) for key, value in plans.iteritems()
                 if value["active"]],
        validators=[Required()], )

    enterprise_access = SelectField(
        u"Are you planning on scheduling more than 40 workers?",
        choices=[
            ("no", "No"),
            ("yes", "Yes"),
        ],
        default="no",
        validators=[Required()], )

    day_week_starts = SelectField(
        u"Day of the week on which your schedules begin",
        choices=[
            ("monday", "Monday"),
            ("tuesday", "Tuesday"),
            ("wednesday", "Wednesday"),
            ("thursday", "Thursday"),
            ("friday", "Friday"),
            ("saturday", "Saturday"),
            ("Sunday", "Sunday"),
        ],
        validators=[Required()], )
    timezone = HiddenField()
    tos = BooleanField(
        "I agree to the <a href=\"/terms/\">Terms and Conditions</a> and the <a href=\"/privacy-policy/\">Privacy Policy</a>.",
        validators=[
            Required(
                message="You must agree to these terms to create or activate an account."
            )
        ])
    submit = SubmitField("Submit")

    def validate_email(self, field):
        if User.query.filter_by(email=field.data.lower().strip()).first():
            raise ValidationError("Email already registered.")


class LoginForm(Form):
    email = StringField(
        "Email",
        validators=[Required(), Length(1, 256)],
        description="Lenny@7Bridg.es")
    password = PasswordField(
        "Password",
        validators=[Required(), Length(1, 256)],
        description="??????")
    remember_me = BooleanField("Keep me logged in")
    submit = SubmitField("Submit")


class NativeLoginForm(Form):
    email = EmailField(
        "Email",
        validators=[Required(), Length(1, 256)],
        description="Lenny@7Bridg.es")
    password = PasswordField(
        "Password",
        validators=[Required(), Length(1, 256)],
        description="??????")
    submit = SubmitField("Submit")


class RequestPasswordResetForm(Form):
    email = StringField(
        "Email",
        validators=[Required(), Length(1, 64), Email()],
        description="Lenny@7Bridg.es")
    recaptcha = RecaptchaField()
    submit = SubmitField("Request Reset")


class PasswordResetForm(Form):
    email = StringField(
        "Email",
        validators=[Required(), Length(1, 64), Email()],
        description="Lenny@7Bridg.es")
    password = PasswordField(
        "Password",
        validators=[Length(8, 256), Required()],
        description="??????")

    password2 = PasswordField("Confirm password", validators=[Required(), \
        EqualTo("password", message="Passwords must match")], description="??????")
    submit = SubmitField("Reset Password")

    def validate_email(self, field):
        if User.query.filter_by(
                email=field.data.lower().strip()).first() is None:
            raise ValidationError("Unknown email address.")


class ChangePasswordForm(Form):
    old_password = PasswordField(
        "Current Password",
        validators=[Length(1, 256), Required()],
        description="??????")
    password = PasswordField(
        "New Password",
        validators=[Length(8, 256), Required()],
        description="??????")
    password2 = PasswordField("Confirm password", validators=[Required(), \
        EqualTo("password", message="Passwords must match")], description="??????")
    submit = SubmitField("Change")


class ChangeNameForm(Form):
    name = StringField(
        "Name",
        validators=[Required(), Length(1, 256)],
        description="Leonhard Euler")
    submit = SubmitField("Update")


class ChangeEmailForm(Form):
    email = StringField(
        "Email",
        validators=[Required(), Length(1, 256), Email()],
        description="Lenny@7Bridg.es")
    submit = SubmitField("Update")

    def __init__(self, user, *args, **kwargs):
        super(ChangeEmailForm, self).__init__(*args, **kwargs)
        self.user = user

    def validate_email(self, field):
        match = User.query.filter_by(email=field.data.lower().strip()).first()
        if match is not None and match.id != self.user.id:
            raise ValidationError("Email already registered.")


class ChangeUsernameForm(Form):
    username = StringField(
        "Username",
        validators=[
            Required(), Length(1, 64),
            Regexp("^[A-Za-z][A-Za-z0-9_.]*$", 0,
                   "Usernames must have only letters, "
                   "numbers, dots or underscores")
        ],
        description="7Bridges")
    submit = SubmitField("Update")

    def __init__(self, user, *args, **kwargs):
        super(ChangeUsernameForm, self).__init__(*args, **kwargs)
        self.user = user

    def validate_username(self, field):
        match = User.query.filter_by(
            username=field.data.lower().strip()).first()
        if match is not None and match.id != self.user.id:
            raise ValidationError("Username already in use.")


class ActivateForm(Form):
    name = StringField(
        "Name",
        validators=[Required(), Length(1, 256)],
        description="Leonhard Euler")
    username = StringField(
        "Username",
        validators=[
            Required(), Length(1, 64),
            Regexp("^[A-Za-z][A-Za-z0-9_.]*$", 0,
                   "Usernames must have only letters, "
                   "numbers, dots or underscores")
        ],
        description="7Bridges")
    password = PasswordField(
        "Password",
        validators=[Length(8, 256), Required()],
        description="??????")
    password2 = PasswordField("Confirm password", validators=[Required(), \
        EqualTo("password", message="Passwords must match")], description="??????")
    tos = BooleanField(
        "I agree to the <a href=\"/terms/\">Terms and Conditions</a> and the <a href=\"/privacy-policy/\">Privacy Policy</a>.",
        validators=[
            Required(
                message="You must agree to these terms to create or activate an account."
            )
        ])
    recaptcha = RecaptchaField()
    submit = SubmitField("Submit")

    def validate_username(self, field):
        if User.query.filter_by(username=field.data.lower().strip()).first():
            raise ValidationError("Username already in use.")


class ApiKeyForm(Form):
    name = StringField(
        "Key Label",
        validators=[Required(), Length(1, 256)],
        description="Which program will use this key?")
    submit = SubmitField("Issue")


class SessionsForm(Form):
    submit = SubmitField("Logout All Sessions")


class ChangeNotificationsForm(Form):
    enable_notification_emails = BooleanField(
        "Send Email Alerts", )
    enable_timeclock_notification_sms = BooleanField(
        "Send SMS Timeclock Notifications")
    submit = SubmitField("Save")


class NewPhoneNumberForm(Form):
    def __init__(self, country_code_choices, *args, **kwargs):
        super(NewPhoneNumberForm, self).__init__(*args, **kwargs)
        self.phone_country_code.choices = country_code_choices

    phone_country_code = SelectField(
        "Country Code",
        choices=[],
        validators=[Required()], )
    phone_national_number = StringField(
        "National Phone Number",
        validators=[Required(), Length(1, 256)],
        description="443-578-3359")
    submit = SubmitField("Save")


class VerifyPhoneNumberForm(Form):
    pin = StringField(
        "Verification Pin",
        validators=[Required(), Length(1, 256)],
        description="")
    submit = SubmitField("Confirm")


class RemovePhoneNumberForm(Form):
    submit = SubmitField("Remove phone number")
