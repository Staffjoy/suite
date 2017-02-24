(function(root) {

    "use strict";

    var Models = root.App.Models,
        Views = root.App.Views,
        Util = root.App.Util
    ;

    var AddLocationManagerModalView = Views.Base.extend({
        el: ".add-location-manager-modal-placeholder",
        events: {
            'click .add-location-manager-button': 'addLocationManager',
        },
        initialize: function(opts) {
            AddLocationManagerModalView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.locationManagerCardView)) {
                    this.locationManagerCardView = opts.locationManagerCardView;
                }
            }
        },
        render: function(opts) {
            var self = this,
                data = {},
                $modal
            ;

            self.$el.html(ich.add_location_manager_modal(data));

            $modal = $("#add-location-manager-modal");

            $modal.modal();

            $modal.on("hidden.bs.modal", function(e) {
                $('body').removeClass('modal-open');
                self.close();
            });

            self.$modal = $modal;
        },
        close: function() {
            var self = this;

            self.$modal.off("hidden.bs.modal");
            AddLocationManagerModalView.__super__.close.call(this);
        },
        addLocationManager: function(event) {
            event.stopPropagation();

            var self = this,
                emailAddress = $("#location-manager-email").val(),
                name = $("#location-manager-name").val(),
                locationManagerModel = new Models.LocationManager(),
                success,
                error
            ;

            // disable the feature
            $(".add-location-admin-button").attr("disabled", "disabled");

            $("#add-location-manager-modal").modal('hide');

            locationManagerModel.addUpstreamModel('locationId', self.locationManagerCardView.locationModel.id);
            locationManagerModel.createRequest();

            success = function(model, response, opts) {
                locationManagerModel.set(response);
                self.locationManagerCardView.locationManagersCollection.add(locationManagerModel);

                self.locationManagerCardView.locationModel.fetch({
                    success: function(model, response, opts) {
                        var data = model.get('data');

                        self.locationManagerCardView.locationModel.unset('data');
                        self.locationManagerCardView.locationModel.set(data);
                        self.locationManagerCardView.render();
                    },
                });

                $.notify({message: "Successfully added " + model.get("email")}, {type:"success"});
            };

            error = function(model, response, opts) {
                $(".add-location-manager-button").removeAttr("disabled");
                $.notify({message:"Unable to add " + emailAddress},{type: "danger"});
                $("#add-location-manager-modal").modal('hide');
            };

            locationManagerModel.save(
                {
                    email: emailAddress,
                    name: name,
                },
                {
                    success: success,
                    error: error,
                }
            );
        },
    });

    root.App.Views.Components.AddLocationManagerModalView = AddLocationManagerModalView;

})(this);
