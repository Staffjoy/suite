from staffjoy.resource import Resource


class ChompTask(Resource):
    PATH = "internal/tasking/chomp/{schedule_id}"
    ENVELOPE = None
    ID_NAME = "schedule_id"
