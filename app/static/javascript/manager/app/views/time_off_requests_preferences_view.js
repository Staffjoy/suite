(function(root) {

    "use strict";

    var Views = root.App.Views,
        Models = root.App.Models
    ;

    var TimeOffRequestPreferencesCardView = Views.Base.extend({
        el: ".time-off-request-placeholder",
        events: {
            "click .adjust-time-off-request-state": "adjust_time_off_request_state",
        },
        initialize: function(opts) {
            TimeOffRequestPreferencesCardView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.el)) {
                    this.el = opts.el;
                }

                if (!_.isUndefined(opts.defaultTimeOffRequest)) {
                    this.defaultTimeOffRequest = opts.defaultTimeOffRequest;
                }
            }
        },
        render: function(opts) {
            var self = this,
                data = {
                    preferences: [],
                    default: self.defaultTimeOffRequest,
                }
            ;

            // unpack out of data structure
            _.each(self.collection.models, function(model, index) {
                if (model.get("roles").length > 0) {
                    data.preferences.push({
                        locationName: model.get("name"),
                        roles: _.map(model.get("roles"), function(roleModel, index) {
                            return {
                                locationId: model.get("id"),
                                roleId: roleModel.id,
                                roleName: roleModel.name,
                                enable_time_off_requests: roleModel.enable_time_off_requests,
                            };
                        }),
                    });
                }
            });

            self.$el.append(ich.time_off_requests_preferences_card(data));

            return this;
        },
        adjust_time_off_request_state: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target),
                $parent = $target.closest(".time-off-request-radio"),
                selectedValue = $target.attr("data-value"),
                selectedValueBoolean = selectedValue === "true",
                currentValue = $parent.attr("data-current-value"),
                locationId = $parent.attr("data-location-id"),
                roleId = $parent.attr("data-role-id"),
                payload,
                model,
                $neighbor,
                success,
                error
            ;

            if (currentValue === selectedValue) {
                return;
            }

            if (selectedValue === "true") {
                $neighbor = $parent.find(".false");
            } else {
                $neighbor = $parent.find(".true");
            }

            if ($parent.hasClass("default-setting")) {
                model = new Models.Organization({id: ORG_ID});
                payload = {enable_time_off_requests_default: selectedValueBoolean};
            } else {
                model = new Models.Role({id: roleId}),
                payload = {enable_time_off_requests: selectedValueBoolean};

                // add upstream model
                model.addUpstreamModel("locationId", locationId);
            }

            success = function(model, response, opts) {
                if (selectedValue === "true") {
                    $target.addClass("active btn-primary").removeClass("btn-default");
                    $neighbor.removeClass("active");
                } else {
                    $neighbor.removeClass("active btn-primary").addClass("btn-default");
                    $target.addClass("active");
                }

                $parent.attr("data-current-value", selectedValue);
            }

            error = function(model, response, opts) {
                $.notify({message:"Unable to save - please contact support"},{type: "danger"});
            };

            model.save(
                payload,
                {
                    success: success,
                    error: error,
                    patch: true,
                }
            );
        },
    });

    root.App.Views.TimeOffRequestPreferencesCardView = TimeOffRequestPreferencesCardView;

})(this);
