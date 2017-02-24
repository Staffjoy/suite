(function(root) {

    "use strict";

    var Collections = root.App.Collections,
        Models = root.App.Models,
        Views = root.App.Views,
        Util = root.App.Util
    ;

    var TimeclockModalView = Views.Base.extend({
        el: ".modal-placeholder",
        events: {},
        initialize: function(opts) {
            TimeclockModalView.__super__.initialize.apply(this);

            // thank you stack overflow - modal events don't play nice with the select2 text search
            $.fn.modal.Constructor.prototype.enforceFocus = function() {};

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.id)) {
                    this.id = opts.id;
                }

                if (!_.isUndefined(opts.day)) {
                    this.date = opts.date;
                }

                if (!_.isUndefined(opts.el)) {
                    this.el = opts.el;
                }

                if (!_.isUndefined(opts.locationId)) {
                    this.locationId = opts.locationId;
                }

                if (!_.isUndefined(opts.userId)) {
                    this.userId = opts.userId;
                }

                if (!_.isUndefined(opts.roleId)) {
                    this.roleId = opts.roleId;
                }

                if (!_.isUndefined(opts.locationModel)) {
                    this.locationModel = opts.locationModel;
                }

                if (!_.isUndefined(opts.mode)) {
                    this.mode = opts.mode;
                }

                if (!_.isUndefined(opts.rolesCollection)) {
                    this.rolesCollection = opts.rolesCollection;
                }

                if (!_.isUndefined(opts.deleteTimeclockCallback)) {
                    this.deleteTimeclockCallback = opts.deleteTimeclockCallback;
                }

                if (!_.isUndefined(opts.saveTimeclockCallback)) {
                    this.saveTimeclockCallback = opts.saveTimeclockCallback;
                }

                if (!_.isUndefined(opts.suggestedTimes)) {
                    this.suggestedTimes = opts.suggestedTimes;
                } else {
                    this.suggestedTimes = {
                        start: moment(opts.date).add(9, "hours"),
                        stop: moment(opts.date).add(17, "hours"),
                    };
                }

                this.startDatetimepicker;
                this.stopDatetimepicker;
                this.durationText;
                this.durationWarning;
                this.saveButton;
                this.modal;
                this.displayFormat = "hh:mm:ss A  MM-DD-YYYY";
            }
        },
        render: function(opts) {
            var self = this,
                $el = $(self.el),
                start,
                stop,
                timezone = self.locationModel.get("timezone"),
                data = {
                    id: self.id,
                    newTimeclockMode: self.mode === "new",
                }
            ;

            // if editing, it should be prepopulated
            if (self.mode === "edit") {
                data.title = "Edit timeclock";

                start = moment.utc(self.model.get("start")).tz(timezone);
                stop = moment.utc(self.model.get("stop")).tz(timezone);
            }

            // otherwise use the suggested times
            else {
                start = self.suggestedTimes.start;
                stop = self.suggestedTimes.stop;
            }

            // need to include user picker
            if (self.mode === "new") {
                data.title = "New timeclock";

                if (_.isNaN(self.userId)) {
                    data.userSelection = true;
                } else {
                    var roleModel = self.rolesCollection.get(self.roleId),
                        users = roleModel.get("users"),
                        userObj = _.findWhere(users, {id: self.userId})
                    ;

                    data.selectedUser = {
                        name: _.isNull(userObj.name) ? userObj.email : userObj.name,
                        role: roleModel.get("name"),
                        roleId: self.roleId,
                        userId: self.userId,
                    }
                }
            }

            $el.html(ich.modal_edit_timeclock(data));

            self.modal = $("#TimeclockModal-" + self.id);
            self.modal.modal();

            // add a select2 selector if the new timeclock button was pushed
            if (data.userSelection) {
                var select2data = [],
                    selected = true
                ;

                _.each(self.rolesCollection.models, function(model) {
                    _.each(model.get("users"), function(userObj) {
                        select2data.push({
                            id: model.get("id") + "-" + userObj.id,   // roleId-userId
                            text: (_.isNull(userObj.name) ? userObj.email : userObj.name) + " - (" + model.get("name") + ")",
                            selected: selected,
                        });

                        selected = false;
                    });
                });

                $(".select-worker-" + self.id).select2({data: select2data});
            }

            // initialize timepickers
            self.startDatetimepicker = $('#start-datetimepicker-' + self.id).datetimepicker({
                defaultDate: start,
                format: self.displayFormat,
                sideBySide: true,
                widgetPositioning: {
                    horizontal: "right",
                    vertical: "bottom",
                }
            });
            self.stopDatetimepicker = $('#stop-datetimepicker-' + self.id).datetimepicker({
                defaultDate: stop,
                format: self.displayFormat,
                sideBySide: true,
                widgetPositioning: {
                    horizontal: "right",
                    vertical: "bottom",
                }
            });

            self.durationText = $("#durationText-" + self.id);
            self.durationWarning = $("#durationWarning-" + self.id);
            self.saveButton = $("#save-button-" + self.id);

            self.durationText.text(start.preciseDiff(stop));

            self.startDatetimepicker.on("dp.change", function(event) {
                self.updateCheckDuration();
            });

            self.stopDatetimepicker.on("dp.change", function(event) {
                self.updateCheckDuration();
            });

            if (self.mode === "edit") {
                self.saveButton.click(function(event) {
                    self.saveTimeclockAdjustment(event);
                });

                $("#delete-button-" + self.id).click(function(event) {
                    self.deleteTimeclock(event);
                });
            }

            else {
                self.saveButton.click(function(event) {
                    self.createTimeclock(event);
                });
            }
        },
        updateCheckDuration: function() {
            var self = this,
                start = moment(self.startDatetimepicker.data("date"),  self.displayFormat),
                stop = moment(self.stopDatetimepicker.data("date"),  self.displayFormat),
                stopAfterStart = start < stop,
                duration = start.preciseDiff(stop)
            ;

            if (stopAfterStart) {
                self.durationText.removeClass("hidden");
                self.durationWarning.addClass("hidden");

                self.durationText.text(duration);
                self.saveButton.removeClass("disabled");
            } else {
                self.durationText.addClass("hidden");
                self.durationWarning.removeClass("hidden");

                self.saveButton.addClass("disabled");
            }
        },
        createTimeclock: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                timeclockModel = new Models.Timeclock(),
                timezone = self.locationModel.get("timezone"),
                startMoment = moment.tz(self.startDatetimepicker.data("date"),  self.displayFormat, timezone),
                stopMoment = moment.tz(self.stopDatetimepicker.data("date"),  self.displayFormat, timezone),
                secondsDifference = parseInt((stopMoment - startMoment)/1000),
                success,
                error,
                params = {
                    start: startMoment.utc().format(),
                    stop: stopMoment.utc().format(),
                },
                roleId,
                userId
            ;

            // if a userId is defined, then the modal is was triggered from in the html line
            // and it will also have a role id
            if (!_.isNaN(self.userId)) {
                userId = self.userId;
                roleId = self.roleId;
            } else {
                var selectedIds = $(".select-worker-" + self.id).select2().val().split("-");

                roleId = parseInt(selectedIds[0]);
                userId = parseInt(selectedIds[1]);
            }

            // add upstream models
            timeclockModel.addUpstreamModel("locationId", self.locationId);
            timeclockModel.addUpstreamModel("roleId", roleId);
            timeclockModel.addUpstreamModel("userId", userId);

            success = function(model, response) {
                $.notify({message: "Timeclock created"}, {type:"success"});
                self.saveTimeclockCallback(model, secondsDifference, 0);
                self.modal.modal("hide");
            };

            error = function(model, response) {
                $.notify({message: "Unable to create timeclock - please contact support if the problem persists."},{type:"danger"});
            };

            timeclockModel.save(
                params,
                {
                    success: success,
                    error: error,
                }
            );
        },
        saveTimeclockAdjustment: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                timezone = self.locationModel.get("timezone"),
                originalStartMoment = moment.utc(self.model.get("start")).tz(timezone),
                originalStopMoment = moment.utc(self.model.get("stop")).tz(timezone),
                startMoment = moment.tz(self.startDatetimepicker.data("date"), self.displayFormat, timezone),
                stopMoment = moment.tz(self.stopDatetimepicker.data("date"),  self.displayFormat, timezone),
                newDuration = parseInt((stopMoment - startMoment)/1000),
                originalDuration = parseInt((originalStopMoment - originalStartMoment)/1000),
                success,
                error,
                updateParams = {
                    start: startMoment.utc().format(),
                    stop: stopMoment.utc().format(),
                }
            ;

            success = function(model, response) {
                $.notify({message: "Timeclock updated"},{type:"success"});
                self.saveTimeclockCallback(model, newDuration, originalDuration);
                self.modal.modal("hide");
            };

            error = function(model, response) {
                $.notify({message: "Unable to update this timeclock - please contact support if the problem persists."},{type:"danger"});
            };

            self.model.save(
                updateParams,
                {
                    success: success,
                    error: error,
                    patch: true,
                }
            );
        },
        deleteTimeclock: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                timezone = self.locationModel.get("timezone"),
                startMoment = moment.utc(self.model.get("start")).tz(timezone),
                stopMoment = moment.utc(self.model.get("stop")).tz(timezone),
                duration = parseInt((stopMoment - startMoment)/1000),
                success,
                error
            ;

            success = function(model, response) {
                $.notify({message: "Timeclock deleted"},{type:"success"});
                self.deleteTimeclockCallback(model.id, model.get("user_id"), model.get("role_id"), duration);
                self.modal.modal("hide");
            };

            error = function(model, response, opts) {
                $.notify({message: "Unable to delete this timeclock - please contact support if the problem persists."},{type:"danger"});
            };

            self.model.destroy({
                success: success,
                error: error,
            });
        },
    });

    root.App.Views.Components.TimeclockModalView = TimeclockModalView;

})(this);
