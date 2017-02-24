(function(root) {

    "use strict";

    var Views = root.App.Views,
        Util = root.App.Util
    ;

    var SetDemandCardView = Views.Base.extend({
        el: ".role-demand-card-placeholder",
        events: {},
        initialize: function(opts) {
            SetDemandCardView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {

                if (!_.isUndefined(opts.roleId)) {
                    this.roleId = opts.roleId;
                }

                if (!_.isUndefined(opts.roleName)) {
                    this.roleName = opts.roleName;
                }

                if (!_.isUndefined(opts.weekStartsOn)) {
                    this.weekStartsOn = opts.weekStartsOn;
                }

                if (!_.isUndefined(opts.demandStartMoment)) {
                    this.demandStartMoment = opts.demandStartMoment;
                }

                if (!_.isUndefined(opts.state)) {
                    this.state = opts.state;

                    if (this.state == "queued" || this.state == "processing" || this.state == "done") {
                        this.disabled = true;
                    } else {
                        this.disabled = false;
                    }
                }

                if (!_.isUndefined(opts.previousSchedule)) {
                    this.previousSchedule = opts.previousSchedule;
                }

                if (!_.isUndefined(opts.orgModel)) {
                    this.orgModel = opts.orgModel;
                }

                if (!_.isUndefined(opts.showShiftsCallback)) {
                    this.showShiftsCallback = opts.showShiftsCallback;
                }

                if (!_.isUndefined(opts.renderWeekView)) {
                    this.renderWeekView = opts.renderWeekView;
                }
            }

            this.dayLength = 24;
        },
        close: function() {
            this.$("#demand-" + self.roleId + " .dropdown-selection").off();
            this.$("#demand-" + self.roleId + " .demand-button").off();
            SetDemandCardView.__super__.close.call(this);
        },
        render: function(opts) {
            var self = this,
                data,
                graphData = self.orderDemandDays(),
                graphLabel = self.generateTableLabels(),
                orgModel = self.orgModel,
                minShiftLength = orgModel.get('min_shift_length'),
                maxShiftLength = orgModel.get('max_shift_length'),
                equalShiftLengths = minShiftLength === maxShiftLength
            ;

            data = {
                roleId: self.roleId,
                roleName: self.roleName,
                disabled: self.disabled,
                previousSchedule: self.previousSchedule,
                start: self.model.get('start'),
                isFlex: orgModel.isFlex(),
                equalShiftLengths: equalShiftLengths,
                minShiftLength: minShiftLength,
                maxShiftLength: maxShiftLength,
            };

            if (self.state == "queued" || self.state == "processing") {
                data["message"] = "This schedule is currently being processed - please check back in a few hours";
            }

            self.$el.append(ich.set_demand_card(data));

            self.addDelegateView(
                "spreadsheet",
                new Views.Components.SpreadsheetView({
                    el: ".spreadsheet-placeholder-" + self.roleId,
                    data: graphData,
                    roleId: self.roleId,
                    graphLabel: graphLabel,
                    disabled: self.disabled,
                })
            );

            self.populateDropdownFields();
            self.renderDropdownValues();

            $("#demand-" + self.roleId + " .dropdown-selection").on("click", function(e) {
                self.setShiftLength(e);
            });

            $("#demand-" + self.roleId + " .demand-button").on("click", function(e) {
                switch ($(e.target).data('action')) {
                    case 'copy':
                        self.setPreviousDemand(e);
                        break;
                    case 'calculate':
                        self.calculateNow(e);
                        break;
                    case 'save':
                        self.saveRoleDemandSettings(e);
                        break;
                    case 'discard':
                        self.discard(e);
                        break;
                }
            });

            return this;
        },
        populateDropdownFields: function() {
            var self = this,
                fields = self.$el.find('#demand-' + self.roleId + ' .dropdown'),
                fieldName,
                $input,
                $list,
                unit
            ;

            // iterate through and add list items to each field item
            _.each(fields, function(input, index, list) {
                $input = $(input);
                $list = $input.find(".dropdown-menu");
                fieldName = $input.attr("data-param-name");

                _.each(_.range(1, 24), function(value, index, list) {
                    unit = value === 1 ? "hour" : "hours";
                    $list.append(
                        "<li role='presentation'><a class='dropdown-selection' " +
                        "data-value='" + value + "' role='menuitem'>" +
                        value + " " + unit + "</a></li>"
                    )
                });
            });
        },
        renderDropdownValues: function() {
            var self = this,
                fields = self.$el.find('#demand-' + self.roleId + ' .dropdown'),
                $field,
                fieldName,
                fieldValue,
                unit
            ;

            _.each(fields, function(field, list, index) {
                $field = $(field);
                fieldName = $field.attr("data-param-name");

                // render value into button text
                fieldValue = self.model.get(fieldName);

                if (_.isNull(fieldValue)) {
                    if (fieldName.slice(0, 3) === "min") {
                        fieldValue = 4;
                    } else {
                        fieldValue = 8;
                    }
                }

                unit = fieldValue === 1 ? "hour" : "hours";

                $field.find(".dropdown-value").text(fieldValue + " " + unit);
                $field.find(".dropdown-value").data('value', fieldValue);
            });
        },
        setShiftLength: function(event) {
            var self = this,
                $target = $(event.target),
                $dropdown = $target.closest('.dropdown'),
                $dropdownValue = $dropdown.find('.dropdown-value'),
                counterpart = $dropdownValue.data('counterpart'),
                value = $target.data('value'),
                param = $dropdown.data('param-name'),
                unit = value === 1 ? "hour" : "hours"
            ;

            $dropdownValue.data('value', value);
            $dropdownValue.text(value + ' ' + unit);

            self.checkCounterpart(counterpart, value);
        },
        setShiftLengthData: function(schedule) {
            var self = this,
                fields = self.$el.find('#demand-' + self.roleId + ' .dropdown'),
                $dropdownValue,
                unit,
                data = {},
                $list,
                fieldName,
                $field
            ;

            data.min_shift_length_hour = schedule.get('min_shift_length_hour') || 4;
            data.max_shift_length_hour = schedule.get('max_shift_length_hour') || 8;

            _.each(fields, function(field, index, list) {
                $field = $(field);
                $list = $field.find(".dropdown-menu");
                fieldName = $field.attr("data-param-name");

                if (_.has(data, fieldName) && !_.isNull(data['fieldName'])) {
                    unit = data['fieldName'] === 1 ? 'hour' : 'hours';
                    $field.find(".dropdown-value").text(data[fieldName] + " " + unit);
                    $field.find(".dropdown-value").data('value', data[fieldName]);
                }
            });
        },
        checkCounterpart: function(counterpart, value) {
            var self = this,
                $counterpart = $('#' + counterpart + ' .dropdown-value'),
                counterpartValue = $counterpart.data('value'),
                unit = value === 1 ? "hour" : "hours"
            ;

            if (counterpart === 'min_shift_length_hour' && value < counterpartValue) {
                $counterpart.data('value', value);
                $counterpart.text(value + ' ' + unit);
            } else if (counterpart === 'max_shift_length_hour' && value > counterpartValue) {
                $counterpart.data('value', value);
                $counterpart.text(value + ' ' + unit);
            }
        },
        setPreviousDemand: function(e) {
            var self = this,
                previousDemand = self.previousSchedule.get('demand'),
                spreadsheet = self.delegateViews.spreadsheet
            ;

            if (!_.isNull(previousDemand) && !_.isUndefined(previousDemand)) {
                spreadsheet.setSpreadsheetData(previousDemand);
                self.setShiftLengthData(self.previousSchedule);

                $.notify({ message: "Copied - Click save when finished" }, { type: "info" });
            } else {
                $.notify({ message: "No data found from last week" }, { type: "info" });
            }
        },
        orderDemandDays: function() {
            var self = this,
                demand,
                currentDayMoment = self.demandStartMoment.clone(),
                result = [],
                startIndex,
                order = [
                    "Monday",
                    "Tuesday",
                    "Wednesday",
                    "Thursday",
                    "Friday",
                    "Saturday",
                    "Sunday",
                ],
                j,
                k
            ;

            demand = self.model.get("demand");
            startIndex = order.indexOf(self.weekStartsOn);

            // make sure week start appears in leftmost column, then retain order
            for (j=startIndex; j < order.length; j++) {

                // create empty day of 0's if no demand yet
                if (_.isNull(demand)) {
                    result.push({
                        name: order[j],
                        day: currentDayMoment.format("M/D") ,
                        demand: self.generateDemandArray(),
                    });

                // otherwise extract from model
                } else {
                    result.push({
                        name: order[j],
                        day: currentDayMoment.format("M/D") ,
                        demand: demand[order[j].toLowerCase()],
                    });
                }
                currentDayMoment.add(1, "days");
            }

            // add the days "before" start of week to end
            for (k=0; k < startIndex; k++) {
                if (_.isNull(demand)) {
                    result.push({
                        name: order[k],
                        day: currentDayMoment.format("M/D") ,
                        demand: self.generateDemandArray(),
                    });
                } else {
                    result.push({
                        name: order[k],
                        day: currentDayMoment.format("M/D") ,
                        demand: demand[order[k].toLowerCase()],
                    });
                }
                currentDayMoment.add(1, "days");
            }

            return result;
        },
        generateDemandArray: function() {
            var self = this,
                zeros = [],
                i
            ;

            for (i = 0; i < (self.dayLength); i++) zeros[i] = 0;

            return zeros;
        },
        generateTableLabels: function() {
            var self = this,
                currentTime = moment().minutes(0).seconds(0).hours(0),
                step = 60,
                result = [],
                i
            ;

            for (i = 0; i < self.dayLength; i++) {
                result.push(currentTime.format("h:mm A"));
                currentTime.add(step, "minutes");
            }

            return result;
        },
        getDemandData: function() {
            var self = this;

            return self.delegateViews.spreadsheet.getSpreadsheetData();
        },
        getShiftLengthData: function() {
            var self = this,
                $dropdowns = $("#demand-" + self.roleId + " .dropdown"),
                shiftLengthData = {},
                paramName,
                $value,
                value
            ;

            _.each($dropdowns, function(dropdown) {
                paramName = $(dropdown).data('param-name');
                $value = $(dropdown).find('.dropdown-value');
                value = $value.data('value');
                shiftLengthData[paramName] = value
            });

            return shiftLengthData;
        },
        saveRoleDemandSettings: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target),
                roleName = $target.attr("data-roleId"),
                demandData = self.getDemandData(),
                shiftLengthData = self.getShiftLengthData(),
                success,
                error
            ;

            $target.addClass("disabled");

            success = function(model, response, opts) {
                $target.removeClass("disabled");
                $.notify({message:"Saved demand for " + roleName}, {type:"success"});

                // the demand attr needs to be JSON for request, but an object in model
                model.set("demand", JSON.parse(model.get("demand")));
            };

            error = function(model, response, opts) {
                $target.removeClass("disabled");
                $.notify({message:"Unable to save demand for " + roleName},{type: "danger"});

                // the demand attr needs to be JSON for request, but an object in model
                model.set("demand", JSON.parse(model.get("demand")));
            };

            self.model.save({
                    demand: JSON.stringify(demandData),
                    min_shift_length_hour: shiftLengthData.min_shift_length_hour,
                    max_shift_length_hour: shiftLengthData.max_shift_length_hour,
                },
                {success: success, error: error, patch: true}
            );
        },
        calculateNow: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target),
                roleName = $target.attr("data-roleId"),
                demandData = self.getDemandData(),
                shiftLengthData = self.getShiftLengthData(),
                success,
                error
            ;

            $target.addClass("disabled");

            success = function(model, response, opts) {
                $target.removeClass("disabled");
                $.notify({message:"Starting calculations for " + roleName}, {type:"success"});

                // the demand attr needs to be JSON for request, but an object in model
                if (_.isString(model.get("demand"))) {
                    model.set("demand", JSON.parse(model.get("demand")));
                }

                self.$el.find('#demand-' + self.roleId).hide();

                $(".scheduling-messages").append(ich.scheduling_message({
                    info: true,
                    message: "The schedule for " + roleName + " is being processed. You will receive an email when processing is complete.",
                }));
            };

            error = function(model, response, opts) {
                $target.removeClass("disabled");
                $.notify({message:"Unable to start calculations for " + roleName},{type: "danger"});

                // the demand attr needs to be JSON for request, but an object in model
                if (_.isString(model.get("demand"))) {
                    model.set("demand", JSON.parse(model.get("demand")));
                }
            };

            self.model.save({
                    demand: JSON.stringify(demandData),
                    min_shift_length_hour: shiftLengthData.min_shift_length_hour,
                    max_shift_length_hour: shiftLengthData.max_shift_length_hour,
                    state: 'chomp-queue',
                },
                {success: success, error: error, patch: true}
            );
        },
        discard: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target),
                roleName = $target.attr("data-roleId"),
                success,
                error
            ;

            var success = function(model) {
                self.$el.find('#demand-' + self.roleId).hide();
                $('#wizard-' + self.roleId).show();
                self.showShiftsCallback();
            };

            var error = function(model) {
                $.notify({message:"Unable to discard schedule for for " + roleName},{type: "danger"});
            };

            self.model.save({
                    demand: "",
                }, {
                    success: success,
                    error: error,
                    patch: true,
                }
            );
        },
    });

    root.App.Views.SetDemandCardView = SetDemandCardView;

})(this);
