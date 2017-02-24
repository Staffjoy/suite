from staffjoy.resource import Resource


class OrganizationWorker(Resource):
    """Organization workers - this endpoint is only a get collection"""
    PATH = "organizations/{organization_id}/workers/"
