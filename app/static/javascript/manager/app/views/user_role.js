(function(root) {

    "use strict";

    var Util = root.App.Util,
        Views = root.App.Views
    ;

    var UserRoleView = Views.Base.extend({
        el: "#manage-main",
        events: {
            "click .user-role-info span.card-element-active": "editProperty",
            "click .reminder-email": "sendReminderEmail",
        },
        initialize: function(opts) {
            /*
             * this view is used for pages with this route: #locations/:id/roles/:id/users/:id
             */

            UserRoleView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.locationId)) {
                    this.locationId = opts.locationId;
                }

                if (!_.isUndefined(opts.organizationModel)) {
                    this.organizationModel = opts.organizationModel;
                }

                if (!_.isUndefined(opts.roleId)) {
                    this.roleId = opts.roleId;
                }

                if (!_.isUndefined(opts.roleModel)) {
                    this.roleModel = opts.roleModel;
                }

                if (!_.isUndefined(opts.recurringShiftsCollection)) {
                    this.recurringShiftsCollection = opts.recurringShiftsCollection;
                }
            }

            this.mainHeaderContentVisible = 'roles';
        },
        render: function(opts) {
            var self = this,
                roleName = self.roleModel.get("data").name,
                userName = self.model.get("name"),
                email = self.model.get("email"),
                data
            ;

            if (_.isNull(userName) || _.isEmpty(userName) || _.isUndefined(userName)) {
                userName = self.model.get("email");
            }

            data = _.extend({}, self.model.toJSON(), opts, {
                roleName: roleName,
                userName: userName,
            });

            self.$el.html(ich.user_role(data));

            // show schedule preferene card if it's the Boss plan
            if (self.organizationModel.isBoss()) {

                // scheduling preferences / core worker profile
                self.addDelegateView(
                    self.model.get("id") + "-preferences",
                    new Views.SchedulingPreferencesCardView({
                        model: self.model,
                        strings: {
                            title: "Weekly Scheduling Preferences",
                        },
                        template: "user-role",
                    })
                );

                // card for working hours
                self.addDelegateView(
                    self.model.get("id") + "-working-hours",
                    new Views.WorkingHoursCard({
                        el: ".working-hours-card-placeholder",
                        model: self.model,
                        organizationModel: self.organizationModel,
                    })
                );
            }

            self.addDelegateView(
                'danger-zone',
                new Views.DangerZoneCard({
                    description: 'Clicking here will remove ' + userName + ' from ' + roleName + '. You can add ' + userName + ' to another role using ' + email + '.',
                    buttonLabel: 'Delete ' + userName,
                    confirmationMessage: 'Are you sure you want to remove ' + userName + '? Staffjoy retains some data for compliance purposes, such as preserving payroll records.',
                    dangerZoneCallback: self.removeUserFromRole.bind(self),
                })
            );

            self.addDelegateView(
                'recurring-shifts-worker',
                new Views.RecurringShiftsCardView({
                    recurringShiftsCollection: self.recurringShiftsCollection,
                    roleModel: self.roleModel,
                    userModel: self.model,
                    orgModel: self.organizationModel,
                    showDescription: false,
                })
            );

            return this;
        },
        getAction: function() {
            var self = this;

            return {
                label: 'Recurring Shift',
                data: 'recurringShiftCreate',
                callback: function() {
                    $('#manager-header-action .dropdown-toggle').dropdown('toggle')
                    self.delegateViews['recurring-shifts-worker'].editShift(event);
                },
            };
        },
        editProperty: function(e) {
            var self = this,
                $target = $(e.target).closest(".card-element-active"),
                param = $target.attr("data-param"),
                locationId = self.locationId,
                roleId = self.roleId,
                userId = self.model.get("id")
            ;

            e.preventDefault();
            e.stopPropagation();

            Backbone.history.navigate("locations/" + locationId + "/roles/" + roleId + "/users/" + userId + "/preferences/" + param, {trigger: true});
        },
        removeUserFromRole: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target),
                userName = self.model.get("name"),
                roleName = self.roleModel.get("data").name,
                locationId = self.locationId,
                success,
                error
            ;

            $target.addClass("disabled");

            if (_.isNull(userName) || _.isEmpty(userName) || _.isUndefined(userName)) {
                userName = self.model.get("email");
            }

            success = function(collection, response, opts) {
                $.notify({message: "Successfully removed " + userName + " from " + roleName}, {type:"success"});
                Backbone.history.navigate("/locations/" + locationId + "/roles", {trigger: true});
            };

            error = function(collection, response, opts) {
                $.notify({message:"Unable to remove " + userName + " from " + roleName},{type: "danger"});
                $target.removeClass("disabled");
            };

            self.model.destroy({
                success: success,
                error: error,
            });
        },
        sendReminderEmail: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this;

            self.addDelegateView(
                "resend-email-modal",
                new Views.Components.MessageModalView({
                    el: ".email-reminder-modal-placeholder",
                    params: {
                        title: "Resend Confirmation Email",
                        actionStatus: "primary",
                        actionLabel: "Resend Email",
                        message: Util.generateConfirmationEmailModalText(self.model.get("email")),
                    },
                    callback: function() {
                        var success = function(model, response, opts) {
                                $.notify({message: "Success"},{type:"success"});
                            },
                            error = function(model, response, opts) {
                                $.notify({message:ERROR_MESSAGE},{type:"danger"});
                            }
                        ;

                        self.model.save(
                            {activateReminder: true},
                            {
                                success: success,
                                error: error,
                                patch: true,
                            }
                        );
                    },
                })
            );
        },
    });

    root.App.Views.UserRoleView = UserRoleView;

})(this);
