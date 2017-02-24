(function(root) {

    "use strict";

    var Views = root.App.Views,
        Models = root.App.Models,
        Collections = root.App.Collections
    ;

    var RolePreferencesView = Views.Base.extend({
        el: "#manage-main",
        events: {
            "click span.card-element-active.edit-param": "editProperty",
        },
        initialize: function(opts) {
            RolePreferencesView.__super__.initialize.apply(this);
            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.locationId)) {
                    this.locationId = opts.locationId;
                }

                if (!_.isUndefined(opts.orgModel)) {
                    this.orgModel = opts.orgModel;
                }

                if (!_.isUndefined(opts.recurringShiftsCollection)) {
                    this.recurringShiftsCollection = opts.recurringShiftsCollection;
                }
            }

            this.mainHeaderContentVisible = 'roles';
        },
        render: function(opts) {
            var self = this,
                userRolesCollection = new Collections.UserRoles(),
                users = self.model.get("users"),
                userCardView,
                data = _.extend({}, self.model.toJSON(), opts)
            ;

            _.each(users, function(user, index, list) {
                var userModel = new Models.UserRole(user);

                userModel.addUpstreamModel("locationId", self.locationId);
                userModel.addUpstreamModel("roleId", self.model.get("id"));
                userRolesCollection.add(userModel);
            });

            self.$el.html(ich.role_preferences(data));

            self.addDelegateView(
                self.model.get("id"),
                new Views.RoleUserCardView({
                    collection: userRolesCollection,
                    roleId: self.model.get("id"),
                    roleName: self.model.get("name"),
                    locationId: self.locationId,
                })
            );

            // scheduling preferences / core worker profile
            if (self.orgModel.isBoss()) {
                self.addDelegateView(
                    self.model.get("id") + "-preferences",
                    new Views.SchedulingPreferencesCardView({
                        model: self.model,
                        strings: {
                            title: "Weekly Scheduling Preferences",
                        },
                        template: "role-preferences",
                    })
                );
            }

            self.addDelegateView(
                'danger-zone',
                new Views.DangerZoneCard({
                    description: "Clicking here will delete " + data.name + " including all of it's users.",
                    buttonLabel: 'Delete ' + data.name,
                    confirmationMessage: 'Are you sure you want to delete ' + data.name + ' including all of its users? Staffjoy retains some data for compliance purposes, such as preserving payroll records.',
                    dangerZoneCallback: self.deleteRole.bind(self),
                })
            );

            self.addDelegateView(
                'recurring-shifts-role',
                new Views.RecurringShiftsCardView({
                    roleModel: self.model,
                    recurringShiftsCollection: self.recurringShiftsCollection,
                    userRolesCollection: userRolesCollection,
                    orgModel: self.orgModel,
                    showDescription: true,
                })
            );

            return this;
        },
        getAction: function() {
            var self = this,
                action = {
                    label: 'Create',
                    callback: function(event) {
                        var $target = $(event.target),
                            id = $target.data('id')
                        ;

                        switch (id) {
                            case 'addWorker':
                                Backbone.history.navigate(Backbone.history.getFragment() + "/add-worker", {trigger: true});
                                break;
                            case 'recurringShiftCreate':
                                $('#manager-header-action .dropdown-toggle').dropdown('toggle')
                                self.delegateViews['recurring-shifts-role'].editShift(event);
                                break;
                        }
                    },
                    data: [
                        {
                            label: 'Add Worker',
                            id: 'addWorker',
                        },
                        {
                            label: 'Recurring Shift',
                            id: 'recurringShiftCreate',
                        }
                    ]
                };
            ;

            return action;
        },
        editProperty: function(e) {
            var self = this,
                roleId = self.model.id,
                $target = $(e.target).closest(".card-element-active"),
                param = $target.attr("data-param"),
                locationId = self.locationId
            ;

            e.preventDefault();
            e.stopPropagation();

            Backbone.history.navigate("/locations/" + locationId + "/roles/" + roleId + "/preferences/" + param, {trigger: true});
        },
        deleteRole: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target),
                roleName = self.model.get("name"),
                locationId = self.locationId,
                success,
                error
            ;

            $target.addClass("disabled");

            success = function(collection, response, opts) {
                $.notify({message: "Successfully deleted " + roleName}, {type:"success"});
                Backbone.history.navigate("/locations/" + locationId + "/roles", {trigger: true});
            };

            error = function(collection, response, opts) {
                $.notify({message:"Unable to delete " + roleName},{type: "danger"});
                $target.removeClass("disabled");
            };

            self.model.destroy({
                success: success,
                error: error,
            });
        },
    });

    root.App.Views.RolePreferencesView = RolePreferencesView;

})(this);
