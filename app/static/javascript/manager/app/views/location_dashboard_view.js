(function(root) {

    "use strict";

    var Views = root.App.Views,
        Models = root.App.Models
    ;

    var LocationDashboardView = Views.Base.extend({
        el: "#manage-main",
        events: {},
        initialize: function(opts) {
            LocationDashboardView.__super__.initialize.apply(this);
            this.mainHeaderContentVisible = "dashboard";

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.locationModel)) {
                    this.locationModel = opts.locationModel;
                }

                if (!_.isUndefined(opts.locationShiftsCollection)) {
                    this.locationShiftsCollection = opts.locationShiftsCollection;
                }

                if (!_.isUndefined(opts.locationTimeclocksCollection)) {
                    this.locationTimeclocksCollection = opts.locationTimeclocksCollection;
                }

                if (!_.isUndefined(opts.locationTimeOffRequestsCollection)) {
                    this.locationTimeOffRequestsCollection = opts.locationTimeOffRequestsCollection;
                }

                if (!_.isUndefined(opts.rolesCollection)) {
                    this.rolesCollection = opts.rolesCollection;
                }
            }
        },
        render: function(opts) {
            var self = this,
                data = {}
            ;

            self.$el.html(ich.location_dashboard_view(data));

            self.addDelegateView(
                'location-dashboard-shifts',
                new Views.LocationDashboardShiftsCardView({
                    locationModel: self.locationModel,
                    locationShiftsCollection: self.locationShiftsCollection,
                    locationTimeclocksCollection: self.locationTimeclocksCollection,
                    locationTimeOffRequestsCollection: self.locationTimeOffRequestsCollection,
                    rolesCollection: self.rolesCollection,
                })
            );

            return this;
        },
        close: function() {
            LocationDashboardView.__super__.close.call(this);
        },
    });

    root.App.Views.LocationDashboardView = LocationDashboardView;

})(this);
