from datetime import datetime

from flask import url_for, request, current_app, abort
from twilio.util import RequestValidator
import twilio.twiml
import phonenumbers

import pytz

from app.ivr import ivr
from app.sms import twiml, send_sms
from app.models import User


@ivr.before_request
def authenticate():
    """Verify that request came from Twilio"""
    if current_app.config.get("DEBUG"):
        return  # Don't auth in dev

    # Auth that it came from twilio

    validator = RequestValidator(current_app.config.get("TWILIO_AUTH_TOKEN"))
    valid = validator.validate(request.url, request.form,
                               request.headers.get('X-Twilio-Signature', ''))

    if not valid:
        # If the request was spoofed, then send '403 Forbidden'.
        current_app.logger.info("IVR detected spoofed incoming call")
        abort(403)

    # Final thing - check that the number is registered to the application.
    # HYPOTHETICALLY - somebody could buy a number through their own
    # twilio account and point it at our app, and be able to cause
    # issues.
    to = request.values.get("To")
    if not to:
        current_app.logger.info("IVR missing To parameter")
        abort(403)
    p = phonenumbers.parse(to)
    if not current_app.config["TWILIO_NUMBER"].get(str(p.country_code)) == str(
            p.national_number):
        current_app.logger.info("IVR call to unregistered number - %s" % to)
        abort(403)
    return


@ivr.route("/sms/", methods=["POST"])
def sms():
    """All inbound sms comes to this function"""
    # (other functions in this file handle voice)

    from_number = request.values.get("From")
    to_number = request.values.get("To")

    p_from = phonenumbers.parse(from_number)

    from_user = User.get_user_from_phone_number(
        str(p_from.country_code), str(p_from.national_number))

    if from_user:
        current_app.logger.info(
            "Incoming SMS from %s to Staffjoy number %s by user %s" %
            (from_number, to_number, from_user))
    else:
        current_app.logger.info(
            "Incoming SMS from %s to Staffjoy number %s (unknown user) " %
            (from_number, to_number))

    # Get a response
    # CURRENTLY - we don't support incoming sms and just send a generic message.
    # IN THE FUTURE - we may want to process message, in which case we would send the message body for processing.

    if from_user:
        # Greet the user by name
        message = "Hi %s - email help@staffjoy.com for support. Manage which notifications you receive in \"My Account\"." % (
            from_user.name or "there")
    else:
        message = "You have reached Staffjoy.com - Reply STOP to unsubscribe."

    send_sms(str(p_from.country_code), str(p_from.national_number), message)

    return "<Response></Response>"  # Twilio null response


@ivr.route("/", methods=["POST"])
def welcome():
    from_number = request.values.get("From")
    to_number = request.values.get("To")

    p_from = phonenumbers.parse(from_number)

    from_user = User.get_user_from_phone_number(
        str(p_from.country_code), str(p_from.national_number))

    if from_user:
        current_app.logger.info(
            "Incoming call from %s to Staffjoy number %s by user %s" %
            (from_number, to_number, from_user))
    else:
        current_app.logger.info(
            "Incoming call from %s to Staffjoy number %s (unknown user) " %
            (from_number, to_number))

    response = twilio.twiml.Response()
    with response.gather(
            numDigits=1, action=url_for("ivr.menu"), method="POST") as g:
        g.say(
            "Thank you for calling Staffjoy. " + "For sales, press 1. " +
            "For support, press 2. " + "For billing, press 3. " +
            "For corporate matters, press 4.",
            loop=3,
            voice="alice",
            language="en-gb")
    return twiml(response)


@ivr.route("/menu", methods=["POST"])
def menu():
    selected_option = request.form["Digits"]
    option_actions = {
        "1": _sales,
        "2": _support,
        "3": _billing,
        "4": _corporate,
    }

    if selected_option in option_actions:
        response = twilio.twiml.Response()
        option_actions[selected_option](response)
        return twiml(response)

    return _redirect_welcome()


def _business_open():
    """Check whether it's monday through friday 8am to 8pm"""
    OFFICE_TZ = "America/Los_Angeles"
    DEFAULT_TZ = "UTC"

    now = datetime.utcnow().replace(
        tzinfo=pytz.timezone(DEFAULT_TZ)).astimezone(pytz.timezone(OFFICE_TZ))

    # Check if it's not monday through friday
    if now.isoweekday() not in range(1, 6):
        return False

    # Check if 8am to 8pm, inclusive to exclusive
    if now.hour not in range(8, 15):
        return False

    return True


def _sales(response):
    SALES_NUMBER = "+1<phonenumber>"

    response.say(
        "Now connecting you to Staffjoy sales. " +
        "You may also send an email to sales at staffjoy dot com.",
        voice="alice",
        language="en-gb")
    response.dial(SALES_NUMBER)
    return twiml(response)


def _support(response):
    response.say(
        "Staffjoy support operates over email. Please send your question to " +
        "help at staffjoy dot com for prompt help. To see the system " +
        "status, visit status dot staffjoy dot com. You may also find answers to common "
        +
        "questions at help dot staffjoy.com. Thank you for calling Staffjoy. "
        + "Bye!",
        voice="alice",
        language="en-gb")

    response.hangup()
    return twiml(response)


def _billing(response):
    BILLING_NUMBER = "+1<phonenumber>"  # Phone number

    if _business_open():
        response.say(
            "Now connecting you to Staffjoy billing.  " +
            "You may also send an email to billing at staffjoy dot com.",
            voice="alice",
            language="en-gb")
        response.dial(BILLING_NUMBER)
    else:
        response.say(
            "The Staffjoy billing office is currently closed. Please email " +
            "billing at Staffjoy dot com for prompt service. " +
            "Thanks for calling Staffjoy - Bye!",
            voice="alice",
            language="en-gb")

        response.hangup()

    return twiml(response)


def _corporate(response):
    CORPORATE_NUMBER = "+1<phonenumber>"  # Phone number
    if _business_open():
        response.say(
            "Now connecting you to Staffjoy corporate.",
            voice="alice",
            language="en-gb")
        response.dial(CORPORATE_NUMBER)
    else:
        response.say(
            "Staffjoy headquarters is currently closed. Please " +
            "email help at Staffjoy dot com for prompt service. " +
            "Thanks for calling Staffjoy - Bye!",
            voice="alice",
            language="en-gb")

        response.hangup()

    return twiml(response)


def _redirect_welcome():
    response = twilio.twiml.Response()
    response.say(
        "Returning to the main menu.", voice="alice", language="en-gb")
    response.redirect(url_for("ivr.welcome"))

    return twiml(response)
