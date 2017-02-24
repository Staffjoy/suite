(function(root) {

    "use strict";

    var Collections = root.App.Collections,
        Views = root.App.Views
    ;

    var LocationPreferencesView = Views.Base.extend({
        el: "#manage-main",
        events: {
            "click span.card-element-active": "editProperty",
            "click span.delete-location": "deleteLocation",
        },
        initialize: function(opts) {
            LocationPreferencesView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.orgModel)) {
                    this.orgModel = opts.orgModel;
                }

                if (!_.isUndefined(opts.rootModel)) {
                    this.rootModel = opts.rootModel;
                }

                if (!_.isUndefined(opts.headerView)) {
                    this.headerView = opts.headerView;
                }
            }

            this.mainHeaderContentVisible = "preferences";
        },
        render: function(opts) {
            var self = this,
                data = _.extend({}, self.model.toJSON(), opts)
            ;

            data["timezoneDisplay"] = self.model.get("timezone").replace('_', ' ');

            self.$el.html(ich.location_preferences(data));

            if (self.rootModel.isOrgAdmin()) {
                self.addDelegateView(
                    'danger-zone',
                    new Views.DangerZoneCard({
                        description: 'Clicking here will delete ' + data.name + ' including all of its roles and users.',
                        buttonLabel: 'Delete ' + data.name,
                        confirmationMessage: 'Are you sure you want to delete ' + data.name + '? Staffjoy retains some data for compliance purposes, such as preserving payroll records.',
                        dangerZoneCallback: self.deleteLocation.bind(self),
                    })
                );
            }

            if (self.orgModel.get('data').enterprise_access) {
                self.addDelegateView(
                    "location-manager-card",
                    new Views.LocationManagersLocationCardView({
                        locationModel: self.model,
                        locationManagersCollection: new Collections.LocationManagers(self.model.get('managers')),
                    })
                );
            }

            return this;
        },
        editProperty: function(e) {
            var self = this,
                id = self.model.id,
                $target = $(e.target).closest(".card-element-active"),
                param = $target.attr("data-param")
            ;

            e.preventDefault();
            e.stopPropagation();

            Backbone.history.navigate("/locations/" + id + "/preferences/" + param, {trigger: true});
        },
        deleteLocation: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target),
                locationName = self.model.get("name"),
                success,
                error
            ;

            $target.addClass("disabled");

            success = function(collection, response, opts) {
                $.notify({message: "Successfully deleted " + locationName}, {type:"success"});
                self.headerView.refresh();
                return self.navigate_to_locations();
            };

            error = function(collection, response, opts) {
                $.notify({message:"Unable to delete " + locationName},{type: "danger"});
                $target.removeClass("disabled");
            };

            self.model.destroy({
                success: success,
                error: error,
            });
        },
        navigate_to_locations: function() {
            return Backbone.history.navigate("locations", {trigger: true});
        },
        getAction: function() {
            var self = this;

            if (!self.orgModel.get('data').enterprise_access) {
                return;
            }

            return {
                label: 'Add Location Manager',
                callback: function(event) {
                    self.addDelegateView(
                        "add-location-manager-modal",
                        new Views.Components.AddLocationManagerModalView({
                            locationManagerCardView: self.delegateViews["location-manager-card"],
                        })
                    );
                },
            };
        },
    });

    root.App.Views.LocationPreferencesView = LocationPreferencesView;

})(this);
