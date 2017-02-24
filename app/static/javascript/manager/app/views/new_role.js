(function(root) {

    "use strict";

    var Util = root.App.Util,
        Views = root.App.Views,
        Models = root.App.Models
    ;

    var NewRoleView = Views.Base.extend({
        el: "#manage-main",
        events: {
            "click .panel-heading": "return_to_roles",
            "click input.cancel-role-create" : "return_to_roles",
            "click input.submit-role-create": "create_role",
        },
        initialize: function(opts) {
            NewRoleView.__super__.initialize.apply(this);
            this.mainHeaderContentVisible = "roles";
            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.model)) {
                    this.model = opts.model;
                }
                if (!_.isUndefined(opts.locationId)) {
                    this.locationId = opts.locationId;
                }
            }
        },
        render: function() {
            var self = this;

            self.$el.html(ich.new_role());

            return this;
        },
        return_to_roles: function(e) {
            var self = this;

            e.preventDefault();
            e.stopPropagation();
            this.undelegateEvents();

            return self.navigate_to_roles();
        },
        navigate_to_roles: function() {
            var self = this,
                locationId = self.locationId
            ;

            return Backbone.history.navigate("locations/" + locationId + "/roles", {trigger: true});
        },
        create_role: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                roleName = $("#role-new-name").val(),
                success,
                error
            ;

            success = function(collection, response, opts) {
                $.notify({message: "Successfully created " + roleName}, {type:"success"});
                return self.navigate_to_roles();
            };

            error = function(collection, response, opts) {
                $.notify({message:"Unable to create " + roleName},{type: "danger"});
                return self.navigate_to_roles();
            };

            if (_.isUndefined(self.model)) {
                return error();
            }

            self.model.createRequest();

            if (!self.model.isNew() || _.isEmpty(roleName)) {
                return error();
            }

            self.model.save(
                {name: roleName},
                {success: success, error: error}
            );
        },
    });

    root.App.Views.NewRoleView = NewRoleView;

})(this);
