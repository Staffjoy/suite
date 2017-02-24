(function(root) {

    "use strict";

    var Collections = root.App.Collections,
        Models = root.App.Models,
        Views = root.App.Views,
        Util = root.App.Util
    ;

    var EditLocationManagerModalView = Views.Base.extend({
        el: ".edit-location-manager-modal-placeholder",
        events: {
            "click .delete-location-manager": "deleteLocationManager",
        },
        initialize: function(opts) {
            EditLocationManagerModalView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.managerId)) {
                    this.managerId = opts.managerId;
                }

                if (!_.isUndefined(opts.locationManagerData)) {
                    this.locationManagerData = opts.locationManagerData;
                    this.manager = this.locationManagerData[this.managerId];
                }

                if (!_.isUndefined(opts.locationsCollection)) {
                    this.locationsCollection = opts.locationsCollection;
                }

                if (!_.isUndefined(opts.locationManagersCardView)) {
                    this.locationManagersCardView = opts.locationManagersCardView;
                }
            }
        },
        render: function(opts) {
            var self = this,
                data = {
                    name: self.manager.name,
                    email: self.manager.email,
                    locations: _.chain(self.manager.locations).keys().map(function(locationId) {
                        var locationModel = self.locationsCollection.get(locationId);

                        return {
                            id: locationModel.id,
                            name: locationModel.get('name'),
                        };
                    }).valueOf(),
                }
            ;

            self.$el.html(ich.edit_location_manager_modal(data));
            $("#edit-location-managers-modal").modal();

            $("#edit-location-managers-modal").on("hide.bs.modal", function(e) {
                $('body').removeClass('modal-open');
                self.renderCard();
                self.close();
            });
        },
        close: function() {
            $("#edit-location-managers-modal").off("hidden.bs.modal");

            EditLocationManagerModalView.__super__.close.call(this);
        },
        deleteLocationManager: function(event) {
            event.stopPropagation();

            var self = this,
                $target = $(event.target),
                locationId = $target.data('id'),
                locationManagerModel = new Models.LocationManager({ id: self.manager.id }),
                email = self.manager.email
            ;

            locationManagerModel.addUpstreamModel("locationId", locationId);

            locationManagerModel.destroy({
                success: function() {
                    delete self.manager.locations[locationId];
                    $('#edit-location-manager-row-' + locationId).remove()

                    if (_.keys(self.manager.locations).length === 0) {
                        $('body').removeClass('modal-open');
                        delete self.locationManagerData[self.managerId];
                        self.renderCard();
                    }

                    $.notify({message: "Successfully removed " + email}, {type:"success"});
                },
                error: function() {
                    $.notify({message:"Unable to remove " + email},{type: "danger"});
                },
            });
        },
        renderCard: function() {
            var self = this,
                locationsCollection = new Collections.Locations()
            ;

            locationsCollection.addParam("recurse", true);
            locationsCollection.addParam("archived", false);

            locationsCollection.fetch({
                success: function() {
                    locationsCollection.add(locationsCollection.models.pop().get("data"));

                    self.locationManagersCardView.locationsCollection = locationsCollection;
                    self.locationManagersCardView.render();
                },
            });
        },
    });

    root.App.Views.Components.EditLocationManagerModalView = EditLocationManagerModalView;

})(this);
