from flask import current_app
import mandrill

from app import create_celery_app
celery = create_celery_app()


def send_email(to, subject, html_body):
    """Wrap async email sender"""
    _send_email.apply_async(args=[to, subject, html_body])


@celery.task(bind=True, max_retries=2)
def _send_email(self, to, subject, html_body):

    # We intentionally commented out this code - we used it to prevent emails in development from going to non-Staffjoy emails.
    """
    if current_app.config.get("ENV") != "prod":
        allowed_domains = ["@staffjoy.com", "@7bridg.es"]
        ok = False
        for d in allowed_domains:
            if to[-len(d):].lower() == d:
                ok = True

        if not ok:
            current_app.logger.info(
                "Intercepted email to %s and prevented sending due to environment rules."
                % to)
            return
    """

    if to in current_app.config.get("EMAIL_BLACKLIST") or (
            to.startswith("demo+") and to.endswith("@7bridg.es")):
        current_app.logger.debug(
            "Not sending email to %s becuase it is blacklisted" % to)
        return

    current_app.logger.info("Sending an email to %s - subject '%s'" %
                            (to, subject))

    try:
        client = mandrill.Mandrill(current_app.config.get('MANDRILL_API_KEY'))

        # Staffjoy originaly used a Mandrill template hosted in our account.
        # We have commented it out, and subbed in a no-template sender.
        # pylint: disable=pointless-string-statement
        """
        template_content = [
            {'content': html_body,
             'name': 'body'},
            {'content': subject,
             'name': 'title'},
        ]

        message = {
            'auto_text': True,
            'subject': subject,
            "headers": {
                "Reply-To": "help@staffjoy.com",
            },
            'to': [{'email': to,
                    'type': 'to'}]
        }

        client.messages.send_template(
            template_name=current_app.config.get('MANDRILL_TEMPLATE'),
            template_content=template_content,
            message=message)
        """

        # If you restore the above code, comment this out
        message = {
            'auto_text': True,
            'subject': subject,
            'html': html_body,
            "headers": {
                "Reply-To": current_app.config.get("FROM_EMAIL"),
            },
            'to': [{
                'email': to,
                'type': 'to'
            }]
        }
        client.messages.send(message=message, async=False)

    except mandrill.Error, e:
        # Mandrill errors are thrown as exceptions
        # and they can include things like "out of credits"
        current_app.logger.exception(
            'A mandrill error to email %s occurred: %s - %s' %
            (to, e.__class__, e))
        raise self.retry(exc=e)
