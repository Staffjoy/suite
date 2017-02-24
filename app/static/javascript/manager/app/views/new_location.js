(function(root) {

    "use strict";

    var Util = root.App.Util,
        Views = root.App.Views,
        Models = root.App.Models
    ;

    var NewLocationView = Views.Base.extend({
        el: "#manage-main",
        events: {
            "click .panel-heading": "return_to_locations",
            "click input.cancel-location-create" : "return_to_locations",
            "click input.submit-location-create": "create_location",
        },
        initialize: function(opts) {
            NewLocationView.__super__.initialize.apply(this);
            this.TopNavView = "locations";
            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.timezonesCollection)) {
                    this.timezonesCollection = opts.timezonesCollection;
                }

                if (!_.isUndefined(opts.headerView)) {
                    this.headerView = opts.headerView;
                }
            }
        },
        render: function() {
            var self = this;

            self.$el.html(ich.new_location());

            self.renderTimezoneDropdown();

            return this;
        },
        renderTimezoneDropdown: function() {
            var self = this,
                tzDetect = jstz.determine(),
                tzName = tzDetect.name(),
                $timezoneSelect = $(".select-timezone"),
                exists,
                iteratee = function(value, index) {
                    var name = value.get('name'),
                        selected = tzName === name,
                        formattedName = name.replace('_', ' ')
                    ;

                    return { id: name, text: formattedName, selected: selected };
                },
                data = self.timezonesCollection.map(iteratee)
            ;

            // make sure detected timezone exists in our API
            exists = self.timezonesCollection.where({name: tzName}).length > 0;

            // make timezone name be UTC if detector didn't work
            tzName = exists ? tzName : "UTC";

            // set timezone value into dropdown
            $timezoneSelect.select2({ data: data });
        },
        return_to_locations: function(e) {
            var self = this;

            e.preventDefault();
            e.stopPropagation();
            this.undelegateEvents();

            return self.navigate_to_locations();
        },
        navigate_to_locations: function() {
            return Backbone.history.navigate("locations", {trigger: true});
        },
        create_location: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                locationName,
                currentTimezone = $(".select-timezone option:selected").val(),
                success,
                error,
                exists
            ;

            // likely unnecessary but just be careful to never send a timezone that doesn't exists through API
            exists = self.timezonesCollection.where({name: currentTimezone}).length > 0;
            currentTimezone = exists ? currentTimezone : "UTC";

            self.model.createRequest();

            success = function(collection, response, opts) {
                $.notify({message: "Successfully created " + locationName}, {type:"success"});
                self.headerView.refresh();
                return self.navigate_to_locations();
            };
            error = function(collection, response, opts) {
                $.notify({message:"Unable to create " + locationName},{type: "danger"});
                return self.navigate_to_locations();
            };

            locationName = $("#location-new-name").val();

            if (!self.model.isNew() || _.isEmpty(locationName)) {
                return error();
            }

            self.model.save(
                {
                    name: locationName,
                    timezone: currentTimezone
                },
                {success: success, error: error}
            );
        },
    });

    root.App.Views.NewLocationView = NewLocationView;

})(this);
