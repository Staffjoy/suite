(function(root) {

    "use strict";

    var Util = root.App.Util,
        Views = root.App.Views,
        Models = root.App.Models
    ;

    var LocationManagersOrganizationCardView = Views.Base.extend({
        el: "#manage-main .location-managers-placeholder",
        events: {
            "click .edit-location-manager": "editLocationManager",
        },
        initialize: function(opts) {
            LocationManagersOrganizationCardView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.locationsCollection)) {
                    this.locationsCollection = opts.locationsCollection;
                }

                if (!_.isUndefined(opts.locationManagerData)) {
                    this.locationManagerData = opts.locationManagerData;
                }
            }
        },
        render: function(opts) {
            var self = this,
                data = {}
            ;

            data.managers = _.map(self.locationManagerData, function(data) {
                return {
                    id: data.id,
                    locations: _.chain(data.locations).keys().map(function(location) {
                        return {
                            id: location,
                            name: self.locationsCollection.get(location).get('name'),
                        };
                    }).valueOf(),
                    name: data.name,
                    email: data.email,
                    locationsList: (function() {
                        var locationIds = _.keys(data.locations),
                            getLocationName = function(locationId) {
                                return self.locationsCollection.get(locationId).get('name');
                            },
                            text = ""
                        ;

                        if (locationIds.length > 4) {
                            var others = locationIds.length - 3;

                            _.each(_.first(locationIds, 3), function(element, index, list) {
                                text += getLocationName(element) + ', ';
                            });

                            text += ' and ' + others + ' others';
                        } else {
                            _.each(locationIds, function(element, index, list) {
                                if (index > 0) {
                                    if (index === locationIds.length - 1) {
                                        if (locationIds.length === 2) {
                                            text += ' and ';
                                        } else {
                                            text += ', and ';
                                        }
                                    } else {
                                        text += ', ';
                                    }
                                }

                                text += getLocationName(element);
                            });
                        }

                        return text;
                    })(),
                };
            });

            if (data.managers.length === 0) {
                data.isEmpty = true;
            }

            self.$el.html(ich.location_managers_org_card(data));

            return this;
        },
        editLocationManager: function(event) {
            event.stopPropagation();

            var self = this,
                $target = $(event.target),
                id = $target.data('id')
            ;

            self.addDelegateView(
                'edit-location-manager-modal',
                new Views.Components.EditLocationManagerModalView({
                    managerId: id,
                    locationManagerData: self.locationManagerData,
                    locationsCollection: self.locationsCollection,
                    locationManagersCardView: self,
                })
            );
        },
    });

    root.App.Views.LocationManagersOrganizationCardView = LocationManagersOrganizationCardView;

})(this);
