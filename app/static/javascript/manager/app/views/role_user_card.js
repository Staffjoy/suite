(function(root) {

    "use strict";

    var Views = root.App.Views,
        Models = root.App.Models,
        Util = root.App.Util
    ;

    var RoleUserCardView = Views.Base.extend({
        el: "#manage-main .role-users-placeholder",
        events: {
            "click span.card-element.user-info" : "goToUser",
            "click .delete-user" : "deleteUser",
            "click .reminder-email": "sendReminderEmail",
        },
        initialize: function(opts) {
            RoleUserCardView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.locationId)) {
                    this.locationId = opts.locationId;
                }

                if (!_.isUndefined(opts.roleId)) {
                    this.roleId = opts.roleId;
                }

                if (!_.isUndefined(opts.roleName)) {
                    this.roleName = opts.roleName;
                }
            }

            this.mainHeaderContentVisible = 'roles';
        },
        render: function(opts) {
            var self = this,
                data = {data: []},
                userName
            ;

            // really annoying that mustache and backbone don't always play nice
            // needed an array to iterate over
            _.each(self.collection.models, function(model, index, list) {
                userName = model.get("name");

                if (_.isNull(userName) || _.isEmpty(userName) || _.isUndefined(userName)) {
                    userName = model.get("email");
                }

                // don't panic
                data.data.push(_.extend({}, model.toJSON(), {userName: userName}));
            });

            self.$el.append(ich.role_user_card(data));

            return this;
        },
        goToUser: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target).closest(".user-info"),
                userId = $target.attr("data-id"),
                locationId = self.locationId
            ;

            Backbone.history.navigate("locations/" + locationId + "/roles/" + self.roleId + "/users/" + userId, {trigger: true});
        },
        addUserToRole: function(e) {
            e.preventDefault();
            e.stopPropagation();

            Backbone.history.navigate(Backbone.history.getFragment() + "/add-worker", {trigger: true});
        },
        deleteUser: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                locationId = self.locationId,
                $target = $(e.target).closest(".user-info"),
                userId = $target.attr("data-id"),
                userModel = self.collection.get(userId),
                userName = userModel.get("name"),
                roleName = self.roleName,
                success,
                error
            ;

            if (_.isNull(userName) || _.isEmpty(userName) || _.isUndefined(userName)) {
                userName = userModel.get("email");
            }

            success = function(collection, response, opts) {
                $.notify({message: "Successfully removed " + userName + " from " + roleName}, {type:"success"});

                // remove the model from the collection
                self.collection.remove(userId);

                // re render the collection
                $(self.el).empty();
                self.render();
            };

            error = function(collection, response, opts) {
                $.notify({message:"Unable to remove " + userName},{type: "danger"});
            };

            userModel.destroy({
                success: success,
                error: error,
            });
        },
        sendReminderEmail: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target),
                $userTarget = $target.closest(".user-info"),
                userId = parseInt($userTarget.attr("data-id")),
                userModel = self.collection.get(userId)
            ;

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

    root.App.Views.RoleUserCardView = RoleUserCardView;

})(this);
