from staffjoy.resource import Resource
from staffjoy.resources.organization import Organization
from staffjoy.resources.cron import Cron
from staffjoy.resources.user import User
from staffjoy.resources.plan import Plan
from staffjoy.resources.chomp_task import ChompTask
from staffjoy.resources.mobius_task import MobiusTask


class Client(Resource):
    def get_organizations(self, limit=25, offset=0, **kwargs):
        return Organization.get_all(parent=self,
                                    limit=limit,
                                    offset=offset,
                                    **kwargs)

    def get_organization(self, id):
        return Organization.get(parent=self, id=id)

    def create_organization(self, **kwargs):
        return Organization.create(parent=self, **kwargs)

    def cron(self):
        """Internal only - cron job manual timer"""
        return Cron.get_all(parent=self)

    def get_users(self, limit=25, offset=0, **kwargs):

        # Some supported filters: filterbyUsername, filterByEmail
        return User.get_all(parent=self, limit=limit, offset=offset, **kwargs)

    def get_user(self, id):
        return User.get(parent=self, id=id)

    def get_plans(self, **kwargs):
        return Plan.get_all(parent=self, **kwargs)

    def get_plan(self, id):
        return Plan.get(parent=self, id=id)

    def get_chomp_task(self, id):
        # id is schedule id
        return ChompTask.get(parent=self)

    def get_chomp_tasks(self, **kwargs):
        return ChompTask.get(parent=self)

    def claim_chomp_task(self):
        return ChompTask.create(parent=self)

    def get_mobius_task(self, id):
        # id is schedule id
        return MobiusTask.get(parent=self)

    def get_mobius_tasks(self, **kwargs):
        return MobiusTask.get(parent=self)

    def claim_mobius_task(self):
        return MobiusTask.create(parent=self)
