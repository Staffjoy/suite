(function(root) {

    "use strict";

    var Util = root.App.Util,
        Views = root.App.Views,
        Models = root.App.Models
    ;

    var AdminsCardView = Views.Base.extend({
        el: "#manage-main .admins-placeholder",
        events: {
            "submit form.add-admin": "addAdmin",
            "click .delete-admin" : "deleteAdmin",
            "click .reminder-email": "sendReminderEmail",
        },
        initialize: function(opts) {
            AdminsCardView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.orgModel)) {
                    this.orgModel = opts.orgModel;
                }
            }
        },
        render: function(opts) {
            var self = this,
                data = {data: []}
            ;

            data.orgName = self.orgModel.get('name');

            // really annoying that mustache and backbone don't always play nice
            // needed an array to iterate over
            _.each(self.collection.models, function(model, index, list) {
                data.data.push(_.extend({}, model.toJSON()));
            });

            self.$el.append(ich.admins_card(data));

            return this;
        },
        addAdmin: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                emailAddress = $("#admin-email").val(),
                adminModel = new Models.Admin(),
                success,
                error
            ;

            // disable the feature
            $(".add-admin-button").attr("disabled", "disabled");

            adminModel.createRequest();

            success = function(model, responde, opts) {
                $.notify({message: "Successfully added " + model.get("email")}, {type:"success"});

                // add the model to the collection
                self.collection.add(model);

                // re render the collection
                $(self.el).empty();
                self.render();
                $("#admin-email").focus();
            };

            error = function(model, response, opts) {
                $(".add-admin-button").removeAttr("disabled");
                $.notify({message:"Unable to add " + emailAddress},{type: "danger"});
            };

            adminModel.save(
                {
                    email: emailAddress
                },
                {
                    success: success,
                    error: error,
                }
            );
        },
        deleteAdmin: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target).closest(".user-info"),
                userId = $target.attr("data-id"),
                userModel = self.collection.get(userId),
                success,
                error
            ;

            success = function(collection, response, opts) {
                $.notify({message: "Successfully removed " + userModel.get("email")}, {type:"success"});

                // remove the model from the collection
                self.collection.remove(userId);

                // re render the collection
                $(self.el).empty();
                self.render();
            };

            error = function(collection, response, opts) {
                $.notify({message:"Unable to remove " + userModel.get("email")},{type: "danger"});
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
                adminId = parseInt($userTarget.attr("data-id")),
                adminModel = self.collection.get(adminId)
            ;

            self.addDelegateView(
                "resend-email-modal",
                new Views.Components.MessageModalView({
                    el: ".email-reminder-modal-placeholder",
                    params: {
                        title: "Resend Confirmation Email",
                        actionStatus: "primary",
                        actionLabel: "Resend Email",
                        message: Util.generateConfirmationEmailModalText(adminModel.get("email")),
                    },
                    callback: function() {
                        var success = function(model, response, opts) {
                                $.notify({message: "Success"},{type:"success"});
                            },
                            error = function(model, response, opts) {
                                $.notify({message:ERROR_MESSAGE},{type:"danger"});
                            }
                        ;

                        adminModel.save(
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

    root.App.Views.AdminsCardView = AdminsCardView;

})(this);
