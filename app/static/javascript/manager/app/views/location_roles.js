(function(root) {

    "use strict";

    var Util = root.App.Util,
        Models = root.App.Models,
        Views = root.App.Views,
        Collections = root.App.Collections
    ;

    var LocationRolesView = Views.Base.extend({
        el: "#manage-main",
        events: {
            "click .edit-role" : "goToRolePreferences",

            "click .role-users .role-user" : "goToUserRole",
            "click .reminder-email": "sendReminderEmail",
        },
        initialize: function(opts) {
            LocationRolesView.__super__.initialize.apply(this);
            this.mainHeaderContentVisible = "roles";

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.locationId)) {
                    this.locationId = opts.locationId;
                }
            }
        },
        render: function(opts) {
            var self = this,
                RolesCollection = Collections.Base.extend({
                    model: Models.Role,
                }),
                data = {},
                userRoleCollection
            ;

            // check if any roles exist
            if (self.collection.models.length === 0) {
                data["message"] = {
                    type: "info",
                    message: "Create a new role to be scheduled.",
                };
            }

            self.$el.html(ich.location_roles(data));

            _.each(self.collection.models, function(model, index, list) {
                self.addDelegateView(
                    model.get("id"),
                    new Views.LocationRoleCardView({
                        model: model
                    })
                );
            });

            return this;
        },
        getAction: function() {
            var self = this;

            return {
                label: 'Role',
                callback: function() {
                    Backbone.history.navigate("locations/" + self.locationId + "/new-role", {trigger: true});
                },
            };
        },
        goToRolePreferences: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target).closest(".role-card"),
                roleId = $target.attr("data-role"),
                locationId = self.locationId
            ;

            Backbone.history.navigate("locations/" + locationId + "/roles/" + roleId + "/preferences", {trigger: true});
        },
        goToUserRole: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $userTarget = $(e.target).closest(".role-user"),
                userId = $userTarget.attr("data-user-id"),
                $roleTarget = $(e.target).closest(".role-card"),
                roleId = $roleTarget.attr("data-role"),
                locationId = self.locationId
            ;

            Backbone.history.navigate("locations/" + locationId + "/roles/" + roleId + "/users/" + userId, {trigger: true});
        },
        sendReminderEmail: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target),
                $userTarget = $target.closest(".role-user"),
                userId = parseInt($userTarget.attr("data-user-id")),
                $roleTarget = $(e.target).closest(".role-card"),
                roleId = parseInt($roleTarget.attr("data-role")),
                roleModel = self.collection.get(roleId),
                userData = _.findWhere(roleModel.get("users"), {id: userId}),
                userModel = new Models.UserRole({id: userId}),
                workerName
            ;

            // construct model
            userModel.set(userData);
            userModel.addUpstreamModel("locationId", self.locationId);
            userModel.addUpstreamModel("roleId", roleId);

            self.addDelegateView(
                "resend-email-modal",
                new Views.Components.MessageModalView({
                    el: ".email-reminder-modal-placeholder",
                    params: {
                        title: "Resend Confirmation Email",
                        actionStatus: "primary",
                        actionLabel: "Resend Email",
                        message: Util.generateConfirmationEmailModalText(userModel.get("email")),
                    },
                    callback: function() {
                        var success = function(model, response, opts) {
                                $.notify({message: "Success"},{type:"success"});
                            },
                            error = function(model, response, opts) {
                                $.notify({message:ERROR_MESSAGE},{type:"danger"});
                            }
                        ;

                        userModel.save(
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

    root.App.Views.LocationRolesView = LocationRolesView;

})(this);
