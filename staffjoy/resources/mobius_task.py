from staffjoy.resource import Resource


class MobiusTask(Resource):
    PATH = "internal/tasking/mobius/{schedule_id}"
    ID_NAME = "schedule_id"
    ENVELOPE = None
