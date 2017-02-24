(function(root) {

    "use strict";

    var Collections = root.App.Collections,
        Models = root.App.Models,
        Views = root.App.Views,
        Util = root.App.Util
    ;

    var SchedulingControllerView = Views.Base.extend({
        el: "#manage-main",
        events: {
            "click .schedule-navigation-bar .change-week" : "adjustWeek",
            "click .role-demand .save-demand-settings" : "saveRoleDemandSettings",
            "click .role-demand .calculate-now" : "calculateNow",
            "click .download-csv" : "downloadCSV",
            "click .copy-demand-button": "onCopyDemandButtonClick",
            "click #view-attendance": "goToAttendance",
        },
        initialize: function(opts) {
            SchedulingControllerView.__super__.initialize.apply(this);
            this.mainHeaderContentVisible = "scheduling";

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.orgModel)) {
                    this.orgModel = opts.orgModel;
                }

                if (!_.isUndefined(opts.locationModel)) {
                    this.locationModel = opts.locationModel;
                }

                if (!_.isUndefined(opts.rolesCollection)) {
                    this.rolesCollection = opts.rolesCollection;
                }

                if (!_.isUndefined(opts.rolesUsersCollection)) {
                    this.rolesUsersCollection = opts.rolesUsersCollection;
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
                    this.currentDate = opts.currentDate;
                } else {
                    this.currentDate = Util.convertMomentObjToDateStr(moment());
                }

                this.csvFormat = opts.csvFormat || false;

                // determine start and future bound of scheduling page
                var currentWeekMoment = Util.getDateForWeekStart(moment(this.currentDate), this.weekStartsOn),
                    lastWeekMoment = Util.getDateForWeekStart(moment().add("days", 100), this.weekStartsOn)
                ;

                this.currentWeek = Util.convertMomentObjToDateStr(currentWeekMoment);
                this.lastWeekStart = Util.convertMomentObjToDateStr(lastWeekMoment);

                this.checkCurrentWeek();
            }

            this.shifts = [];
            this.shiftSummaries = [];
            this.scheduleModels = [];
            this.timeclocks = [];
            this.timeOffRequests = [];
            this.demandViews = {};
            this.displayShifts;

            this.error = function(collection, response, opts) {
                $.notify({message:"There was an error loading the page"},{type: "danger"});
            };

            this.$el.on('show.bs.collapse', function (event) {
                var $target = $(event.target),
                    collapseId = $target.data('collapse-id'),
                    selector = '.collapse-button-' + collapseId
                ;

                $(selector).find('.glyphicon').removeClass('glyphicon-chevron-down').addClass('glyphicon-chevron-up');
            });

            this.$el.on('hide.bs.collapse', function (event) {
                var $target = $(event.target),
                    collapseId = $target.data('collapse-id'),
                    selector = '.collapse-button-' + collapseId
                ;

                $(selector).find('.glyphicon').removeClass('glyphicon-chevron-up').addClass('glyphicon-chevron-down');
            });

            this.shiftsShown = false;
        },
        close: function() {
            this.$el.off("hide.bs.collapse");
            this.$el.off("show.bs.collapse");
            SchedulingControllerView.__super__.close.call(this);
        },
        render: function(opts) {
            var self = this,
                data = {
                    displayTimezone: self.displayTimezone,
                    timezoneWarning: self.timezoneWarning,
                    timezone: self.locationModel.get("timezone").replace('_', ' '),
                }
            ;

            self.$el.html(ich.scheduling_controller(data));
            self.renderWeekView();
            return this;
        },
        renderWeekView: function() {
            // these need to be reset for each week
            this.shifts = [];
            this.shiftSummaries = [];
            this.scheduleModels = [];
            this.timeclocks = [];
            this.timeOffRequests = [];
            this.displayShifts = false;
            this.shiftsShown = false;

            var self = this,
                schedules = [],
                tempSchedulesCollection,
                schedulesFetch,
                stillProcessing = [],
                currentWeekMoment = moment.tz(
                    self.currentWeek, self.locationModel.get("timezone")).utc(),
                queryStart = currentWeekMoment.format("YYYY-MM-DDTHH:mm:ss"),
                scheduleStartQuery = moment.tz(
                    self.currentWeek, self.locationModel.get("timezone")).subtract(1, "week").utc().format("YYYY-MM-DDTHH:mm:ss"),
                shiftStartQuery = moment.tz(
                    self.currentWeek, self.locationModel.get("timezone")).subtract(1, "day").utc().format("YYYY-MM-DDTHH:mm:ss"),
                queryEnd = moment.tz(
                    self.currentWeek, self.locationModel.get("timezone")).add(7, "days").utc().format("YYYY-MM-DDTHH:mm:ss"),
                validStates = ["initial", "unpublished", "chomp-queue", "chomp-processing", "mobius-queue", "mobius-processing", "published"],
                processingStates = ["chomp-queue", "chomp-processing", "mobius-queue", "mobius-processing"]
            ;

            // remove delegate views, if any
            self.removeAllDelegateViews();

            $(".scheduling-messages").empty();

            $(".schedule-navigation-bar").show();
            self.renderRightArrow();
            self.updateWeekTitle();
            self.updateRoute();

            // loop through roles collection and prepare schedule collections to fetch
            _.each(self.rolesCollection.models, function(roleModel, index) {

                tempSchedulesCollection = new Collections.Schedules();
                tempSchedulesCollection.addUpstreamModel("locationId", self.locationModel.id);
                tempSchedulesCollection.addUpstreamModel("roleId", roleModel.id);
                tempSchedulesCollection.addParam("start", scheduleStartQuery);
                tempSchedulesCollection.addParam("end", queryEnd);
                tempSchedulesCollection.addProperty("roleName", roleModel.get("name"));

                schedules.push(tempSchedulesCollection);
            });

            schedulesFetch = _.invoke(schedules, "fetch", {error: self.error});

            $.when.apply($, schedulesFetch).done(function() {
                _.each(schedules, function(roleScheduleCollection, index) {
                    var roleName = roleScheduleCollection.roleName,
                        roleId = roleScheduleCollection.getUpstreamModelId("roleId"),
                        tempShiftsCollection,
                        tempShiftSummaryCollection,
                        tempTimeclockCollection,
                        tempTimeOffRequestCollection,
                        scheduleModel,
                        pastScheduleModel,
                        currentState,
                        demandView,
                        wizardView
                    ;

                    // this is a collection query - but for a very specific time span
                    // it can return 0, 1, or 2 schedules (it's ok if there is no schedule during the week)
                    if (roleScheduleCollection.models.length > 2) {
                        return self.error();
                    }

                    if (roleScheduleCollection.models.length === 2) {
                        scheduleModel = roleScheduleCollection.last();
                        pastScheduleModel = roleScheduleCollection.first();
                    } else if (roleScheduleCollection.models.length === 1) {
                        var tempSchedule = roleScheduleCollection.first();

                        if (moment.utc(tempSchedule.get("start")).isBefore(currentWeekMoment)) {
                            pastScheduleModel = tempSchedule;
                        } else {
                            scheduleModel = tempSchedule;
                        }
                    }

                    // if no schedule, still get shifts for that timespan via normal endpoint
                    if (_.isUndefined(scheduleModel)) {
                        currentState = "unpublished";

                        /* shifts */
                        tempShiftsCollection = new Collections.Shifts();
                        tempShiftsCollection.addUpstreamModel("locationId", self.locationModel.id);
                        tempShiftsCollection.addUpstreamModel("roleId", roleId);
                        tempShiftsCollection.addParam("start", shiftStartQuery);
                        tempShiftsCollection.addParam("end", queryEnd);
                        tempShiftsCollection.addProperty("roleName", roleName);

                        // shift summary collection
                        tempShiftSummaryCollection = new Collections.Shifts();
                        tempShiftSummaryCollection.addUpstreamModel("locationId", self.locationModel.id);
                        tempShiftSummaryCollection.addUpstreamModel("roleId", roleId);
                        tempShiftSummaryCollection.addProperty("roleName", roleName);
                        tempShiftSummaryCollection.addParam("start", shiftStartQuery);
                        tempShiftSummaryCollection.addParam("end", queryEnd);
                        tempShiftSummaryCollection.addParam("include_summary", true);

                    } else {
                        currentState = scheduleModel.get("state");

                        // check if a valid state
                        if (validStates.indexOf(currentState) === -1) {
                            self.error();
                        }

                        // check if being processed
                        if (processingStates.indexOf(currentState) >= 0) {
                            stillProcessing.push(roleName);
                        }

                        // make sure model has the same attributes as the collection
                        scheduleModel.addProperty("roleName", roleScheduleCollection.roleName);
                        scheduleModel.addUpstreamModel("locationId", self.locationModel.id);
                        scheduleModel.addUpstreamModel("roleId", roleId);

                        /* shift prep */
                        tempShiftsCollection = new Collections.ScheduleShifts();
                        tempShiftsCollection.addUpstreamModel("locationId", self.locationModel.id);
                        tempShiftsCollection.addUpstreamModel("roleId", roleId);
                        tempShiftsCollection.addUpstreamModel("scheduleId", scheduleModel.id);
                        tempShiftsCollection.addProperty("roleName", roleName);

                        /* shift summary */
                        tempShiftSummaryCollection = new Collections.ScheduleShifts();
                        tempShiftSummaryCollection.addUpstreamModel("locationId", self.locationModel.id);
                        tempShiftSummaryCollection.addUpstreamModel("roleId", roleId);
                        tempShiftSummaryCollection.addUpstreamModel("scheduleId", scheduleModel.id);
                        tempShiftSummaryCollection.addProperty("roleName", roleName);
                        tempShiftSummaryCollection.addParam("include_summary", true);

                        /* timeclock prep */
                        tempTimeclockCollection = new Collections.ScheduleTimeclocks();
                        tempTimeclockCollection.addUpstreamModel("locationId", self.locationModel.id);
                        tempTimeclockCollection.addUpstreamModel("roleId", roleId);
                        tempTimeclockCollection.addUpstreamModel("scheduleId", scheduleModel.id);

                        /* time off request prep */
                        tempTimeOffRequestCollection = new Collections.ScheduleTimeOffRequests();
                        tempTimeOffRequestCollection.addUpstreamModel("locationId", self.locationModel.id);
                        tempTimeOffRequestCollection.addUpstreamModel("roleId", roleId);
                        tempTimeOffRequestCollection.addUpstreamModel("scheduleId", scheduleModel.id);

                        self.timeclocks.push(tempTimeclockCollection);
                        self.timeOffRequests.push(tempTimeOffRequestCollection);
                        self.scheduleModels.push(scheduleModel);

                        // prepare demand view separately so that the wizard can include it as a callback
                        self.demandViews[roleName] = new Views.SetDemandCardView({
                            model: scheduleModel,
                            roleName: roleName,
                            roleId: roleId,
                            weekStartsOn: self.weekStartsOn.charAt(0).toUpperCase() + self.weekStartsOn.substring(1),
                            demandStartMoment: moment.tz(self.currentWeek, self.locationModel.get("timezone")),
                            previousSchedule: pastScheduleModel,
                            orgModel: self.orgModel,
                            showShiftsCallback: function() {
                                if (!self.dislpayShifts) {
                                    self.showShifts();
                                    self.displayShifts = true;
                                }
                            },
                        });

                        wizardView = new Views.SchedulingWizardView({
                            model: scheduleModel,
                            roleName: roleName,
                            roleId: roleId,
                            orgModel: self.orgModel,
                            showDemandCallback: function() {
                                self.showDemandCard(roleName, roleId);
                            },
                            showShiftsCallback: function() {
                                if (!self.dislpayShifts) {
                                    self.showShifts();
                                    self.displayShifts = true;
                                }
                            },
                            renderHeaderAction: function() {
                                self.renderHeaderAction(self.delegateViews[self.currentWeek + "-shifts"]);
                            },
                        });

                        self.addDelegateView(
                            "wizard-view-" + roleName,
                            wizardView
                        );

                        wizardView.hide();

                        // show the wizard for this schedule if in initial state
                        if (currentState === "initial") {
                            wizardView.show()
                        }

                        // show a demand card if unpublished and chomp hasn't run yet
                        else if (currentState === "unpublished") {
                            if((_.isNull(scheduleModel.get("chomp_end")) &&
                                 _.isNull(scheduleModel.get("chomp_start"))) &&
                                !_.isNull(scheduleModel.get('demand'))
                            ) {
                                self.showDemandCard(roleName, roleId);
                            } else {
                                wizardView.show();
                            }
                        }
                    }

                    // check if need to display shifts
                    if (currentState !== "initial") {
                        self.displayShifts = true
                    }

                    self.shifts.push(tempShiftsCollection);
                    self.shiftSummaries.push(tempShiftSummaryCollection);
                });

                // shifts will be rendered in all cases except when all schedules are in the initial state
                if (self.displayShifts) {
                    self.showShifts();
                } else {
                    self.renderHeaderAction(self.delegateViews[self.currentWeek + "-shifts"]);
                }

                // always do fetch to check for timeclocks
                self.checkTimeclocks();

                // show time off requests for boss
                if (self.orgModel.isBoss()) {
                    self.showTimeOffRequests();
                }

                if (stillProcessing.length > 0) {
                    var concatArrayString = function(stringArray) {
                        return stringArray.length === 1 ? stringArray[0] : stringArray.slice(0, stringArray.length - 1).join(', ').concat(' and ' + stringArray[stringArray.length - 1]);
                    };

                    $(".scheduling-messages").append(ich.scheduling_message({
                        info: true,
                        message: "Schedules for " + concatArrayString(stillProcessing) + " are still being processed. You will receive an email when processing is complete.",
                    }));
                }
            });
        },
        showShifts: function() {
            var self = this,
                shiftsFetch,
                shiftSummariesFetch,
                csvData = {}
            ;

            if (self.shiftsShown) {
                return;
            }

            // fetch shifts and add the view that contains all of them
            shiftsFetch = _.invoke(self.shifts, "fetch", {error: self.error});
            $.when.apply($, shiftsFetch).done(function() {

                // add upstream model info to each shift
                _.each(self.shifts, function(shiftsCollection, index) {
                    _.each(shiftsCollection.models, function(shiftModel) {
                        shiftModel.addUpstreamModel("locationId", self.locationModel.id);
                        shiftModel.addUpstreamModel("roleId", shiftsCollection.getUpstreamModelId("roleId"));
                        shiftModel.addProperty("roleName", shiftsCollection.roleName);
                    });
                });

                self.addDelegateView(
                    self.currentWeek + "-shifts",
                    new Views.SchedulingWeekShiftsView({
                        shifts: self.shifts,
                        orgModel: self.orgModel,
                        locationModel: self.locationModel,
                        currentWeek: self.currentWeek,
                        scheduleModels: self.scheduleModels,
                        rolesCollection: self.rolesCollection
                    })
                );

                self.renderHeaderAction(self.delegateViews[self.currentWeek + "-shifts"]);
            });

            // fetch shift summaries separately
            shiftSummariesFetch = _.invoke(self.shiftSummaries, "fetch", {error: self.error});
            $.when.apply($, shiftSummariesFetch).done(function() {

                self.addDelegateView(
                    self.currentWeek + "-shiftSummary",
                    new Views.WeekSummaryCardView({
                        data: self.shiftSummaries
                    })
                );
            });

            // csv download button for shifts are visible when shifts are being rendered
            if (self.csvFormat) {
                csvData["data"] = [];

                _.each(self.rolesCollection.models, function(roleModel, index) {
                    csvData["data"].push({
                        name: roleModel.get("name"),
                        roleId: roleModel.id,
                    });
                });

                self.addDelegateView(
                    "csv-download-view",
                    new Views.Components.CSVDownloadView({
                        data: csvData,
                    })
                );
            }

            self.shiftsShown = true;
        },
        showDemandCard: function(roleName, roleId) {
            var self = this;

            if (_.has(self.delegateViews, roleName + "-demand")) {
                $('#demand-' + roleId).show();
            } else {
                self.addDelegateView(
                    roleName + "-demand",
                    self.demandViews[roleName]
                );
            }

        },
        showTimeOffRequests: function() {
            var self = this,
                fetch,
                count = 0,
                allTimeOffRequestsOff = _.every(
                    self.rolesCollection.pluck("enable_time_off_requests"), function(value) {
                        return !value;
                })
            ;

            fetch = _.invoke(self.timeOffRequests, "fetch", {error: self.error});
            $.when.apply($, fetch).done(function() {
                _.each(self.timeOffRequests, function(collection) {
                    count += collection.models.length;
                });

                // show time off requests view, if applicable
                if (count > 0 || !allTimeOffRequestsOff ) {
                    self.addDelegateView(
                        "scheduling-time-off-requests",
                        new Views.SchedulingTimeOffRequestsCardView({
                            timeOffRequests: self.timeOffRequests,
                            rolesUsersCollection: self.rolesUsersCollection,
                            collapsed: count < 1,
                            locationModel: self.locationModel,
                            currentWeek: self.currentWeek,
                        })
                    );
                }
            });
        },
        checkTimeclocks: function() {
            var self = this,
                timeclocksFetch,
                timeclockCount = 0
            ;

            timeclocksFetch = _.invoke(self.timeclocks, "fetch", {error: self.error});
            $.when.apply($, timeclocksFetch).done(function() {

                _.each(self.timeclocks, function(collection) {
                    timeclockCount += collection.models.length;
                });

                if (timeclockCount > 0) {
                    $("#view-attendance").removeClass("hidden");
                } else {
                    $("#view-attendance").addClass("hidden");
                }
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
                return self.error();
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
        downloadCSV: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target),
                roleId = $target.attr("data-roleId"),
                queryStart = moment.tz(self.currentWeek, self.locationModel.get("timezone")).utc().format("YYYY-MM-DDTHH:mm:ss"),
                queryEnd = moment.tz(self.currentWeek, self.locationModel.get("timezone")).add(7, "days").utc().format("YYYY-MM-DDTHH:mm:ss"),
                csvUrl = "/api/v2/organizations/" + ORG_ID +
                         "/locations/" + self.locationId +
                         "/roles/" + roleId +
                         "/shifts/?csv_export=true&start=" + queryStart + "&end=" + queryEnd
            ;

            window.open(csvUrl);
        },
        updateRoute: function() {
            var self = this,
                route,
                regex = /^(\d{4})(\/|-)(\d{1,2})(\/|-)(\d{1,2})$/,
                replace = !Backbone.history.getFragment().split("/").pop().match(regex)
            ;

            route = "locations/" + self.locationModel.id + "/scheduling/" + self.currentWeek;

            Backbone.history.navigate(route, {trigger: false, replace: replace});
        },
        updateWeekTitle: function() {
            // renders the title of the current week being shown

            var self = this,
                week,
                $weekNav = $(".schedule-navigation-bar").find(".week-date-label"),
                $weekText = $weekNav.children(".week-title"),
                $weekTextMobile = $weekNav.children(".week-title-mobile")
            ;

            week = moment(self.currentWeek);

            $weekText.text("Week of " + week.format("D MMMM YYYY"));
            $weekTextMobile.text("Week of " + week.format("MM-DD-YYYY"));
        },
        renderRightArrow: function() {
            // renders the right arrow based on the current week being shown
            var self = this,
                $rightArrow = $(".schedule-navigation-bar").find(".right-arrow")
            ;

            if (self.currentWeek === self.lastWeekStart ||
                moment(self.currentWeek) > moment(self.lastWeekStart))
            {
                $rightArrow.addClass("disabled");
            } else {
                $rightArrow.removeClass("disabled");
            }
        },
        goToAttendance: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                route = "locations/" + self.locationModel.id + "/attendance/" + self.currentWeek
            ;

            Backbone.history.navigate(route, {trigger: true});
        },
    });

    root.App.Views.SchedulingControllerView = SchedulingControllerView;

})(this);
