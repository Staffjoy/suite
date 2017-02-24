(function(root) {

    "use strict";

    var Collections = root.App.Collections,
        Models = root.App.Models,
        Views = root.App.Views,
        Util = root.App.Util
    ;

    var TimeOffRequestModalView = Views.Base.extend({
        el: ".modal-placeholder-time-off-requests",
        events: {
            "click .select-state .dropdown-selection": "changeState",
            "blur .new-time-off-request-hours-paid": "parseHoursPaid",
        },
        initialize: function(opts) {
            TimeOffRequestModalView.__super__.initialize.apply(this);

            // thank you stack overflow - modal events don't play nice with the select2 text search
            $.fn.modal.Constructor.prototype.enforceFocus = function() {};

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.locationModel)) {
                    this.locationModel = opts.locationModel;
                }

                if (!_.isUndefined(opts.rolesUsersCollection)) {
                    this.rolesUsersCollection = opts.rolesUsersCollection;
                }

                if (!_.isUndefined(opts.currentWeek)) {
                    this.currentWeek = opts.currentWeek;
                }

                if (!_.isUndefined(opts.callback) && _.isFunction(opts.callback)) {
                    this.callback = opts.callback;
                }
            }

            this.modal;
            this.selectWorker;
            this.datetimepicker;
            this.hoursPaid;
            this.state;
            this.displayFormat = "MM-DD-YYYY";
            this.createButton;
        },
        render: function(opts) {
            var self = this,
                select2data = [],
                data = {}
            ;

            self.$el.html(ich.modal_new_time_off_request(data));

            self.modal = $("#TimeOffRequestModal");
            self.modal.modal();

            _.each(self.rolesUsersCollection.models, function(model) {
                _.each(model.get("users"), function(userObj) {
                    if (!userObj.archived) {
                        select2data.push({
                            id: model.get("id") + "-" + userObj.id,   // roleId-userId
                            text: (_.isNull(userObj.name) ? userObj.email : userObj.name) + " - (" + model.get("name") + ")",
                        });
                    }
                });
            });

            self.selectWorker = $(".select-worker-time-off-request")
            self.selectWorker.select2({data: select2data});

            // initialize timepicker
            self.datetimepicker = $("#datetimepicker").datetimepicker({
                defaultDate: moment(self.currentWeek),
                format: self.displayFormat,
            });

            self.createButton = $(".time-off-request-create-btn");
            self.createButton.click(function(event) {
                self.createTimeOffRequest(event);
            });

            self.hoursPaid = $(".new-time-off-request-hours-paid");
            self.state = $("#new-time-off-request-state");

            self.hoursPaid.keyup(function(e) {
                // keyCode 13 is the enter key
                if (e.keyCode == 13) {
                    $(e.target).blur();
                }
            });
        },
        createTimeOffRequest: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                timeOffRequestModel = new Models.TimeOffRequest(),
                date = moment(self.datetimepicker.data("date"), self.displayFormat).format("YYYY-MM-DD"),
                state = self.state.attr("data-value"),
                hoursPaid = self.hoursPaid.val(),
                minutesPaid = Math.floor(hoursPaid * 60),
                success,
                error,
                params = {
                    minutes_paid: minutesPaid,
                    date: date,
                },
                selectedIds = self.selectWorker.select2().val().split("-"),
                roleId = parseInt(selectedIds[0]),
                userId = parseInt(selectedIds[1]),
                roleModel = self.rolesUsersCollection.findWhere({id: roleId}),
                userObj = _.findWhere(roleModel.get("users"), {id: userId}),
                userName = _.isUndefined(userObj.name) ? userObj.email : userObj.name
            ;

            if (state == "approved") {
                params["state"] = minutesPaid > 0 ? "approved_paid" : "approved_unpaid";
            } else {
                params["state"] = state;
            }

            // add upstream models
            timeOffRequestModel.addUpstreamModel("locationId", self.locationModel.id);
            timeOffRequestModel.addUpstreamModel("roleId", roleId);
            timeOffRequestModel.addUpstreamModel("userId", userId);

            timeOffRequestModel.createRequest();

            success = function(model, response) {
                $.notify({message: "Time off request created"}, {type:"success"});
                self.callback(model);
                self.modal.modal("hide");
            };

            error = function(model, response) {
                $.notify({message: userName + " already has a time off request on this day."},{type:"warning"});
                self.modal.modal("hide");
            };

            timeOffRequestModel.save(
                params,
                {
                    success: success,
                    error: error,
                }
            );
        },
        changeState: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target),
                value = $target.attr("data-value")
            ;

            self.state.text($target.text());
            self.state.attr("data-value", value);
            self.state.dropdown("toggle");

            if (value == "denied") {
                self.hoursPaid.val(0);
                self.hoursPaid.attr("disabled", "disabled");
            } else {
                self.hoursPaid.removeAttr("disabled");
            }
        },
        parseHoursPaid: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                value = Util.adjustToDecimalPoint(parseFloat(self.hoursPaid.val()), 2, true, 24)
            ;

            self.hoursPaid.val(value);
        },
    });

    root.App.Views.Components.TimeOffRequestModalView = TimeOffRequestModalView;

})(this);
