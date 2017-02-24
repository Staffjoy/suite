(function(root) {

    "use strict";

    var Views = root.App.Views,
        Util = root.App.Util,
        Collections = root.App.Collections,
        Models = root.App.Models
    ;

    var SchedulingWeekShiftsView = Views.Base.extend({
        el: ".scheduling-shifts-container",
        events: {},
        initialize: function(opts) {
            SchedulingWeekShiftsView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.el)) {
                    this.el = opts.el;
                }

                if (!_.isUndefined(opts.orgModel)) {
                    this.orgModel = opts.orgModel;
                }

                if (!_.isUndefined(opts.locationModel)) {
                    this.locationModel = opts.locationModel;
                }

                if (!_.isUndefined(opts.shifts)) {
                    this.shifts = opts.shifts;
                }

                if (!_.isUndefined(opts.currentWeek)) {
                    this.currentWeek = opts.currentWeek;
                }

                if (!_.isUndefined(opts.scheduleModels)) {
                    this.scheduleModels = opts.scheduleModels;
                }

                if (!_.isUndefined(opts.rolesCollection)) {
                    this.rolesCollection = opts.rolesCollection;
                }
            }

            this.weekLength = 7;
            this.views = [];
            this.lazyLoadFunction = lazyLoadFunction.bind(this);
            this.startTime = 0;
            this.endTime = 24;
            this.$newShiftButton;
        },
        close: function() {
            $(".new-shift").off();
            $("#modal-placeholder-new").empty();
            window.removeEventListener('scroll', this.lazyLoadFunction);
            Views.Base.prototype.close.call(this);
        },
        getAction: function() {
            var self = this,
                action = {
                    label: 'Shift',
                    callback: function(event) {
                        self.openNewShiftModal(event);
                    },
                },
                roles
            ;

            roles = self.rolesCollection.map(function(model) {
                return {
                    label: model.get('name'),
                    id: model.id,
                };
            });

            if (roles.length === 1) {
                action.data = _.first(roles).id;
            } else if (roles.length > 1) {
                action.data = roles;
            }

            return action;
        },
        render: function(opts) {
            var self = this,
                scheduleDays = self.getDayDataFromSchedules()
            ;

            self.$newShiftButton = $("#new-shift-button");
            self.$newShiftButton.removeClass("hidden");

            _.chain(scheduleDays).sortBy(function(day) {
                return day.date.format('YYYY-MM-DD');
            }).each(function(day) {
                self.views.push({
                    id: day.date.format("dddd-D"),
                    view: new Views.SchedulingDayShiftsCardView({
                        data: day.roles,
                        dayMoment: day.date,
                        startTime: self.startTime,
                        endTime: self.endTime,
                        locationModel: self.locationModel,
                        callback: function(shiftModel) {
                            self.sendShiftToView(shiftModel);
                        },
                    })
                });
            });

            window.addEventListener('scroll', this.lazyLoadFunction);
            window.dispatchEvent(new Event('scroll'));

            // add event for new shift button
            // uses dynamic id so backbone event feature doesn't play nice
            $(".new-shift").click(function(e) {
                self.openNewShiftModal(e);
            });

            return this;
        },
        getDayDataFromSchedules: function() {
            var self = this,
                result = [],
                timezone = self.locationModel.get("timezone"),
                weekStartMoment = moment.tz(self.currentWeek, timezone),
                segmentedShifts = self.segmentShiftsByDay(),
                currentDateMoment,
                dayData,
                j
            ;

            // order by week starts on
            for (j=0; j < self.weekLength; j++) {
                currentDateMoment = weekStartMoment.clone().add("days", j);
                dayData = {
                    date: currentDateMoment,
                    roles: {}
                };

                _.each(_.keys(segmentedShifts), function(roleName) {
                    dayData.roles[roleName] = {
                        "shifts": segmentedShifts[roleName][j].shifts,
                        "roleName": roleName,
                        "models": {
                            "locationId": self.locationModel.id,
                            "roleId": segmentedShifts[roleName][j].roleId,
                        },
                    };
                });

                result.push(dayData);
            }

            return result;
        },
        segmentShiftsByDay: function() {
            /* all timezone comparisons are going to be done in local time */

            var self = this,
                timezone = self.locationModel.get("timezone"),
                weekStartMoment = moment.tz(self.currentWeek, timezone),
                weekStopMoment = weekStartMoment.clone().add("days", 7),
                result = {},
                k
            ;

            // result[roleName] = [day1, day2, day3, etc.]

            // for each role
            _.each(self.shifts, function(shiftsCollection) {
                var roleShiftData = {},
                    currentDate,
                    roleName = shiftsCollection.roleName,
                    roleId = shiftsCollection.getUpstreamModelId("roleId")
                ;

                // roleShiftData is a dict indexed by date - so we can push shifts into proper local date
                // NOTE: we are using a collection here so that we can listen to changes to our shifts
                // to access stuff downstream, just use collection.models
                for (k=0; k < self.weekLength; k++) {
                    currentDate = weekStartMoment.clone().add("days", k);
                    roleShiftData[currentDate.format("YYYY-MM-DD")] = {
                        shifts: new Backbone.Collection(),
                        momentDate: currentDate,
                        roleId: roleId,
                    };
                }

                // iterate through shifts and add them to proper day
                _.each(shiftsCollection.models, function(shiftModel) {
                    var shiftStartLocalMoment = moment.utc(shiftModel.get("start")).tz(timezone),
                        shiftStopLocalMoment = moment.utc(shiftModel.get("stop")).tz(timezone),
                        stopsAfterMidnight = (shiftStopLocalMoment.hours() +
                                             shiftStopLocalMoment.minutes() +
                                             shiftStopLocalMoment.seconds() +
                                             shiftStopLocalMoment.milliseconds()) > 0
                    ;

                    // check if shift is split across multiple days but make sure
                    // that it doesn't get added to dates that don't occurr in the current week
                    if (shiftStartLocalMoment.date() !== shiftStopLocalMoment.date() && stopsAfterMidnight) {
                        if (shiftStopLocalMoment.isBefore(weekStopMoment)) {
                            roleShiftData[shiftStopLocalMoment.format("YYYY-MM-DD")].shifts.add(shiftModel);
                        }
                    }

                    // using ! .isBefore to get inclusive for case where start == weekStart
                    if (!shiftStartLocalMoment.isBefore(weekStartMoment)) {
                        roleShiftData[shiftStartLocalMoment.format("YYYY-MM-DD")].shifts.add(shiftModel);
                    }
                });

                // bundle roleShiftData into correct order
                result[roleName] = _.values(roleShiftData).sort(function(a, b) {
                    if (a.momentDate.isBefore(b.momentDate)) {
                        return -1;
                    } else {
                        return 1;
                    }
                });
            });

            return result
        },
        openNewShiftModal: function(event) {
            event.preventDefault();
            event.stopPropagation();

            var self = this,
                $target = $(event.target),
                roleId = $target.data('id'),
                roleName = self.rolesCollection.get(roleId).get('name'),
                newShiftModel = new Models.Shift(),
                eligibleUsersCollection = new Collections.ShiftEligibleWorkers(),
                timezone = self.locationModel.get("timezone"),
                weekStartMoment = moment.tz(self.currentWeek, timezone),
                shiftStart = weekStartMoment.clone().hours(9).utc().format(),
                shiftStop = weekStartMoment.clone().hours(17).utc().format(),
                scheduleModelIndex = self.scheduleModels.getIndexBy("roleName", roleName),
                scheduleModel,
                success,
                callbackedSuccess,
                error
            ;

            if (scheduleModelIndex >= 0) {
                scheduleModel = self.scheduleModels[scheduleModelIndex];
            }

            // close the dropdown if it's open
            if ($target.hasClass("dropdown-selection")) {
                $target.closest('.dropdown').find(".dropdown-toggle").dropdown("toggle");
            } else if ($target.hasClass("dropup-selection")) {
                $target.closest('.dropup').find(".dropdown-toggle").dropdown("toggle");
            }

            // add upstream models to the shift model
            newShiftModel.addUpstreamModel("locationId", self.locationModel.id);
            newShiftModel.addUpstreamModel("roleId", roleId);
            newShiftModel.addProperty("roleName", roleName);

            // and to the collection
            eligibleUsersCollection.addUpstreamModel("locationId", self.locationModel.id);
            eligibleUsersCollection.addUpstreamModel("roleId", roleId);

            newShiftModel.createRequest();

            error = function(model, response, opts) {
                $.notify({message: "Unable to create a new shift - please contact support if the problem persists."},{type: "danger"});
            };

            success = function(model, response, opts) {

                model.set("user_name", "Unassigned Shift");

                // add shift id to the collection and then fetch it
                eligibleUsersCollection.addUpstreamModel("shiftId", model.id);

                callbackedSuccess = function(coll, response, opts) {
                    self.addDelegateView(
                        "modal-view-" + model.id,
                        new Views.Components.ShiftModalView({
                            el: "modal-placeholder-new",
                            collection: eligibleUsersCollection,
                            model: model,
                            mode: "new",
                            roleName: roleName,
                            locationModel: self.locationModel,
                            id: model.id,
                            scheduleModel: scheduleModel,
                            callback: function(shiftModel) {
                                self.sendShiftToView(shiftModel);
                            },
                        })
                    );

                    $("#shiftControlModal-" + model.id).on("hidden.bs.modal", function(e) {
                        self.delegateViews["modal-view-" + model.id].close()
                    });
                };

                eligibleUsersCollection.fetch({
                    success: callbackedSuccess,
                    error: error,
                });
            };

            newShiftModel.save(
                {
                    start: shiftStart,
                    stop: shiftStop,
                },
                {
                    success: success,
                    error: error
                }
            );
        },
        sendShiftToView: function(shiftModel) {
            /* adds a model to the appropriate day calendar */
            var self = this,
                timezone = self.locationModel.get("timezone"),
                shiftStartLocalMoment = moment.utc(shiftModel.get("start")).tz(timezone),
                shiftStopLocalMoment = moment.utc(shiftModel.get("stop")).tz(timezone),
                startDay = shiftStartLocalMoment.format("dddd-D"),
                viewIndex = -1,
                stopDay = shiftStopLocalMoment.format("dddd-D"),

                stopsAfterMidnight = (shiftStopLocalMoment.hours() +
                                     shiftStopLocalMoment.minutes() +
                                     shiftStopLocalMoment.seconds() +
                                     shiftStopLocalMoment.milliseconds()) > 0
            ;

            // try adding to start
            // view might be in self.views, or in the delegateViews - will never be in both
            if (_.has(self.delegateViews, startDay)) {
                self.delegateViews[startDay].data[shiftModel.roleName].shifts.add(shiftModel);
            }

            viewIndex = self.views.getIndexBy("id", startDay);
            if (viewIndex >= 0) {
                self.views[viewIndex].view.data[shiftModel.roleName].shifts.add(shiftModel);
            }

            // also add shift to the stopDay, because they wrap
            if (startDay !== stopDay && stopsAfterMidnight) {
                if (_.has(self.delegateViews, stopDay)) {
                    self.delegateViews[stopDay].data[shiftModel.roleName].shifts.add(shiftModel);
                }

                viewIndex = self.views.getIndexBy("id", stopDay);
                if (viewIndex >= 0) {
                    self.views[viewIndex].view.data[shiftModel.roleName].shifts.add(shiftModel);
                }
            }
        }
    });

    var lazyLoadFunction = _.throttle(function (event) {
        var self = this;

        if (!_.isEmpty(self.views) && isScrolledIntoView('.scheduling-shifts-container')) {
            var view = self.views.shift();
            self.addDelegateView(view.id, view.view);
        }
    }, 100);

    var isScrolledIntoView = function (elem) {
        var $elem = $(elem),
            $window = $(window),
            docViewTop = $window.scrollTop(),
            docViewBottom = docViewTop + $window.height(),
            elemTop = $elem.offset().top,
            elemBottom = elemTop + $elem.height()
        ;

        return elemBottom <= docViewBottom;
    };

    root.App.Views.SchedulingWeekShiftsView = SchedulingWeekShiftsView;

})(this);
