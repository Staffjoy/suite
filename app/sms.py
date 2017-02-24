import phonenumbers
from twilio.rest import TwilioRestClient
from flask import current_app, Response

from app import create_celery_app
celery = create_celery_app()

# Class for interacting with Twilio.
# If it's not text, it's in ivr blueprint.


def twiml(resp):
    """Make an XML response for twilio"""
    resp = Response(str(resp))
    resp.headers['Content-Type'] = 'text/xml'
    return resp


def staffjoy_phone_number(country_code=None, fmt=None):
    """Return Staffjoy phonenumber in for outputs"""
    DEFAULT_CC = "1"  # USA

    if fmt is None or fmt is "pretty":
        fmt = phonenumbers.PhoneNumberFormat.INTERNATIONAL
    elif fmt is "E164":
        fmt = phonenumbers.PhoneNumberFormat.E164
    elif fmt is "local":
        fmt = phonenumbers.PhoneNumberFormat.NATIONAL

    if country_code is None or not str(country_code) in current_app.config[
            "TWILIO_NUMBER"]:
        country_code = DEFAULT_CC

    p = phonenumbers.parse("+" + country_code + current_app.config[
        "TWILIO_NUMBER"][country_code])

    return phonenumbers.format_number(p, fmt)


def send_sms(country_code, user_local_number, message):
    """Wrap async sms sender"""
    _send_sms.apply_async(args=[country_code, user_local_number, message])


@celery.task(bind=True, max_retries=2)
def _send_sms(self, country_code, user_local_number, message):
    """Send a message to a number. Mainly access via the user_model"""

    # If we're not in production, prepend the env for sanity
    if current_app.config.get("ENV") != "prod":
        message = "[%s] %s" % (current_app.config.get("ENV", "dev"), message)

    # Get the phone number from config.
    # In future, if we have multiple numbers per country code, this needs
    # to be modified (to pick between numbers)
    staffjoy_local_number = current_app.config["TWILIO_NUMBER"].get(
        country_code)
    if staffjoy_local_number is None:
        raise Exception("No known number for country code %s" % country_code)

    client = _get_twilio_client()

    message = client.messages.create(
        body=message,
        to="+%s%s" %
        (country_code, user_local_number),  # Replace with your phone number
        from_="+%s%s" %
        (country_code,
         staffjoy_local_number)  # Replace with your Twilio number
    )


def _get_twilio_client():
    """Return twilio rest client with variables"""
    return TwilioRestClient(
        current_app.config.get("TWILIO_ACCOUNT_SID"),
        current_app.config.get("TWILIO_AUTH_TOKEN"))
