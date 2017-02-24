(function(root) {

    "use strict";

    var Collections = root.App.Collections,
        Models = root.App.Models,
        Views = root.App.Views,
        Util = root.App.Util
    ;

    var AttendanceControllerView = Views.Base.extend({
        el: "#manage-main",
        events: {
            "click .attendance-navigation-bar .change-week" : "adjustWeek",
        },
        initialize: function(opts) {
            AttendanceControllerView.__super__.initialize.apply(this);
            this.mainHeaderContentVisible = "attendance";

            // this.collection holds a collection of roles with users recursively added

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.locationId)) {
                    this.locationId = opts.locationId;
                }

                if (!_.isUndefined(opts.locationModel)) {
                    this.locationModel = opts.locationModel;
                }

                if (!_.isUndefined(opts.orgModel)) {
                    this.orgModel = opts.orgModel;
                }

                if (!_.isUndefined(opts.displayTimezone)) {
                    this.displayTimezone = opts.displayTimezone;
                }

                if (!_.isUndefined(opts.timezoneWarning)) {
                    this.timezoneWarning = opts.timezoneWarning;
                }

                if (!_.isUndefined(opts.weekStartsOn)) {
                    this.weekStartsOn = opts.weekStartsOn;
                }

                if (!_.isUndefined(opts.renderHeaderAction)) {
                    this.renderHeaderAction = opts.renderHeaderAction;
                }

                if (!_.isUndefined(opts.currentDate) && !_.isNull(opts.currentDate)) {
                    this.currentDate = opts.currentDate;    // format 2016-01-15
                } else {
                    this.currentDate = Util.convertMomentObjToDateStr(moment());    // format 2016-01-15
                }

                var currentWeekMoment = Util.getDateForWeekStart(moment(this.currentDate), this.weekStartsOn),
                    lastWeekStartMoment = Util.getDateForWeekStart(moment(), this.weekStartsOn)
                ;

                this.currentWeek = Util.convertMomentObjToDateStr(currentWeekMoment);

                // also calculate end of the calendar
                this.lastWeekStart = Util.convertMomentObjToDateStr(lastWeekStartMoment);

                this.checkCurrentWeek();
            }
        },
        render: function(opts) {
            var self = this,
                currentIndex,
                data = {
                    displayTimezone: self.displayTimezone,
                    timezoneWarning: self.timezoneWarning,
                    timezone: self.locationModel.get("timezone").replace('_', ' '),
                    locationName: self.locationModel.get("name"),
                },
                timeclocksEnabled = self.collection.pluck("enable_timeclock"),
                timeclockOnboarding = true
            ;

            for (var i=0; i < timeclocksEnabled.length; i++) {
                if (timeclocksEnabled[i] === true) {
                    timeclockOnboarding = false;
                    break;
                }
            }

            data.timeclockOnboard = timeclockOnboarding;

            // render base wrapper
            self.$el.html(ich.location_attendance_controller(data));

            // on with the real stuff now
            self.renderWeekView();

            return this;
        },
        renderWeekView: function() {
            var self = this,
                locationAttendanceCollection = new Collections.LocationAttendance(),
                currentWeekStart = self.currentWeek,
                currentWeekEnd = Util.convertMomentObjToDateStr(
                    moment(currentWeekStart).add(6, "days")     // this is the last date of the week
                ),
                success,
                error = function(collection, response, opts) {
                    $.notify({message:"There was an error loading the page"},{type: "danger"});
                },
                dates,
                data,
                responseData,
                summaryData
            ;

            // remove delegate views, if any
            _.each(self.delegateViews, function(delegateView, index, list) {
                delegateView.close();
            });

            self.renderRightArrow();
            self.updateWeekTitle();
            self.updateRoute();

            // upstream models and params
            locationAttendanceCollection.addUpstreamModel("locationId", self.locationId);

            // add params
            locationAttendanceCollection.addParam("startDate", currentWeekStart);
            locationAttendanceCollection.addParam("endDate", currentWeekEnd);

            success = function(collection, response, opts) {

                // backbone is shoving all data into one model still, will split this up later
                responseData = locationAttendanceCollection.pop();
                data = responseData.get("data");
                summaryData = responseData.get("summary");

                // the dates appear to be sorted in the collection, but better safe than sorry
                dates = _.keys(data).sort(
                    function(a, b) {
                        return moment(a) > moment(b);
                    }
                );

                // create view for each day of the week
                _.each(dates, function(date, index) {
                    self.addDelegateView(
                        date,
                        new Views.AttendanceDayView({
                            rolesCollection: self.collection,
                            date: date,
                            collection: new Collections.Base(data[date]),
                            locationId: self.locationId,
                            orgModel: self.orgModel,
                            locationModel: self.locationModel,
                            sendTimeclockToOtherDayCallback: function(date, timeclockModel) {
                                if (_.has(self.delegateViews, date)) {
                                    self.delegateViews[date].addTimeclockOnDay(timeclockModel);
                                }
                            },
                            updateSummaryCardCallback: function(date, userId, roleId, addSeconds, deductSeconds, timeclockAdjustment) {
                                if (_.has(self.delegateViews, date)) {
                                    self.delegateViews["summary"].updateUserModelData(userId, roleId, addSeconds, deductSeconds, timeclockAdjustment);
                                }
                            }
                        })
                    );
                });

                self.addDelegateView(
                    "summary",
                    new Views.AttendanceSummaryView({
                        collection: new Collections.Base(summaryData),
                        locationId: self.locationId,
                        rolesCollection: self.collection,
                    })
                );

                self.addDelegateView(
                    "csv-export",
                    new Views.AttendanceCSVExportView({
                        locationId: self.locationId,
                        locationModel: self.locationModel,
                        queryStart: currentWeekStart,
                        queryStop: currentWeekEnd,
                    })
                );

                self.renderHeaderAction({
                    getAction: function() {
                        return {
                            label: 'Timeclock',
                            callback: function() {
                                self.newTimeclock(event);
                            },
                            data: _.first(dates),
                        };
                    },
                });
            };

            locationAttendanceCollection.fetch({
                success: success,
                error: error,
            });
        },
        adjustWeek: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target).closest(".change-week"),
                direction = $target.attr("data-direction"),
                newWeekMoment,
                newWeek
            ;

            // only enable if it's an active button
            if ($target.hasClass("disabled")) {
                return;
            }

            // travel to the future
            if (direction === "right") {
                newWeekMoment = moment(self.currentWeek).add(1, "week");

            // travel back in time
            } else if (direction === "left") {
                newWeekMoment = moment(self.currentWeek).subtract(1, "week");

            // gtfo
            } else {
                console.log("unknown direction provided");
                $.notify({message:"There was an error loading the page"},{type: "danger"});
                return;
            }

            self.currentWeek = Util.convertMomentObjToDateStr(newWeekMoment);
            self.checkCurrentWeek();

            return self.renderWeekView();
        },
        checkCurrentWeek: function() {
            var self = this;

            // make sure currentWeek is within set bounds
            if (moment(self.currentWeek) > moment(self.lastWeekStart)) {
                self.currentWeek = self.lastWeekStart;
            }
        },
        updateRoute: function() {
            var self = this,
                route,
                regex = /^(\d{4})(\/|-)(\d{1,2})(\/|-)(\d{1,2})$/,
                replace = !Backbone.history.getFragment().split("/").pop().match(regex);
            ;

            route = "locations/" + self.locationId + "/attendance/" + self.currentWeek;

            Backbone.history.navigate(route, {trigger: false, replace: replace});
        },
        updateWeekTitle: function() {
            // renders the title of the current week being shown

            var self = this,
                week,
                $weekNav = $(".attendance-navigation-bar").find(".week-date-label"),
                $weekText = $weekNav.children(".week-title"),
                $weekTextMobile = $weekNav.children(".week-title-mobile")
            ;

            week = moment(self.currentWeek);

            $weekText.text("Week of " + week.format("D MMMM YYYY"));
            $weekTextMobile.text("Week of " + week.format("MM-DD-YYYY"));
        },
        renderRightArrow: function() {
            // determines if the right arrow should be disabled or not
            var self = this,
                $rightArrow = $(".attendance-navigation-bar").find(".right-arrow")
            ;

            if (self.currentWeek === self.lastWeekStart ||
                moment(self.currentWeek) > moment(self.lastWeekStart))
            {
                $rightArrow.addClass("disabled");
            } else {
                $rightArrow.removeClass("disabled");
            }
        },
        newTimeclock: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target),
                $mainSpan = $target.closest(".new-timeclock"),
                roleId = parseInt($mainSpan.attr("data-role-id")),
                userId = parseInt($mainSpan.attr("data-user-id")),
                timezone = self.locationModel.get("timezone"),
                roleId,
                suggestedTimes,
                userDayObj,
                shifts,
                firstShift,
                date = $target.data('id');
            ;

            if (!_.isNaN(userId)) {
                userDayObj = self.collection.findWhere({role_id: roleId, user_id: userId});
                shifts = userDayObj.get("shifts");
                firstShift = shifts[0];

                if (!_.isUndefined(firstShift)) {
                    suggestedTimes = {
                        start: moment.utc(firstShift.start).tz(timezone),
                        stop: moment.utc(firstShift.stop).tz(timezone),
                    };
                }
            }

            // NOTE: if userId is defined, the modal will be restricted to only including that user
            self.addDelegateView(
                "modal-view-new",
                new Views.Components.TimeclockModalView({
                    el: ".modal-placeholder-" + date,
                    id: "new-" + date,
                    locationId: self.locationId,
                    locationModel: self.locationModel,
                    rolesCollection: self.collection,
                    date: date,
                    mode: "new",
                    userId: userId,
                    roleId: roleId,
                    suggestedTimes: suggestedTimes,
                    saveTimeclockCallback: function(model, addSeconds, subtractSeconds) {
                        var startLocalMoment = moment.utc(model.get("start")).tz(self.locationModel.get("timezone")),
                            isoDate = startLocalMoment.format("YYYY-MM-DD")
                        ;

                        // model's start is on same day as it was
                        if (isoDate === date) {
                            self.delegateViews[date].addTimeclockOnDay(model);
                        }

                        // model's start day is different
                        else {
                            self.delegateViews[date].sendTimeclockToOtherDayCallback(isoDate, model);
                            self.delegateViews[date].removeTimeclockFromDay(model.get("id"), model.get("role_id"), model.get("user_id"));
                        }

                        self.delegateViews[date].updateSummaryCardCallback(isoDate, model.get("user_id"), model.get("role_id"), addSeconds, subtractSeconds, 1);
                    },
                })
            );
        },
    });

    root.App.Views.AttendanceControllerView = AttendanceControllerView;

})(this);
