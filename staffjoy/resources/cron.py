from staffjoy.resource import Resource


class Cron(Resource):
    PATH = "internal/cron/"
    ID_NAME = ""
    ENVELOPE = None

    # Usage: cron.getall()
