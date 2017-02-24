(function(root) {

    "use strict";

    var Util = root.App.Util,
        Views = root.App.Views
    ;

    var UserView = Views.Base.extend({
        el: "#euler-container",
        events: {
            "click span.card-element-active": "editProperty",
            "click .to-org": "toOrg",
            "click span.go-to-planner" : "toPlanner",
            "click #activation-reminder" : "sendReminderEmail",
        },
        initialize: function() {
            UserView.__super__.initialize.apply(this);
        },
        render: function() {
            var self = this;

            self.$el.html(ich.user(self.model.toJSON()));
            return this;
        },
        editProperty: function(e) {
            var self = this,
                id = self.model.get("id"),
                $target = $(e.target).closest(".card-element-active"),
                param = $target.attr("data-param")
            ;

            e.preventDefault();
            e.stopPropagation();

            Backbone.history.navigate("users/" + id + "/edit/" + param, {trigger: true});
        },
        toOrg: function(e) {
            var self = this,
                $target = $(e.target).closest(".to-org"),
                orgId = $target.attr("data-org")
            ;

            e.preventDefault();
            e.stopPropagation();

            Backbone.history.navigate("organizations/" + orgId, {trigger: true});
        },
        toPlanner: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target).closest(".go-to-planner"),
                orgId = $target.attr("data-organization-id"),
                locationId = $target.attr("data-location-id"),
                roleId = $target.attr("data-role-id"),
                userId = self.model.get("id")
            ;

            document.location.href = "/planner/organizations/" + orgId + "/locations/" + locationId + "/roles/" + roleId + "/users/" + userId;
        },
        sendReminderEmail: function(e) {
            e.preventDefault();
            e.stopPropagation();

            this.model.save(
                {activateReminder: true},
                {
                    success: function() {
                        $.notify({message:"Success"},{type:"success"});
                    },
                    error: function() {
                        $.notify({message:"Unable to dispatch an email"},{type:"danger"});
                    },
                    patch: true,
                }
            );
        },
    });

    root.App.Views.UserView = UserView;

})(this);
