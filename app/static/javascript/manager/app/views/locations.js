(function(root) {

    "use strict";

    var Views = root.App.Views;

    var LocationsView = Views.Base.extend({
        el: "#manage-main",
        events: {
            "click .view-location": "goToLocation",
            "click .location-role" : "goToLocationRoleEdit",
        },
        initialize: function(opts) {
            LocationsView.__super__.initialize.apply(this);
            this.topNavVisible = "locations";
            this.mainHeaderContentVisible = "locations";

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.rootModel)) {
                    this.rootModel = opts.rootModel;
                }
            }
        },
        render: function(opts) {
            var self = this,
                data = self.rootModel.isOrgAdmin() ? _.extend({}, {
                    data: self.collection.map(function(model) {
                        return model.attributes;
                    })
                }, opts) : {
                    data: _.chain(self.rootModel.get('access').location_manager).where({
                        organization_id: parseInt(ORG_ID)
                    }).map(function(data) {
                        return self.collection.get(data.location_id).attributes;
                    }).valueOf()
                }
            ;

            if (self.collection.models.length === 0) {
                data["message"] = {
                    type: "info",
                    message: "Create a new location to be scheduled.",
                }
            }

            self.$el.html(ich.locations(data));

            return this;
        },
        getAction: function() {
            var self = this;

            if (!self.rootModel.isOrgAdmin()) {
                return;
            }

            return {
                label: 'Location',
                callback: function() {
                    Backbone.history.navigate("new-location", {trigger: true});
                },
            };
        },
        goToLocation: function(e) {
            var self = this,
                $target = $(e.target).closest(".location-card"),
                locationId = $target.attr("data-location")
            ;

            e.preventDefault();
            e.stopPropagation();

            Backbone.history.navigate("locations/" + locationId, {trigger: true});
        },
        goToLocationRoleEdit: function(e) {
            var self = this,
                $locationTarget = $(e.target).closest(".location-card"),
                locationId = $locationTarget.attr("data-location"),
                $roleTarget = $(e.target).closest(".location-role"),
                roleId = $roleTarget.attr("data-role-id")
            ;

            e.preventDefault();
            e.stopPropagation();

            Backbone.history.navigate("locations/" + locationId + "/roles/" + roleId + "/preferences", {trigger: true});
        },
    });

    root.App.Views.LocationsView = LocationsView;

})(this);
