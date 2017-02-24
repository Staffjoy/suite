(function(root) {

    "use strict";

    var Util = root.App.Util,
        Views = root.App.Views,
        Models = root.App.Models
    ;

    var OrganizationNewView = Views.Base.extend({
        el: "#euler-container",
        events: {
            "click .panel-heading": "return_to_organizations",
            "click input.cancel-org-create" : "return_to_organizations",
            "click .week-starts-on .dropdown-selection": "selectWeekday",
            "click input.submit-org-create": "create_organization",
        },
        initialize: function() {
            OrganizationNewView.__super__.initialize.apply(this);
            this.dayWeekStarts = "monday";
        },
        render: function() {
            var self = this;

            self.$el.html(ich.organization_new());

            return this;
        },
        return_to_organizations: function(e) {
            var self = this;

            e.preventDefault();
            e.stopPropagation();
            this.undelegateEvents();

            return self.navigate_to_organizations();
        },
        navigate_to_organizations: function() {
            return Backbone.history.navigate("organizations", {trigger: true});
        },
        selectWeekday: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target),
                formvalue = $target.attr("data-value"),
                $formgroup = $(".form-group.week-starts-on"),
                $formtext = $formgroup.find(".dropdown-value")
            ;

            self.dayWeekStarts = formvalue;
            $formtext.text(formvalue);
            $formgroup.find('.dropdown-toggle').dropdown("toggle");
        },
        create_organization: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                newOrgModel = new Models.Organization(),
                orgName,
                success,
                error
            ;

            newOrgModel.createRequest();

            success = function(collection, response, opts) {
                $.notify({message: "Successfully created " + orgName}, {type:"success"});
                return self.navigate_to_organizations();
            };
            error = function(collection, response, opts) {
                $.notify({message:"Unable to create " + orgName},{type: "danger"});
                return self.navigate_to_organizations();
            };

            orgName = $("#organization-new-name").val();

            if (!newOrgModel.isNew() || _.isEmpty(orgName)) {
                return error();
            }

            newOrgModel.save(
                {
                    name: orgName,
                    day_week_starts: self.dayWeekStarts
                },
                {success: success, error: error}
            );
        },
    });

    root.App.Views.OrganizationNewView = OrganizationNewView;

})(this);
