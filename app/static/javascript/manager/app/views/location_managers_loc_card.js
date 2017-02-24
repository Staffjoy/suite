(function(root) {

    "use strict";

    var Util = root.App.Util,
        Views = root.App.Views,
        Models = root.App.Models
    ;

    var LocationManagersLocationCardView = Views.Base.extend({
        el: "#manage-main .location-managers-placeholder",
        events: {
            "click .delete-location-manager": "deleteLocationManager",
            "click .reminder-email": "sendReminderEmail",
            "click .add-location-manager": "addLocationManager",
        },
        initialize: function(opts) {
            LocationManagersLocationCardView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.locationModel)) {
                    this.locationModel = opts.locationModel;
                }

                if (!_.isUndefined(opts.locationManagersCollection)) {
                    this.locationManagersCollection = opts.locationManagersCollection;
                }
            }
        },
        render: function(opts) {
            var self = this,
                data = {}
            ;

            data.managers = self.locationManagersCollection.map(function(model) {
                return {
                    id: model.id,
                    name: model.get('name'),
                    email: model.get('email'),
                    active: model.get('active'),
                };
            });

            data.isEmpty = data.managers.length === 0;

            self.$el.html(ich.location_managers_loc_card(data));

            return this;
        },
        sendReminderEmail: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target),
                locationManagerId = parseInt($target.data('id')),
                email = _.findWhere(self.locationModel.get('managers'), { id: locationManagerId }).email,
                locationManagerModel = new Models.LocationManager({ id: locationManagerId })
            ;

            locationManagerModel.addUpstreamModel("locationId", self.locationModel.id);

            self.addDelegateView(
                "resend-email-modal",
                new Views.Components.MessageModalView({
                    el: ".email-reminder-modal-placeholder",
                    params: {
                        title: "Resend Confirmation Email",
                        actionStatus: "primary",
                        actionLabel: "Resend Email",
                        message: Util.generateConfirmationEmailModalText(email),
                    },
                    callback: function() {
                        var success = function(model, response, opts) {
                                $.notify({message: "Success"},{type:"success"});
                            },
                            error = function(model, response, opts) {
                                $.notify({message:ERROR_MESSAGE},{type:"danger"});
                            }
                        ;

                        locationManagerModel.save(
                            {activateReminder: true},
                            {
                                success: success,
                                error: error,
                                patch: true,
                            }
                        );
                    },
                })
            );
        },
        deleteLocationManager: function(event) {
            event.stopPropagation();

            var self = this,
                $target = $(event.target),
                id = $target.data('id'),
                locationManagerModel = self.locationManagersCollection.get(id),
                email = locationManagerModel.get('email')
            ;

            locationManagerModel.addUpstreamModel("locationId", self.locationModel.id);

            locationManagerModel.destroy({
                success: function() {
                    self.locationManagersCollection.remove(id);

                    self.render();

                    $.notify({message: "Successfully removed " + email}, {type:"success"});
                },
                error: function(data) {
                    $.notify({message:"Unable to add " + email},{type: "danger"});
                },
            });
        },
        addLocationManager: function(event) {
            event.stopPropagation();

            var self = this;

            self.addDelegateView(
                "add-location-manager-modal",
                new Views.Components.AddLocationManagerModalView({
                    locationManagerCardView: self,
                })
            );
        }
    });

    root.App.Views.LocationManagersLocationCardView = LocationManagersLocationCardView;

})(this);
