(function(root) {

    "use strict";

    var Util = root.App.Util,
        Views = root.App.Views
    ;

    var OrganizationsView = Views.Base.extend({
        el: "#euler-container",
        initialize: function(opts) {
            OrganizationsView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.page)) {
                    this.page = parseInt(opts.page);
                }

                if (!_.isUndefined(opts.plansCollection)) {
                    this.plansCollection = opts.plansCollection;
                }
            }
        },
        events: {
            "click tr.org-row": "showOrganization",
            "click .pagination .previous": "previousPage",
            "click .pagination .next": "nextPage",
            "click .euler-table-action-btn": "createNewOrganization",
        },
        render: function(opts) {
            var self = this,
                data
            ;

            _.each(self.collection.models[0].get("data"), function(object, index) {
                object["planName"] = self.plansCollection.get(object.plan).get("name");
            });

            data = _.extend({}, self.collection.toJSON()[0], opts);

            self.$el.html(ich.organizations(data));
            return this;
        },
        showOrganization: function(e) {
            var $target = $(e.target).parent("tr.org-row"),
                id = $target.attr("data-id")
            ;

            e.preventDefault();
            e.stopPropagation();

            Backbone.history.navigate("organizations/" + id, {trigger:true});
        },
        previousPage: function(e) {
            var self = this;

            e.preventDefault();
            e.stopPropagation();

            Backbone.history.navigate("organizations/page/" + (self.page-1), {trigger:true});
        },
        nextPage: function(e) {
            var self = this;

            e.preventDefault();
            e.stopPropagation();

            Backbone.history.navigate("organizations/page/" + (self.page+1), {trigger:true});
        },
        createNewOrganization: function(e) {
            e.preventDefault();
            e.stopPropagation();

            Backbone.history.navigate("new-organization", {trigger: true});
        },
    });

    root.App.Views.OrganizationsView = OrganizationsView;

})(this);
