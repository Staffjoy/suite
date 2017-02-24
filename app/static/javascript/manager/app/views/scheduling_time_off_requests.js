(function(root) {

    "use strict";

    var Views = root.App.Views,
        Models = root.App.Models,
        Util = root.App.Util
    ;

    var SchedulingTimeOffRequestsCardView = Views.Base.extend({
        el: ".time-off-requests-card-placeholder",
        events: {
            "click .new-time-off-request-btn": "timeOffRequestModal",
            "blur .hours-paid": "adjustHoursPaid",
            "click .time-off-status": "answerRequest",
            "change .select-state": "changeState",
        },
        close: function() {
            $(".hours-paid").off();
            SchedulingTimeOffRequestsCardView.__super__.close.call(this);
        },
        initialize: function(opts) {
            SchedulingTimeOffRequestsCardView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.locationModel)) {
                    this.locationModel = opts.locationModel;
                }

                if (!_.isUndefined(opts.rolesUsersCollection)) {
                    this.rolesUsersCollection = opts.rolesUsersCollection;
                }

                if (!_.isUndefined(opts.collapsed)) {
                    this.collapsed = opts.collapsed;
                }

                if (!_.isUndefined(opts.timeOffRequests)) {
                    this.timeOffRequests = opts.timeOffRequests;
                }

                if (!_.isUndefined(opts.currentWeek)) {
                    this.currentWeek = opts.currentWeek;
                }
            }
        },
        render: function(opts) {
            var self = this,
                data = {
                    collapsed: self.collapsed,
                }
            ;

            // collapse/expand events
            self.$el.on('show.bs.collapse', function (event) {
                var $target = $(event.target),
                    collapseId = $target.data('collapse-id'),
                    selector = '.collapse-btn-time-off-requests'
                ;

                $(selector).find('.glyphicon').removeClass('glyphicon-chevron-down').addClass('glyphicon-chevron-up');
            });

            self.$el.on('hide.bs.collapse', function (event) {
                var $target = $(event.target),
                    collapseId = $target.data('collapse-id'),
                    selector = '.collapse-btn-time-off-requests'
                ;

                $(selector).find('.glyphicon').removeClass('glyphicon-chevron-up').addClass('glyphicon-chevron-down');
            });

            self.$el.html(ich.scheduling_time_off_requests_card(data));
            self.renderTable();

            return this;
        },
        renderTable: function() {
            var self = this,
                data = []
            ;

            $(".hours-paid").off();

            _.each(self.timeOffRequests, function(timeOffRequestCollection) {
                _.each(timeOffRequestCollection.models, function(model) {
                    var roleCollection = self.rolesUsersCollection.get(model.get("role_id")),
                        roleName = roleCollection.get("name"),
                        users = roleCollection.get("users"),
                        user = _.findWhere(users, {id: model.get("user_id")}),
                        displayName = _.isNull(user.name) ? user.email : user.name,
                        date = moment.utc(model.get("start")).tz(self.locationModel.get("timezone")),
                        displayDate = date.format("M/D"),
                        state = model.get("state"),
                        displayState,
                        needsApproval = _.isNull(state),
                        denied = state === "denied",
                        hoursPaid = Math.ceil(model.get("minutes_paid") / 60 * 100) / 100,
                        displayState = "Unassigned",
                        approved = false,
                        sick = state === "sick"
                    ;

                    if (state === "approved_unpaid" || state === "approved_paid") {
                        approved = true;
                    }

                    data.push({
                        id: model.id,
                        roleId: model.get("role_id"),
                        userId: model.get("user_id"),
                        displayDate: displayDate,
                        roleName: roleName,
                        displayName: displayName,
                        displayState: displayState,
                        approved: approved,
                        sick: sick,
                        date: date,
                        denied: denied,
                        needsApproval: needsApproval,
                        hoursPaid: hoursPaid,
                    });
                });
            });

            data.sort(function(a, b) {
                if (a.displayName !== b.displayName) {
                    return a.displayName > b.displayName ? 1 : -1;
                }

                return a.date >= b.date ? 1 : -1;
            });

            $("#time-off-requests-table").html(ich.scheduling_time_off_requests_table({data: data}));

            // if enter key is pressed, force a blur function
            $(".hours-paid").keyup(function(e) {
                // keyCode 13 is the enter key
                if (e.keyCode == 13) {
                    $(e.target).blur();
                }
            });
        },
        adjustHoursPaid: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target),
                $row = $target.closest(".time-off-request-row"),
                id = $row.data("id"),
                roleId = $row.data("role-id"),
                userId = $row.data("user-id"),
                value = Util.adjustToDecimalPoint(parseFloat($target.val()), 2, true, 24),
                minutesPaid = Math.floor(value * 60),
                requestRoleIndex = -1,
                requestModel,
                error = function(collection, response, opts) {
                    $.notify({message:"An error has occurred, please contact support if the problem persists."},{type: "danger"});
                },
                success,
                payload = {minutes_paid: minutesPaid},
                requestState
            ;

            // update input entry after parsing
            $target.text(value);
            $target.val(value);

            // get the collection we are working with
            for (var i=0; i < self.timeOffRequests.length; i++) {
                if (self.timeOffRequests[i].getUpstreamModelId("roleId") == roleId) {
                    requestRoleIndex = i;
                }
            }

            // make sure we have it
            if (requestRoleIndex < 0) {
                return error();
            }

            // now get time off request model
            requestModel = self.timeOffRequests[requestRoleIndex].get(id);
            requestState = requestModel.get("state");

            // don't save if no changes made
            if (requestModel.get("minutes_paid") === minutesPaid) {
                return;
            }

            // make a patch request if state has been set, and check for minutes_paid issues
            if (!_.isNull(requestState)) {
                if (minutesPaid === 0 && requestState === "approved_paid") {
                    payload["state"] = "approved_unpaid";
                }

                if (minutesPaid > 0 && requestState === "approved_unpaid") {
                    payload["state"] = "approved_paid";
                }

            // do nothing if request hasn't been responded to yet
            } else {
                return;
            }

            // prepare model for a patch
            requestModel.addUpstreamModel("locationId", self.locationModel.id);
            requestModel.addUpstreamModel("roleId", roleId);
            requestModel.addUpstreamModel("userId", userId);

            success = function(collection, response, opts) {
                $.notify({message:"Saved hours paid."},{type: "success"});
            };

            requestModel.save(
                payload,
                {
                    success: success,
                    error: error,
                    patch: true,
                }
            );
        },
        answerRequest: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target),
                type = $target.data("state"),
                $row = $target.closest(".time-off-request-row"),
                $hoursPaid = $row.find(".hours-paid"),
                hoursPaid = Util.adjustToDecimalPoint(parseFloat($hoursPaid.val()), 2, true, 24),
                minutesPaid = Math.floor(hoursPaid * 60),
                payload,
                id = $row.data("id"),
                roleId = $row.data("role-id"),
                userId = $row.data("user-id"),
                requestRoleIndex = -1,
                requestModel,
                success,
                error = function(collection, response, opts) {
                    $.notify({message:"An error has occurred, please contact support if the problem persists."},{type: "danger"});
                }
            ;

            // construct payload
            if (type === "denied") {
                payload = {
                    minutes_paid: 0,
                    state: "denied",
                }
            } else {
                payload = {
                    minutes_paid: minutesPaid,
                }

                if (minutesPaid > 0) {
                    payload["state"] = "approved_paid";
                } else {
                    payload["state"] = "approved_unpaid";
                }
            }

            // get the collection we are working with
            for (var i=0; i < self.timeOffRequests.length; i++) {
                if (self.timeOffRequests[i].getUpstreamModelId("roleId") == roleId) {
                    requestRoleIndex = i;
                }
            }

            // make sure we have it
            if (requestRoleIndex < 0) {
                return error();
            }

            // now get time off request model
            requestModel = self.timeOffRequests[requestRoleIndex].get(id);

            // prepare model for a patch
            requestModel.addUpstreamModel("locationId", self.locationModel.id);
            requestModel.addUpstreamModel("roleId", roleId);
            requestModel.addUpstreamModel("userId", userId);

            success = function(collection, response, opts) {
                $.notify({message:"Saved hours paid."},{type: "success"});
                self.renderTable();
            };

            requestModel.save(
                payload,
                {
                    success: success,
                    error: error,
                    patch: true,
                }
            );
        },
        changeState: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target),
                state = $target.val(),
                $row = $target.closest(".time-off-request-row"),
                $hoursPaid = $row.find(".hours-paid"),
                hoursPaid = Util.adjustToDecimalPoint(parseFloat($hoursPaid.val()), 2, true, 24),
                minutesPaid = Math.floor(hoursPaid * 60),
                payload,
                id = $row.data("id"),
                roleId = $row.data("role-id"),
                userId = $row.data("user-id"),
                requestRoleIndex = -1,
                requestModel,
                success,
                error = function(collection, response, opts) {
                    $.notify({message:"An error has occurred, please contact support if the problem persists."},{type: "danger"});
                }
            ;

            // construct payload
            if (state === "denied") {
                payload = {
                    minutes_paid: 0,
                    state: "denied",
                }
            } else if (state === "sick") {
                payload = {
                    state: "sick",
                }
            } else {
                if (minutesPaid > 0) {
                    payload = {state: "approved_paid"};
                } else {
                    payload = {state: "approved_unpaid"};
                }
            }

            // get the collection we are working with
            for (var i=0; i < self.timeOffRequests.length; i++) {
                if (self.timeOffRequests[i].getUpstreamModelId("roleId") == roleId) {
                    requestRoleIndex = i;
                }
            }

            // make sure we have it
            if (requestRoleIndex < 0) {
                return error();
            }

            // now get time off request model
            requestModel = self.timeOffRequests[requestRoleIndex].get(id);

            // prepare model for a patch
            requestModel.addUpstreamModel("locationId", self.locationModel.id);
            requestModel.addUpstreamModel("roleId", roleId);
            requestModel.addUpstreamModel("userId", userId);

            success = function(collection, response, opts) {
                $.notify({message:"Updated time off request."},{type: "success"});

                if (state === "denied") {
                    $hoursPaid.text(0);
                    $hoursPaid.val(0);
                    $hoursPaid.attr("disabled", "disabled");
                } else {
                    $hoursPaid.removeAttr("disabled");
                }
            };

            requestModel.save(
                payload,
                {
                    success: success,
                    error: error,
                    patch: true,
                }
            );

        },
        addTimeOffRequestToTable: function(model) {
            var self = this,
                timezone = self.locationModel.get("timezone"),
                requestStartMomentLocal = moment.utc(model.get("start")).tz(timezone),
                weekStartMoment = moment.tz(self.currentWeek, timezone),
                weekEndMoment = moment.tz(self.currentWeek, timezone).add(7, "days"),
                roleIndex = -1
            ;

            if (requestStartMomentLocal.isSameOrAfter(weekStartMoment) &&
                requestStartMomentLocal.isBefore(weekEndMoment)
            ) {
                for (var i=0; i < self.timeOffRequests.length; i++) {
                    if (self.timeOffRequests[i].getUpstreamModelId("roleId") == model.get("role_id")) {
                        roleIndex = i;
                    }
                }

                if (roleIndex < 0) {
                    error();
                }

                self.timeOffRequests[roleIndex].add(model);
                self.renderTable();
            }
        },
        timeOffRequestModal: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this;

            self.addDelegateView(
                "new-time-off-request-modal",
                new Views.Components.TimeOffRequestModalView({
                    rolesUsersCollection: self.rolesUsersCollection,
                    locationModel: self.locationModel,
                    currentWeek: self.currentWeek,
                    callback: function(model) {
                        self.addTimeOffRequestToTable(model);
                    }
                })
            );

            $("#TimeOffRequestModal").on("hidden.bs.modal", function(e) {
                self.delegateViews["new-time-off-request-modal"].close();
            });
        },
    });

    root.App.Views.SchedulingTimeOffRequestsCardView = SchedulingTimeOffRequestsCardView;

})(this);
