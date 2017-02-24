(function(root) {

    "use strict";

    var Util = root.App.Util,
        Views = root.App.Views,
        Models = root.App.Models
    ;

    var AddWorkerView = Views.Base.extend({
        el: "#manage-main",
        events: {
            "click .panel-heading": "return_to_role_preferences",
            "click input.cancel-add-worker" : "return_to_role_preferences",
            "click input.submit-add-worker": "add_worker",
            "click .worker-add .dropdown-selection": "change_selection",
        },
        initialize: function(opts) {
            AddWorkerView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.orgModel)) {
                    this.orgModel = opts.orgModel;
                }
            }

            this.mainHeaderContentVisible = 'roles';
        },
        render: function() {
            var self = this;

            self.$el.html(ich.add_worker({
                isFlex: self.orgModel.isFlex(),
            }));

            self.populateDropdownFields();
            self.renderDropdownValues();

            return this;
        },
        populateDropdownFields: function() {
            var self = this,
                fields = $(".hours-per-workweek .form-group"),
                $input,
                $list
            ;

            // iterate through and add list items to each field item
            _.each(fields, function(input, index, list) {
                $input = $(input);
                $list = $input.find(".dropdown-menu");

                _.each(_.range(0, 169), function(value, index, list) {
                    $list.append(
                        "<li role='presentation'><a class='dropdown-selection' " +
                        "data-value='" + value + "' role='menuitem'>" +
                        value + " hours</a></li>"
                    )
                });

            });
        },
        renderDropdownValues: function() {
            var self = this,
                $minHourField = $('#min_hours_per_workweek'),
                $maxHourField = $('#max_hours_per_workweek')
            ;

            $minHourField.find(".dropdown-value").text("20 hours");
            $maxHourField.find(".dropdown-value").text("40 hours");
        },
        return_to_role_preferences: function(e) {
            var self = this;

            e.preventDefault();
            e.stopPropagation();
            this.undelegateEvents();

            return self.navigate_to_role_preferences();
        },
        navigate_to_role_preferences: function() {
            return Backbone.history.navigate("locations/" + this.model.getUpstreamModelId('locationId') + '/roles/' + this.model.id + '/preferences', {trigger: true});
        },
        change_selection: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target),
                $formgroup = $target.closest(".form-group"),
                attr = $formgroup.attr("data-param-name"),
                value = parseInt($target.attr("data-value")),
                $dropdown = $("#" + attr),
                propertyCounterparts = {
                    min_hours_per_workweek: "max_hours_per_workweek",
                    max_hours_per_workweek: "min_hours_per_workweek",
                },
                $counterartDropdown = $("#" + propertyCounterparts[attr]),
                counterpartValue = parseInt($counterartDropdown.data("value")),
                boundingEnd = attr.substr(0, 3),
                needsCounterpartAdjustment = false;
            ;

            $dropdown.find(".dropdown-value").text(value + " hours");
            $dropdown.data("value", value);

            if (boundingEnd === "min") {
                if (value > counterpartValue) {
                    needsCounterpartAdjustment = true;
                }
            } else if (boundingEnd === "max") {
                if (value < counterpartValue) {
                    needsCounterpartAdjustment = true;
                }
            }

            if (needsCounterpartAdjustment) {
                $counterartDropdown.find(".dropdown-value").text(value + " hours");
                $counterartDropdown.data("value", value);
            }

            $formgroup.find('.dropdown-toggle').dropdown("toggle");
        },
        add_worker: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                locationId = self.model.getUpstreamModelId('locationId'),
                roleId = self.model.id,
                emailAddress = $("#add-worker-email").val(),
                name = $("#add-worker-name").val(),
                minHours = $("#min_hours_per_workweek").data('value'),
                maxHours = $("#max_hours_per_workweek").data('value'),
                userModel = new Models.UserRole(),
                success,
                error,
                payload = {
                    email: emailAddress,
                    min_hours_per_workweek: minHours,
                    max_hours_per_workweek: maxHours,
                }
            ;

            if (!_.isEmpty(name)) {
                payload.name = name;
            }

            // disable the feature
            $(".submit-add-worker").attr("disabled", "disabled");

            // add upstream models
            userModel.addUpstreamModel("locationId", locationId);
            userModel.addUpstreamModel("roleId", roleId);

            userModel.createRequest();

            success = function(model, responde, opts) {
                var userName = model.get("name");

                if (_.isNull(userName) || _.isEmpty(userName) || _.isUndefined(userName)) {
                    userName = model.get("email");
                }

                $.notify({message: "Successfully added " + userName}, {type:"success"});
                return self.navigate_to_role_preferences();
            };

            error = function(model, response, opts) {
                $(".submit-add-worker").removeAttr("disabled");
                $.notify({message:"Unable to add " + emailAddress + " to role"},{type: "danger"});
            };

            userModel.save(
                payload,
                {
                    success: success,
                    error: error,
                }
            );
        },
    });

    root.App.Views.AddWorkerView = AddWorkerView;

})(this);
