from tests.unit.test_base import BasicsTestCase

from flask import g
from app import db
from app.models import Location, Role, User


class AppTestUser(BasicsTestCase):
    def test_is_sudo(self):

        # admin is not
        g.current_user = self.admin
        assert not g.current_user.is_sudo()

        # manager is not
        g.current_user = self.manager
        assert not g.current_user.is_sudo()

        # user1 is not
        g.current_user = self.user1
        assert not g.current_user.is_sudo()

        # make a sudo user
        sudo_dude = User(
            email="sudodude@7bridg.es", name="Sudo Dude", sudo=True)
        db.session.add(sudo_dude)
        db.session.commit()

        g.current_user = sudo_dude
        assert g.current_user.is_sudo()

    def test_is_org_admin_or_location_manager(self):

        # create a 2nd location
        location2 = Location(
            name="2nd Location",
            organization_id=self.organization.id,
            timezone="UTC")
        db.session.add(location2)
        db.session.commit()

        # org admins can access all
        g.current_user = self.admin
        assert g.current_user.is_org_admin_or_location_manager(
            org_id=self.organization.id, location_id=self.location.id)
        assert g.current_user.is_org_admin_or_location_manager(
            org_id=self.organization.id, location_id=location2.id)

        # role to users are not either
        g.current_user = self.user2
        assert not g.current_user.is_org_admin_or_location_manager(
            org_id=self.organization.id, location_id=self.location.id)
        assert not g.current_user.is_org_admin_or_location_manager(
            org_id=self.organization.id, location_id=location2.id)

        # location managers have selective access
        g.current_user = self.manager
        assert g.current_user.is_org_admin_or_location_manager(
            org_id=self.organization.id, location_id=self.location.id)
        assert not g.current_user.is_org_admin_or_location_manager(
            org_id=self.organization.id, location_id=location2.id)

        # make user2 a manager of the new location
        location2.managers.append(self.user2)
        db.session.commit()

        g.current_user = self.user2
        assert not g.current_user.is_org_admin_or_location_manager(
            org_id=self.organization.id, location_id=self.location.id)
        assert g.current_user.is_org_admin_or_location_manager(
            org_id=self.organization.id, location_id=location2.id)

    def test_is_org_admin(self):

        # org admins have access
        g.current_user = self.admin
        assert g.current_user.is_org_admin(org_id=self.organization.id)

        # role to users do not
        g.current_user = self.user2
        assert not g.current_user.is_org_admin(org_id=self.organization.id)

        # location managers do not
        g.current_user = self.manager
        assert not g.current_user.is_org_admin(org_id=self.organization.id)

    def test_is_manager_in_org(self):

        # org admins are not managers
        g.current_user = self.admin
        assert not g.current_user.is_manager_in_org(
            org_id=self.organization.id)

        # role to users do not
        g.current_user = self.user2
        assert not g.current_user.is_manager_in_org(
            org_id=self.organization.id)

        # location managers do
        g.current_user = self.manager
        assert g.current_user.is_manager_in_org(org_id=self.organization.id)

        # create a 2nd location
        location2 = Location(
            name="2nd Location",
            organization_id=self.organization.id,
            timezone="UTC")
        db.session.add(location2)
        db.session.commit()

        # make user2 a manager of the new location
        location2.managers.append(self.user2)
        db.session.commit()

        g.current_user = self.user2
        assert g.current_user.is_manager_in_org(org_id=self.organization.id)

    def test_is_location_manager(self):

        # create a 2nd location
        location2 = Location(
            name="2nd Location",
            organization_id=self.organization.id,
            timezone="UTC")
        db.session.add(location2)
        db.session.commit()

        # org admins are not managers
        g.current_user = self.admin
        assert not g.current_user.is_location_manager(
            location_id=self.location.id)
        assert not g.current_user.is_location_manager(location_id=location2.id)

        # role to users are not either
        g.current_user = self.user2
        assert not g.current_user.is_location_manager(
            location_id=self.location.id)
        assert not g.current_user.is_location_manager(location_id=location2.id)

        # location managers have selective access
        g.current_user = self.manager
        assert g.current_user.is_location_manager(location_id=self.location.id)
        assert not g.current_user.is_location_manager(location_id=location2.id)

        # make user2 a manager of the new location
        location2.managers.append(self.user2)
        db.session.commit()

        g.current_user = self.user2
        assert not g.current_user.is_location_manager(
            location_id=self.location.id)
        assert g.current_user.is_location_manager(location_id=location2.id)

    def test_is_location_worker(self):
        # create a 2nd location
        location2 = Location(
            name="2nd Location",
            organization_id=self.organization.id,
            timezone="UTC")
        db.session.add(location2)
        db.session.commit()

        # create a 2nd role
        role2 = Role(name="2nd Role", location_id=location2.id)
        db.session.add(role2)

        # admins are not considered workers in the location
        g.current_user = self.admin
        assert not g.current_user.is_location_worker(
            location_id=self.location.id)
        assert not g.current_user.is_location_worker(location_id=location2.id)

        # location managers are also not considered workers
        g.current_user = self.manager
        assert not g.current_user.is_location_worker(
            location_id=self.location.id)
        assert not g.current_user.is_location_worker(location_id=location2.id)

        g.current_user = self.user1
        assert g.current_user.is_location_worker(location_id=self.location.id)
        assert not g.current_user.is_location_worker(location_id=location2.id)
