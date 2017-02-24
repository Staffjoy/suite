(function(root) {

    "use strict";

    var Views = root.App.Views;

    var SchedulingPreferencesCardView = Views.Base.extend({
        el: ".scheduling-preferences-placeholder",
        events: {
            "click .scheduling-preferences .dropdown-selection": "saveSchedulingPreference",
            "change .checkbox .boolean-toggle": "saveBooleanPreference",
        },
        initialize: function(opts) {
            SchedulingPreferencesCardView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {

                this.strings = opts.strings || {};

                if (!_.isUndefined(opts.el)) {
                    this.el = opts.el;
                }

                if (!_.isUndefined(opts.template)) {
                    this.template = opts.template;
                }
            }
        },
        render: function(opts) {
            var self = this,
                data
            ;

            data = _.extend({}, self.model.toJSON(), opts, {
                uniqueId: self.template,
                strings: self.strings,
            });

            // render the appropriate template
            switch(self.template) {
                case "org-preferences":
                    self.$el.html(ich.scheduling_org_preferences_card(data));
                    break;

                case "user-role":
                    self.$el.html(ich.scheduling_user_role_preferences_card(data));
                    break;

                case "role-preferences":
                    self.$el.html(ich.scheduling_role_preferences_card(data));
                    break;
            }

            // related to the dropdown fields
            self.populateDropdownFields();
            self.renderDropdownValues();

            // related to checkbox fields
            self.populateCheckboxFields();

            return this;
        },
        populateCheckboxFields: function() {
            var self = this,
                checkboxes = $(".scheduling-preferences." + self.template + " .checkbox"),
                fieldName,
                $checkbox
            ;

            // iterate through all checkboxes
            _.each(checkboxes, function(checkbox, index) {
                $checkbox = $(checkbox);
                fieldName = $checkbox.find(".boolean-toggle").attr("data-param-name");

                // set whether checked or not
                if (self.model.get(fieldName)) {
                    $checkbox.find("#" + fieldName).prop("checked", true);
                } else {
                    $checkbox.find("#" + fieldName).prop("checked", false);
                }
            });
        },
        populateDropdownFields: function() {
            var self = this,
                fields = $(".scheduling-preferences." + self.template + " .form-group"),
                fieldName,
                $input,
                $list
            ;

            // iterate through and add list items to each field item
            _.each(fields, function(input, index, list) {
                $input = $(input);
                $list = $input.find(".dropdown-menu");
                fieldName = $input.attr("data-param-name");

                _.each(self.getValueRangeArray(fieldName), function(value, index, list) {
                    $list.append(
                        "<li role='presentation'><a class='dropdown-selection' " +
                        "data-value='" + value + "' role='menuitem'>" +
                        value + " " + self.numericPhraser(fieldName, value) + "</a></li>"
                    )
                });

            });
        },
        renderDropdownValues: function() {
            var self = this,
                fields = $(".scheduling-preferences." + self.template + " .form-group"),
                $field,
                fieldName,
                fieldValue
            ;

            _.each(fields, function(field, list, index) {
                $field = $(field);
                fieldName = $field.attr("data-param-name");

                // render value into button text
                fieldValue = self.model.get(fieldName);
                $field.find(".dropdown-value").text(fieldValue + " " + self.numericPhraser(fieldName, fieldValue));
            });
        },
        // only positive numbers
        numericPhraser: function(name, number) {

            var wordTree = {
                    "demand_opens_days_before_start" : "day",
                    "availability_closes_days_before_start" : "day",
                    "min_hours_per_workweek" : "hour",
                    "max_hours_per_workweek" : "hour",
                    "min_hours_per_workday" : "hour",
                    "max_hours_per_workday" : "hour",
                    "min_hours_between_shifts" : "hour",
                    "max_consecutive_workdays" : "day",
                    "shifts_assigned_days_before_start" : "day",
                },
                result = wordTree[name]
            ;

            if (number != 1) {
                return result + "s";
            }

            return result;
        },
        getValueRangeArray: function(attr) {
            var tree = {
                    "demand_opens_days_before_start" : [1, 100],
                    "availability_closes_days_before_start" : [1, 100],
                    "min_hours_per_workweek" : [0, 168],
                    "max_hours_per_workweek" : [0, 168],
                    "min_hours_per_workday" : [1, 24],
                    "max_hours_per_workday" : [1, 24],
                    "min_hours_between_shifts" : [0, 24],
                    "max_consecutive_workdays" : [4, 13],
                    "shifts_assigned_days_before_start" : [1, 90],
                },
                result = tree[attr]
            ;

            return _.range(result[0], result[1] + 1);
        },
        saveSchedulingPreference: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target),
                $formgroup = $target.closest(".form-group"),
                attr = $formgroup.attr("data-param-name"),
                value = parseInt($target.attr("data-value")),
                data = {},
                errorMessage = "Unable to save",
                organizationCounterparts = {
                    demand_opens_days_before_start: "availability_closes_days_before_start",
                    availability_closes_days_before_start: "demand_opens_days_before_start",
                },
                propertyCounterparts = {
                    min_hours_per_workweek: "max_hours_per_workweek",
                    max_hours_per_workweek: "min_hours_per_workweek",
                    min_hours_per_workday: "max_hours_per_workday",
                    max_hours_per_workday: "min_hours_per_workday",
                },
                $counterpart,
                counterpartAttr,
                counterpartValue,
                boundingEnd = attr.substr(0, 3),  // gets "min" or "max"
                needsCounterpartAdjustment = false,
                success,
                error = function(collection, response, opts) {
                    $.notify({message: errorMessage},{type: "danger"});
                    $formgroup.find('.dropdown-toggle').dropdown("toggle");
                }
            ;

            // do nothing if the selection is the same as the current
            if (self.model.get(attr) == value) {
                $formgroup.find('.dropdown-toggle').dropdown("toggle");
                return;
            }

            data[attr] = value;

            if (self.template === "org-preferences" && _.has(organizationCounterparts, attr)) {

                counterpartAttr = organizationCounterparts[attr];
                $counterpart = $("#" + counterpartAttr);
                counterpartValue = self.model.get(counterpartAttr);

                if (attr === "availability_closes_days_before_start" && value >= counterpartValue) {
                    errorMessage = "Schedules creation occurs after the manager sets demand (less than " + counterpartValue + " days)";
                    return error();
                }

                else if (attr === "demand_opens_days_before_start" && value <= counterpartValue) {
                    errorMessage = "Demand must be set before the schedule can be created (greater than " + counterpartValue + " days)";
                    return error();
                }
            }

            // for default card
            else if (_.has(propertyCounterparts, attr)) {

                // get counterpart value
                counterpartAttr = propertyCounterparts[attr];
                $counterpart = $("#" + counterpartAttr);
                counterpartValue = self.model.get(counterpartAttr);

                if (boundingEnd === "min") {
                    if (value > counterpartValue) {
                        needsCounterpartAdjustment = true;
                    }
                } else if (boundingEnd === "max") {
                    if (value < counterpartValue) {
                        needsCounterpartAdjustment = true;
                    }
                } else {
                    console.log("unknown boundingEnd value");
                }
            }

            if (needsCounterpartAdjustment) {
                counterpartValue = value;
                data[counterpartAttr] = counterpartValue;
            }

            success = function(collection, response, opts) {
                $.notify({message: "Saved"}, {type:"success"});

                // make sure the model is updated
                self.model.set(attr, value);

                // update the text on that selector
                $formgroup.find(".dropdown-value").text(value + " " + self.numericPhraser(attr, value));

                // was opposing value adjusted
                if (needsCounterpartAdjustment) {
                    $counterpart.find(".dropdown-value").text(counterpartValue + " " + self.numericPhraser(counterpartAttr, counterpartValue));
                    self.model.set(counterpartAttr, counterpartValue);
                }

                // close the dropdown window
                $formgroup.find('.dropdown-toggle').dropdown("toggle");
            };

            self.model.save(
                data,
                {
                    success: success,
                    error: error,
                    patch: true,
                }
            );
        },
        saveBooleanPreference: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target),
                checked = $target.prop("checked"),
                param = $target.closest(".boolean-toggle").attr("data-param-name"),
                data = {},
                success,
                error
            ;

            success = function(collection, response, opts) {
                $.notify({message: "Saved"}, {type:"success"});

                // make sure the model is updated
                self.model.set(param, checked);
            };

            error = function(collection, response, opts) {
                $.notify({message:"Unable to save"},{type: "danger"});
            };

            data[param] = checked;

            self.model.save(
                data,
                {
                    success: success,
                    error: error,
                    patch: true,
                }
            );
        },
    });

    root.App.Views.SchedulingPreferencesCardView = SchedulingPreferencesCardView;

})(this);
