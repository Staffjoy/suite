(function(root) {

    "use strict";

    var Collections = root.App.Collections,
        Models = root.App.Models,
        Views = root.App.Views,
        Util = root.App.Util
    ;

    var TimeOffRequestEditModalView = Views.Base.extend({
        el: ".modal-placeholder-time-off-requests",
        events: {
            "click .select-state .dropdown-selection": "changeState",
        },
        initialize: function(opts) {
            TimeOffRequestEditModalView.__super__.initialize.apply(this);

            // thank you stack overflow - modal events don't play nice with the select2 text search
            $.fn.modal.Constructor.prototype.enforceFocus = function() {};

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.el)) {
                    this.el = opts.el;
                    this.$el = $(this.el);
                }

                if (!_.isUndefined(opts.id)) {
                    this.id = opts.id;
                }

                if (!_.isUndefined(opts.locationModel)) {
                    this.locationModel = opts.locationModel;
                }

                if (!_.isUndefined(opts.date)) {
                    this.date = opts.date;
                }

                if (!_.isUndefined(opts.userDisplayName)) {
                    this.userDisplayName = opts.userDisplayName;
                }

                if (!_.isUndefined(opts.roleName)) {
                    this.roleName = opts.roleName;
                }

                if (!_.isUndefined(opts.saveCallback) && _.isFunction(opts.saveCallback)) {
                    this.saveCallback = opts.saveCallback;
                }

                if (!_.isUndefined(opts.deleteCallback) && _.isFunction(opts.deleteCallback)) {
                    this.deleteCallback = opts.deleteCallback;
                }
            }

            this.modal;
            this.hoursPaid;
            this.state;
            this.createButton;
            this.deleteButton;
        },
        render: function(opts) {
            var self = this,
                state = self.model.get("state"),
                data = {
                    id: self.id,
                    hoursPaid: Math.ceil(self.model.get("minutes_paid") / 60 * 100) / 100,
                    disabled: state === "denied",
                    roleName: self.roleName,
                    userDisplayName: self.userDisplayName,
                    displayDate: moment(self.date).format("dddd, D MMMM YYYY")
                }
            ;

            if (state === "approved_unpaid" || state === "approved_paid") {
                state = "approved";
            }

            data["state"] = state;

            self.$el.html(ich.modal_edit_time_off_request(data));

            self.modal = $("#TimeOffRequestModal-" + self.id);
            self.modal.modal();

            self.createButton = $("#edit-time-off-request-save-button-" + self.id);
            self.createButton.click(function(event) {
                self.saveTimeOffRequest(event);
            });

            self.deleteButton = $("#edit-time-off-request-delete-button-" + self.id);
            self.deleteButton.click(function(event) {
                self.deleteTimeOffRequest(event);
            });

            self.hoursPaid = $(".edit-hours-paid-" + self.id);
            self.state = $("#time-off-request-state-" + self.id);

            self.hoursPaid.blur(function(e) {
                self.parseHoursPaid(e);
            });

            self.hoursPaid.keyup(function(e) {
                // keyCode 13 is the enter key
                if (e.keyCode == 13) {
                    $(e.target).blur();
                }
            });
        },
        deleteTimeOffRequest: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                success,
                error
            ;

            success = function(model, response) {
                $.notify({message: "Deleted time off request"}, {type:"success"});
                self.deleteCallback(self.model.get("user_id"), self.model.get("role_id"), self.model.get("minutes_paid") * 60);
                self.modal.modal("hide");
            };

            error = function(model, response) {
                $.notify({message: "Unable to delete time off request. Please contact support if the problem persists."},{type:"danger"});
            };

            self.model.destroy(
                {
                    success: success,
                    error: error,
                }
            );
        },
        saveTimeOffRequest: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                state = self.state.attr("data-value"),
                hoursPaid = self.hoursPaid.val(),
                minutesPaid = Math.floor(hoursPaid * 60),
                originalDuration = self.model.get("minutes_paid") * 60,
                newDuration = minutesPaid * 60,
                success,
                error,
                params = {
                    minutes_paid: minutesPaid,
                }
            ;

            if (state == "approved") {
                params["state"] = minutesPaid > 0 ? "approved_paid" : "approved_unpaid";
            } else {
                params["state"] = state;
            }

            success = function(model, response) {
                $.notify({message: "Updated time off request created"}, {type:"success"});
                self.saveCallback(model, newDuration, originalDuration);
                self.modal.modal("hide");
            };

            error = function(model, response) {
                $.notify({message: "Unable to save time off request. Please contact support if the problem persists."},{type:"danger"});
            };

            self.model.save(
                params,
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
                value = $target.attr("data-value")
            ;

            self.state.find(".text").text($target.text());
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

    root.App.Views.Components.TimeOffRequestEditModalView = TimeOffRequestEditModalView;

})(this);
