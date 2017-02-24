(function(root) {

    "use strict";

    var Util = root.App.Util,
        Views = root.App.Views
    ;

    var OrganizationView = Views.Base.extend({
        el: "#euler-container",
        events: {
            "click span.card-element-active": "editProperty",
            "click span.go-to-organization" : "goToOrganization",
        },
        initialize: function(opts) {
            OrganizationView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.plansCollection)) {
                    this.plansCollection = opts.plansCollection;
                }
            }
        },
        render: function() {
            var self = this,
                planId = self.model.get("data").plan,
                data = _.extend(
                    {},
                    self.model.toJSON(),
                    {planName: self.plansCollection.get(planId).get("name")}
                )
            ;

            self.$el.html(ich.organization(data));
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

            Backbone.history.navigate("organizations/" + id + "/edit/" + param, {trigger: true});
        },
        goToOrganization: function(e) {
            var self = this,
                id = self.model.get("id")
            ;

            e.preventDefault();
            e.stopPropagation();

            document.location.href = "/manage/organizations/" + id;
        }
    });

    root.App.Views.OrganizationView = OrganizationView;

})(this);
