(function(root) {

    "use strict";

    var Views = root.App.Views,
        Models = root.App.Models,
        Collections = root.App.Collections,
        Util = root.App.Util
    ;

    var AttendanceDayView = Views.Base.extend({
        el: ".attendance-days-placeholder",
        events: {},
        initialize: function(opts) {
            AttendanceDayView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.date)) {
                    this.date = opts.date;
                }

                if (!_.isUndefined(opts.locationId)) {
                    this.locationId = opts.locationId;
                }

                if (!_.isUndefined(opts.locationModel)) {
                    this.locationModel = opts.locationModel;
                }

                if (!_.isUndefined(opts.orgModel)) {
                    this.orgModel = opts.orgModel;
                }

                if (!_.isUndefined(opts.rolesCollection)) {
                    this.rolesCollection = opts.rolesCollection;
                }

                if (!_.isUndefined(opts.sendTimeclockToOtherDayCallback)) {
                    this.sendTimeclockToOtherDayCallback = opts.sendTimeclockToOtherDayCallback;
                }

                if (!_.isUndefined(opts.updateSummaryCardCallback)) {
                    this.updateSummaryCardCallback = opts.updateSummaryCardCallback;
                }
            }
        },
        render: function(opts) {
            var self = this,
                cardSelector = "#attendance-" + self.date,
                today = moment().format("YYYY-MM-DD"),
                renderCardData = {
                    title: moment(self.date).format("dddd, D MMMM YYYY"),
                    date: self.date,
                    inFuture: moment(self.date) > moment(today),
                }
            ;

            self.$el.append(ich.attendance_day_card(renderCardData));

            self.renderTable();

            // collapse/expand events
            this.$(cardSelector).on('show.bs.collapse', function (event) {
                var $target = $(event.target),
                    collapseId = $target.data('collapse-id'),
                    selector = '.collapse-btn-' + collapseId
                ;

                $(selector).find('.glyphicon').removeClass('glyphicon-chevron-down').addClass('glyphicon-chevron-up');
            });

            this.$(cardSelector).on('hide.bs.collapse', function (event) {
                var $target = $(event.target),
                    collapseId = $target.data('collapse-id'),
                    selector = '.collapse-btn-' + collapseId
                ;

                $(selector).find('.glyphicon').removeClass('glyphicon-chevron-up').addClass('glyphicon-chevron-down');
            });

            this.$(cardSelector + " .new-timeclock-btn").click(function(event) {
                self.newTimeclock(event);
            });

            return this;
        },
        renderTable: function() {
            var self = this,
                renderData = {
                    content: _.map(self.collection.models, function(model) {
                        var roleModel = self.rolesCollection.get(model.get("role_id")),
                            roleName = roleModel.get("name"),
                            userObj = _.findWhere(roleModel.get("users"), {id: model.get("user_id")}),
                            userDisplayName = _.isNull(userObj.name) ? userObj.email : userObj.name,
                            timezone = self.locationModel.get("timezone"),
                            timeOffRequest = model.get("time_off_requests"),
                            shifts = [],
                            totalExpected = 0,
                            inPast = false,
                            timeclocks = [],
                            totalTime = 0,
                            sick = false,
                            unpaid = false,
                            paid = false,
                            denied = false
                        ;

                        if (!(_.isNull(timeOffRequest) || _.isUndefined(timeOffRequest))) {
                            switch (timeOffRequest.state) {
                                case "approved_paid":
                                    paid = true;
                                    break;

                                case "approved_unpaid":
                                    unpaid = true;
                                    break;

                                case "sick":
                                    sick = true;
                                    break;

                                case "denied":
                                    denied = true;
                                    break;
                            }

                            totalTime += timeOffRequest.minutes_paid * 60 * 1000;
                        }

                        // summarize for shifts
                        _.each(model.get("shifts"), function(shift) {
                            var start = moment.utc(shift.start).tz(timezone),
                                stopUTC = moment.utc(shift.stop),
                                stop = stopUTC.tz(timezone),
                                duration = start.preciseDiff(start)
                            ;

                            totalExpected += stop.diff(start);

                            shifts.push({
                                start: start.format("hh:mm A"),
                                stop: stop.format("hh:mm A"),
                                id: shift.id,
                            });

                            // if at least one shift is in past, we can show the button
                            if (!inPast && stopUTC.isBefore(moment.utc())) {
                                inPast = true
                            }
                        });

                        // summarize timeclocks
                        _.each(model.get("timeclocks"), function(timeclock) {
                            var start = moment.utc(timeclock.start).tz(timezone),
                                stop = moment.utc(timeclock.stop).tz(timezone),
                                duration = start.preciseDiff(start)
                            ;

                            totalTime += stop.diff(start);

                            timeclocks.push({
                                id: timeclock.id,
                                user_id: timeclock.user_id,
                                role_id: timeclock.role_id,
                                start: start.format("hh:mm A"),
                                stop: stop.format("hh:mm A"),
                                duration: duration,
                            });
                        });

                        return {
                            roleId: model.get("role_id"),
                            roleName: roleName,
                            userDisplayName: userDisplayName,
                            userId: model.get("user_id"),
                            shifts: shifts,
                            timeclocks: timeclocks,
                            inPast: inPast,
                            timeOffRequest: timeOffRequest,
                            sick: sick,
                            unpaid: unpaid,
                            paid: paid,
                            denied: denied,
                            totalExpected: moment(0).preciseDiff(totalExpected),
                            totalTime: moment(0).preciseDiff(totalTime),
                        };
                    }),
                },
                tableSelector = "#attendance-table-" + self.date
            ;

            // remove any old events before enabling new ones
            $(tableSelector + " .clickable").off();
            $(tableSelector + " .new-timeclock").off();

            // set/update the html
            $(tableSelector).html(ich.attendance_day_table(renderData));

            // add events for clicking on timeclock - this is specific to only this card
            $(tableSelector + " .clickable").click(function(e) {
                self.editTimeclock(e);
            });

            $(tableSelector + " .new-timeclock").click(function(e) {
                self.newTimeclock(e);
            });

            $(tableSelector + " .edit-time-off-request").click(function(e) {
                self.editTimeOffRequest(e);
            });
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
                firstShift
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
                    el: ".modal-placeholder-" + self.date,
                    id: "new-" + self.date,
                    locationId: self.locationId,
                    locationModel: self.locationModel,
                    rolesCollection: self.rolesCollection,
                    date: self.date,
                    mode: "new",
                    userId: userId,
                    roleId: roleId,
                    suggestedTimes: suggestedTimes,
                    saveTimeclockCallback: function(model, addSeconds, subtractSeconds) {
                        var startLocalMoment = moment.utc(model.get("start")).tz(self.locationModel.get("timezone")),
                            isoDate = startLocalMoment.format("YYYY-MM-DD")
                        ;

                        // model's start is on same day as it was
                        if (isoDate === self.date) {
                            self.addTimeclockOnDay(model);
                        }

                        // model's start day is different
                        else {
                            self.sendTimeclockToOtherDayCallback(isoDate, model);
                            self.removeTimeclockFromDay(model.get("id"), model.get("role_id"), model.get("user_id"));
                        }

                        self.updateSummaryCardCallback(isoDate, model.get("user_id"), model.get("role_id"), addSeconds, subtractSeconds, 1);
                    },
                })
            );
        },
        editTimeclock: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target).closest(".clickable"),
                roleId = parseInt($target.attr("data-role-id")),
                userId = parseInt($target.attr("data-user-id")),
                roleId = parseInt($target.attr("data-role-id")),
                timeclockId = parseInt($target.attr("data-id")),
                userDayObj = self.collection.findWhere({user_id: userId, role_id: roleId}),
                timeclock = _.findWhere(userDayObj.get("timeclocks"), {id: timeclockId}),
                timeclockModel = new Models.Timeclock(timeclock)
            ;

            // add upstream models
            timeclockModel.addUpstreamModel("locationId", self.locationId);
            timeclockModel.addUpstreamModel("roleId", roleId);
            timeclockModel.addUpstreamModel("userId", userId);

            self.addDelegateView(
                "modal-view-" + timeclockId,
                new Views.Components.TimeclockModalView({
                    el: ".modal-placeholder-" + self.date,
                    model: timeclockModel,
                    id: timeclockId,
                    locationId: self.locationId,
                    locationModel: self.locationModel,
                    rolesCollection: self.rolesCollection,
                    mode: "edit",
                    date: self.date,
                    saveTimeclockCallback: function(model, addSeconds, subtractSeconds) {
                        var startLocalMoment = moment.utc(model.get("start")).tz(self.locationModel.get("timezone")),
                            isoDate = startLocalMoment.format("YYYY-MM-DD")
                        ;

                        // model's start is on same day as it was
                        if (isoDate === self.date) {
                            self.addTimeclockOnDay(model);
                        }

                        // model's start day is different
                        else {
                            self.sendTimeclockToOtherDayCallback(isoDate, model);
                            self.removeTimeclockFromDay(model.get("id"), model.get("role_id"), model.get("user_id"));
                        }

                        self.updateSummaryCardCallback(isoDate, model.get("user_id"), model.get("role_id"), addSeconds, subtractSeconds);

                    },
                    deleteTimeclockCallback: function(timeclockId, userId, roleId, subtractSeconds) {
                        self.removeTimeclockFromDay(timeclockId, roleId, userId);
                        self.updateSummaryCardCallback(self.date, userId, roleId, 0, subtractSeconds, -1);
                    },
                })
            );
        },
        editTimeOffRequest: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target),
                roleId = parseInt($target.attr("data-role-id")),
                userId = parseInt($target.attr("data-user-id")),
                timeOffRequestId = parseInt($target.attr("data-id")),
                userDayObj = self.collection.findWhere({user_id: userId, role_id: roleId}),
                timeOffRequest = userDayObj.get("time_off_requests"),
                timeOffRequestModel = new Models.TimeOffRequest(timeOffRequest),
                roleModel = self.rolesCollection.get(roleId),
                roleName = roleModel.get("name"),
                userObj = _.findWhere(roleModel.get("users"), {id: userId}),
                userDisplayName = _.isNull(userObj.name) ? userObj.email : userObj.name
            ;

            // add upstream models
            timeOffRequestModel.addUpstreamModel("locationId", self.locationId);
            timeOffRequestModel.addUpstreamModel("roleId", roleId);
            timeOffRequestModel.addUpstreamModel("userId", userId);

            self.addDelegateView(
                "time-off-request-modal-view-" + timeOffRequestId,
                new Views.Components.TimeOffRequestEditModalView({
                    el: ".modal-placeholder-" + self.date,
                    model: timeOffRequestModel,
                    id: timeOffRequestId,
                    locationModel: self.locationModel,
                    date: self.date,
                    userDisplayName: userDisplayName,
                    roleName: roleName,
                    saveCallback: function(model, addSeconds, subtractSeconds) {
                        var dayModel = self.collection.findWhere({user_id: model.get("user_id"), role_id: model.get("role_id")});

                        dayModel.set("time_off_requests", model.attributes);
                        self.updateSummaryCardCallback(self.date, model.get("user_id"), model.get("role_id"), addSeconds, subtractSeconds);

                        self.renderTable();

                    },
                    deleteCallback: function(userId, roleId, subtractSeconds) {
                        self.removeTimeOffRequestFromDay(roleId, userId);
                        self.updateSummaryCardCallback(self.date, userId, roleId, 0, subtractSeconds);
                    },
                })
            );
        },
        addTimeclockOnDay: function(timeclockModel) {
            var self = this,
                dayModel = self.collection.findWhere({user_id: timeclockModel.get("user_id"), role_id: timeclockModel.get("role_id")}),
                timeclocks,
                timeclockIndex
            ;

            // this user has no records for this day, add a whole new model
            if (_.isUndefined(dayModel)) {
                self.collection.add(
                    new Models.Base({
                        user_id: timeclockModel.get("user_id"),
                        role_id: timeclockModel.get("role_id"),
                        shifts: [],
                        timeclocks: [timeclockModel.attributes],
                    })
                );
            }

            // this user has a model for this day, add or update just the timeclock
            else {

                // check if timeclock id exists
                timeclocks = dayModel.get("timeclocks");
                timeclockIndex = timeclocks.getIndexBy("id", timeclockModel.get("id"));

                // it exists - update it
                if (timeclockIndex > -1) {
                    timeclocks.splice(timeclockIndex, 1);
                    timeclocks.splice(timeclockIndex, 0, timeclockModel.attributes);
                }

                // it's new - add it
                else {
                    timeclocks.push(timeclockModel.attributes);
                }

                dayModel.set("timeclocks", timeclocks);
            }

            // update the view now
            self.renderTable();
        },
        removeTimeclockFromDay: function(timeclockId, roleId, userId) {
            var self = this,
                model = self.collection.findWhere({user_id: userId, role_id: roleId}),
                timeclocks = model.get("timeclocks"),
                timeclockIndex,
                renderData
            ;

            // only remove this timeclock record
            if (timeclocks.length > 1 ||
                model.get("shifts").length > 0 ||
                !_.isNull(model.get("time_off_requests"))
            ) {
                timeclockIndex = timeclocks.getIndexBy("id", timeclockId);
                timeclocks.splice(timeclockIndex, 1);
                model.set("timeclocks", timeclocks);
            }

            // remove the whole record/user day
            else {
                self.collection.remove(model);
            }

            // update the view now
            self.renderTable();
        },
        removeTimeOffRequestFromDay: function(roleId, userId) {
            var self = this,
                model = self.collection.findWhere({user_id: userId, role_id: roleId}),
                timeOffRequest = model.get("time_off_requests"),
                renderData
            ;

            // only remove this record
            if (model.get("timeclocks").length > 0 ||
                model.get("shifts").length > 0
            ) {
                model.set("time_off_requests", null);
            }

            // remove the whole record/user day
            else {
                self.collection.remove(model);
            }

            // update the view now
            self.renderTable();
        },
    });

    root.App.Views.AttendanceDayView = AttendanceDayView;

})(this);
