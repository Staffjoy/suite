(function(root) {

    "use strict";

    var Collections = root.App.Collections,
        Models = root.App.Models,
        Views = root.App.Views,
        Util = root.App.Util
    ;

    var PlannerControllerView = Views.Base.extend({
        el: "#planner-main",
        events: {
            "click .calendar-navigation-bar .change-week" : "adjustWeek",
        },
        initialize: function(opts) {
            PlannerControllerView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.displayTimezone)) {
                    this.displayTimezone = opts.displayTimezone;
                }

                if (!_.isUndefined(opts.timezone)) {
                    this.timezone = opts.timezone;
                }

                if (!_.isUndefined(opts.locationModel)) {
                    this.locationModel = opts.locationModel;
                }

                if (!_.isUndefined(opts.orgModel)) {
                    this.orgModel = opts.orgModel;
                }

                if (!_.isUndefined(opts.userModel)) {
                    this.userModel = opts.userModel;
                }

                if (!_.isUndefined(opts.roleModel)) {
                    this.roleModel = opts.roleModel;
                }

                if (!_.isUndefined(opts.weekStartsOn)) {
                    this.weekStartsOn = opts.weekStartsOn;
                }

                if (!_.isUndefined(opts.currentDate) && !_.isNull(opts.currentDate)) {
                    this.currentDate = opts.currentDate;
                } else {
                    this.currentDate = Util.convertMomentObjToDateStr(moment());
                }

                // determine start and future bound of scheduling page
                var currentWeekMoment = Util.getDateForWeekStart(moment(this.currentDate), this.weekStartsOn);
                this.currentWeek = Util.convertMomentObjToDateStr(currentWeekMoment);
                this.error = function() {
                    $.notify({message:"There was an error loading the page - please contact support if the problem persists"},{type:"danger"});
                }
            }
        },
        render: function(opts) {
            var self = this,
                data = {
                    displayTimezone: self.displayTimezone,
                    timezone: self.timezone.replace("_", " "),
                }
            ;

            // render base wrapper
            self.$el.html(ich.calendar_base(data));

            // on with the real stuff now
            self.renderWeekView();

            return this;
        },
        renderWeekView: function() {
            var self = this,
                weekStartMoment = moment.tz(
                    self.currentWeek, self.locationModel.get("timezone")).utc(),
                weekStartQuery = weekStartMoment.format("YYYY-MM-DDTHH:mm:ss"),
                shiftStartQuery = moment.tz(
                    self.currentWeek, self.locationModel.get("timezone")).subtract(1, "day").utc().format("YYYY-MM-DDTHH:mm:ss"),
                weekEndQuery = moment.tz(
                    self.currentWeek, self.locationModel.get("timezone")).add(7, "days").utc().format("YYYY-MM-DDTHH:mm:ss"),
                schedulesCollection = new Collections.Schedules(),
                shiftsCollection = new Collections.Shifts(),
                timeclocksCollection = new Collections.Timeclocks(),
                timeOffRequestsCollection = new Collections.TimeOffRequests(),
                unclaimedShiftsCollection,
                scheduleModel,
                currentState,
                primaryFetch,
                availabilityModel,
                onFetchComplete,
                validStates = ["initial", "unpublished", "chomp-queue", "chomp-processing", "mobius-queue", "mobius-processing", "published"],
                preferenceStates = ["initial", "unpublished", "chomp-queue", "chomp-processing"],
                showShifts = true
            ;

            // remove delegate views, if any
            _.each(self.delegateViews, function(delegateView, index, list) {
                delegateView.close();
            });

            self.updateWeekTitle();
            self.updateRoute();

            // prepare collections that are being fetched

            // schedules collection
            schedulesCollection.addUpstreamModel("locationId", LOCATION_ID);
            schedulesCollection.addUpstreamModel("roleId", ROLE_ID);
            schedulesCollection.addUpstreamModel("userId", USER_ID);
            schedulesCollection.addParam("start", weekStartQuery);
            schedulesCollection.addParam("end", weekEndQuery);

            // shifts collection query will include the prior day in order to
            // get the shifts that end during the current week
            shiftsCollection.addUpstreamModel("locationId", LOCATION_ID);
            shiftsCollection.addUpstreamModel("roleId", ROLE_ID);
            shiftsCollection.addParam("user_id", USER_ID);
            shiftsCollection.addParam("start", shiftStartQuery);
            shiftsCollection.addParam("end", weekEndQuery);
            shiftsCollection.addParam("filter_by_published", true);

            timeOffRequestsCollection.addUpstreamModel("locationId", LOCATION_ID);
            timeOffRequestsCollection.addUpstreamModel("roleId", ROLE_ID);
            timeOffRequestsCollection.addUpstreamModel("userId", USER_ID);
            timeOffRequestsCollection.addParam('start', weekStartQuery);
            timeOffRequestsCollection.addParam('end', weekEndQuery);

            timeclocksCollection.addUpstreamModel("locationId", LOCATION_ID);
            timeclocksCollection.addUpstreamModel("roleId", ROLE_ID);
            timeclocksCollection.addUpstreamModel("userId", USER_ID);
            timeclocksCollection.addParam("start", weekStartQuery);
            timeclocksCollection.addParam("end", weekEndQuery);

            primaryFetch = _.invoke([schedulesCollection, shiftsCollection, timeclocksCollection, timeOffRequestsCollection], "fetch", {error: self.error});
            $.when.apply($, primaryFetch).done(function() {

                if (schedulesCollection.models.length > 1) {
                    return self.error();
                }

                scheduleModel = schedulesCollection.first();

                if (!_.isUndefined(scheduleModel)) {
                    currentState = scheduleModel.get("state");

                    // preferences view
                    if (preferenceStates.indexOf(currentState) >= 0 &&
                       self.orgModel.isBoss()
                    ) {
                        showShifts = false;
                        self.showPreferencesView(scheduleModel, timeOffRequestsCollection);
                    }

                    // claimable shifts view
                    if (currentState == "published") {
                        unclaimedShiftsCollection = new Collections.ScheduleShifts();
                        unclaimedShiftsCollection.addUpstreamModel("locationId", LOCATION_ID);
                        unclaimedShiftsCollection.addUpstreamModel("roleId", ROLE_ID);
                        unclaimedShiftsCollection.addUpstreamModel("scheduleId", scheduleModel.id);
                        unclaimedShiftsCollection.addParam("claimable_by_user", parseInt(USER_ID));

                        self.showClaimableShifts(unclaimedShiftsCollection, scheduleModel);
                    }
                } else {
                    currentState = "unpublished";
                }

                // always render a schedule unless when preferences are to be shown
                if (showShifts) {

                    // visual graph for desktop
                    self.addDelegateView(
                        "visual-shifts-view",
                        new Views.Components.PlannerVisualShifts({
                            collection: shiftsCollection,
                            weekStartMoment: weekStartMoment,
                            timeRange: {
                                min: 0,
                                max: 24,
                            },
                        })
                    );

                    // list of shifts for mobile
                    self.addDelegateView(
                        "list-shifts-view",
                        new Views.Components.ListShiftsCard({
                            collection: shiftsCollection,
                            weekStartMoment: weekStartMoment,
                        })
                    );
                }

                // prepare the timeclocks collection
                self.showTimeclocksCard(timeclocksCollection, timeOffRequestsCollection);

            });
        },
        showClaimableShifts: function(unclaimedShiftsCollection, scheduleModel) {
            var self = this;

            unclaimedShiftsCollection.fetch({
                success: function(collection, response, opts) {

                    // add card for claiming unassigned shifts if there are any to claim
                    if (unclaimedShiftsCollection.models.length > 0) {
                        self.addDelegateView(
                            "claim-shifts-view",
                            new Views.Components.ClaimShiftsCard({
                                collection: unclaimedShiftsCollection,
                                scheduleModel: scheduleModel,
                                callback: function(model) {
                                    self.delegateViews["visual-shifts-view"].addToGraph(model);
                                },
                            })
                        );
                    }
                },
                error: self.error,
            });
        },
        // TODO
        showPreferencesView: function(scheduleModel, timeOffRequestsCollection) {
            var self = this,
                preferenceModel = new Models.Preference(),
                addPreferenceCard
            ;

            addPreferenceCard = function() {
                self.addDelegateView(
                    "preferences",
                    new Views.Components.PreferencesCardView({
                        model: preferenceModel,
                        userModel: self.userModel,
                        organizationModel: self.orgModel,
                        scheduleModel: scheduleModel,
                        locationModel: self.locationModel,
                        roleModel: self.roleModel,
                        timeOffRequestsCollection: timeOffRequestsCollection,
                    })
                );
            };

            preferenceModel.addUpstreamModel("locationId", LOCATION_ID);
            preferenceModel.addUpstreamModel("roleId", ROLE_ID);
            preferenceModel.addUpstreamModel("scheduleId", scheduleModel.id);
            preferenceModel.set('id', self.userModel.id);

            preferenceModel.fetch({
                success: function(model) {
                    addPreferenceCard();
                },
                error: function(model, response) {
                    if (response.status === 404) {
                        model.unset('id');
                        model.set('preference', Util.generateFullDayAvailability(0));
                        addPreferenceCard();
                    } else {
                        self.error();
                    }
                },
            });
        },
        showTimeclocksCard: function(timeclocksCollection, timeOffRequestsCollection) {
            var self = this,
                filteredTimeOffRequestCollection = new Collections.TimeOffRequests(
                    timeOffRequestsCollection.filter(function(model) {
                        return model.get('state') === 'sick' ||
                               model.get('state') === 'approved_paid' ||
                               model.get('state') === 'approved_unpaid'
                        ;
                    })
                )
            ;

            if (!timeclocksCollection.isEmpty() || !filteredTimeOffRequestCollection.isEmpty()) {
                self.addDelegateView(
                    "timecard-view",
                    new Views.Components.TimecardView({
                        collection: timeclocksCollection,
                        timeOffRequestsCollection: filteredTimeOffRequestCollection,
                        locationModel: self.locationModel,
                    })
                );
            }
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
                return;
            }

            // if availability card
            if (_.has(self.delegateViews, "availability-view")) {

                // if it's changed
                if (self.delegateViews["availability-view"].hasChanged()) {
                    $.notify({message:"Availability not saved."},{type:"warning"});
                    self.delegateViews["availability-view"].setChanged(false);
                }
            }

            self.currentWeek = Util.convertMomentObjToDateStr(newWeekMoment);

            return self.renderWeekView();
        },
        updateRoute: function() {
            var self = this,
                route = "week/" + self.currentWeek
            ;

            Backbone.history.navigate(route, {trigger: false});
        },
        updateWeekTitle: function() {
            // renders the title of the current week being shown

            var self = this,
                momentDate = moment(self.currentWeek),
                weekDay = momentDate.format("D MMMM YYYY"),
                weekDayMobile = momentDate.format("D MMM YYYY"),
                $weekText = $(".calendar-navigation-bar").find(".week-date-label").children(".week-title"),
                $weekTextMobile = $(".calendar-navigation-bar").find(".week-date-label-mobile").children(".week-title")
            ;

            $weekText.text("Week of " + weekDay);
            $weekTextMobile.text("Week of " + weekDayMobile);
        },
        // TODO
        getDayRangeFromDemand: function(bufferSize) {
            // window the week to when demand requests it
            // bufferSize adds additional hours to each end

            var self = this,
                minThreshold = 4,
                maxThreshold = 27,
                min = 27,
                max = 4,
                offsetHours = 4,
                tempMin,
                tempMax,
                scheduleModel = self.collection.findWhere({start: self.currentWeek})
            ;

            bufferSize = bufferSize || 0;

            // bufferSize >= 0 is true if it's 0 or more
            // strings or NaN also get assigned to false here
            if (!(bufferSize >= 0)) {
                console.log("invalid buffer size supplied");
                // seems weird, but max and min are flipped
                return {
                    min: max,
                    max: min,
                };
            }

            // look through each day in demand chart
            _.each(scheduleModel.get("demand"), function(dayDemand, index) {
                tempMin = dayDemand.firstNonZeroIndex();
                tempMax = dayDemand.lastNonZeroIndex();

                if (tempMin < min) {
                    min = tempMin;
                }

                if (tempMax > max) {
                    max = tempMax;
                }
            });

            // apply offset and buffer size
            min += offsetHours - bufferSize;
            max += offsetHours + bufferSize;

            if (min < minThreshold) {
                min = minThreshold;
            }

            if (max > maxThreshold) {
                max = maxThreshold;
            }

            return {
                min: min,
                max: max,
            };
        },
    });

    root.App.Views.PlannerControllerView = PlannerControllerView;

})(this);
