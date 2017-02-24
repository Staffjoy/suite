(function(root) {

    "use strict";

    var Views = root.App.Views,
        Models = root.App.Models,
        Collections = root.App.Collections
    ;

    var SchedulingDayShiftsCardView = Views.Base.extend({
        el: ".scheduling-shifts-container",
        events: {},
        initialize: function(opts) {
            SchedulingDayShiftsCardView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.el)) {
                    this.el = opts.el;
                }
                if (!_.isUndefined(opts.startTime)) {
                    this.startTime = opts.startTime;
                }
                if (!_.isUndefined(opts.endTime)) {
                    this.endTime = opts.endTime;
                }
                if (!_.isUndefined(opts.data)) {
                    this.data = opts.data;
                }
                if (!_.isUndefined(opts.locationModel)) {
                    this.locationModel = opts.locationModel;
                }
                if (!_.isUndefined(opts.dayMoment)) {
                    this.dayMoment = opts.dayMoment;
                    this.id = this.dayMoment.format("dddd");
                }
                if (!_.isUndefined(opts.callback)) {
                    this.callback = opts.callback;
                }
            }
            this.dayLength = 24;
            this.renderInterval = 4;
        },
        render: function(opts) {
            var self = this,
                renderData = {
                    title: self.dayMoment.format("dddd, D MMMM YYYY"),
                    id: self.id,
                }
            ;

            self.generateCoverageArrays();

            self.$el.append(ich.scheduling_day_shifts(renderData));

            self.addDelegateView(
                self.id + "-shift-summary",
                new Views.Components.SchedulingGanttGraph({
                    el: "#shift-summary-placeholder-" + self.id,
                    id: self.id + "-shift-summary",
                    modalId: "modal-placeholder-" + self.id,
                    data: self.data,
                    startTime: self.startTime,
                    endTime: self.endTime,
                    locationModel: self.locationModel,
                    dayMoment: self.dayMoment,
                })
            );

            self.addDelegateView(
                self.id + "-coverage",
                new Views.Components.StaffingLevelsGraph({
                    el: "#shift-coverage-placeholder-" + self.id,
                    id: self.id + "-coverage",
                    data: self.data,
                    startTime: self.startTime,
                    endTime: self.endTime,
                })
            );

            // add events for if stuff happens to our collections
            _.each(self.data, function(roleName, index) {
                roleName.shifts.on("add", function(model) {
                    /*var updateRange = false;
                    //if (model.get("start") < self.startTime) {
                        self.startTime = model.get("start");
                        updateRange = true;
                    }
                    if (model.get("start") + model.get("length") > self.endTime) {
                        self.endTime = model.get("start") + model.get("length");
                        updateRange = true;
                    }*/

                    // call update to the shift graph
                    self.delegateViews[self.id + "-shift-summary"].addGraphShift(model);

                    //update the coverage graph
                    self.updateCoverageArray(model.roleName);
                    self.delegateViews[self.id + "-coverage"].updateSeries(model);

                    //if (updateRange) {
                    //    self.delegateViews[self.id + "-shift-summary"].updateRange(self.startTime, self.endTime);
                    //    self.delegateViews[self.id + "-coverage"].updateRange(self.startTime, self.endTime);*/
                    //}
                });

                roleName.shifts.on("sync", function(model) {
                    /*var updateRange = false;
                    if (model.get("start") < self.startTime) {
                        self.startTime = model.get("start");
                        updateRange = true;
                    }
                    if (model.get("start") + model.get("length") > self.endTime) {
                        self.endTime = model.get("start") + model.get("length");
                        updateRange = true;
                    }*/

                    var timezone = self.locationModel.get("timezone"),
                        shiftStartMoment = moment.utc(model.get("start")).tz(timezone),
                        shiftStopMoment = moment.utc(model.get("stop")).tz(timezone),
                        removeFromDay = true,
                        nextDay = self.dayMoment.clone().add(1, "day")
                    ;

                    // check if model should still exist on this day
                    if ((!shiftStartMoment.isBefore(self.dayMoment) &&
                         shiftStartMoment.isBefore(nextDay)) ||
                        (!shiftStopMoment.isBefore(self.dayMoment) &&
                         shiftStopMoment.isBefore(nextDay))
                    ) {

                        // call update to the shift graph
                        self.delegateViews[self.id + "-shift-summary"].updateGraphShift(model);

                        // update the coverage graph
                        self.updateCoverageArray(model.roleName);
                        self.delegateViews[self.id + "-coverage"].updateSeries(model);
                    } else {
                        roleName.shifts.remove(model);
                        self.callback(model);
                    }

                    /*if (updateRange) {
                        self.delegateViews[self.id + "-shift-summary"].updateRange(self.startTime, self.endTime);
                        self.delegateViews[self.id + "-coverage"].updateRange(self.startTime, self.endTime);
                    }*/
                });

                roleName.shifts.on("remove", function(model) {
                    // remove shift from shift summary graph
                    self.delegateViews[self.id + "-shift-summary"].updateGraphShift(model, true);

                    // update the coverage graph
                    self.updateCoverageArray(model.roleName);
                    self.delegateViews[self.id + "-coverage"].updateSeries(model);
                });
            });

            return this;
        },
        generateCoverageArrays: function() {
            var self = this;

            _.each(_.keys(self.data), function(roleName) {
                self.data[roleName]["coverage"] = self.generateCoverageArray(roleName);
            });
        },
        generateCoverageArray: function(roleName) {
            var self = this,
                coverageData = _.range(
                    self.dayLength * self.renderInterval).map(function() {return 0;}),
                timezone = self.locationModel.get("timezone"),
                localStart,
                localStop,
                start,
                stop,
                i
            ;

            _.each(self.data[roleName].shifts.models, function(shift) {
                localStart = moment.utc(shift.get("start")).tz(timezone);
                localStop = moment.utc(shift.get("stop")).tz(timezone);

                start = localStart.hour() * 4 + Math.floor(localStart.minute() / 60 * 4);
                stop = localStop.hour() * 4 + Math.ceil(localStop.minute() / 60 * 4);

                if (localStart.date() !== self.dayMoment.date()) {
                    start = 0;
                }

                if (localStop.date() !== self.dayMoment.date()) {
                    stop = 96;
                }

                for (i = start; i < stop; i++) {
                    coverageData[i] += 1;
                }
            });

            return coverageData;
        },
        updateCoverageArray: function(roleName) {
            var self = this;

            self.data[roleName]["coverage"] = self.generateCoverageArray(roleName);
        },
    });

    root.App.Views.SchedulingDayShiftsCardView = SchedulingDayShiftsCardView;

})(this);
