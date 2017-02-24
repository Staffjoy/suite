(function(root) {

    "use strict";

    var Collections = root.App.Collections,
        Models = root.App.Models,
        Views = root.App.Views,
        Util = root.App.Util
    ;

    var ShiftModalView = Views.Base.extend({
        el: ".modal-placeholder",
        events: {},
        initialize: function(opts) {
            ShiftModalView.__super__.initialize.apply(this);

            // required for using select2 text search inside modal
            $.fn.modal.Constructor.prototype.enforceFocus = function() {};

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.id)) {
                    this.id = opts.id;
                }
                if (!_.isUndefined(opts.el)) {
                    this.el = "#" + opts.el;
                    this.$el = $(this.el);
                }
                if (!_.isUndefined(opts.shiftsCollectionRef)) {
                    this.shiftsCollectionRef = opts.shiftsCollectionRef;
                }
                if (!_.isUndefined(opts.mode)) {
                    this.mode = opts.mode;
                }
                if (!_.isUndefined(opts.roleName)) {
                    this.roleName = opts.roleName;
                }
                if (!_.isUndefined(opts.locationModel)) {
                    this.locationModel = opts.locationModel;
                }
                if (!_.isUndefined(opts.scheduleModel)) {
                    this.scheduleModel = opts.scheduleModel;
                }
                if (!_.isUndefined(opts.callback) && _.isFunction(opts.callback)) {
                    this.callback = opts.callback;
                }

                this.displayFormat = "hh:mm A  MM-DD-YYYY";
                this.$startDatetimepicker;
                this.$stopDatetimepicker;
                this.$selector;
                this.$durationText;
                this.$stopBeforeStartWarning;
                this.$tooLongWarning;
                this.$preferencesWarning;
            }
        },
        render: function(opts) {
            var self = this,
                start,
                stop,
                timezone = self.locationModel.get("timezone"),
                description = self.model.get('description'),
                $descriptionInput,
                data = {
                    id: self.id,
                    title: self.mode === "edit" ? "Edit Shift" : "Create a New " + self.roleName + " Shift",
                    newShift: self.mode === "new",
                    description: description,
                }
            ;

            // html and open modal
            self.$el.html(ich.modal_shift(data));
            $("#shiftControlModal-" + self.id).modal();

            $(function () {
                $('[data-toggle="tooltip"]').tooltip()
            });

            start = moment.utc(self.model.get("start")).tz(timezone);
            stop = moment.utc(self.model.get("stop")).tz(timezone);
            $descriptionInput = $('.description-' + self.id);

            $descriptionInput.on('blur', function(event) {
                if (description === $descriptionInput.val()) {
                    return;
                }

                description = $descriptionInput.val()

                self.model.save(
                    {
                        description: description,
                    },
                    {
                        success: function() {
                            $.notify({message: "The description has been updated"},{type: "success"});
                        },
                        error: function() {
                            $.notify({message: "Unable to update the description"},{type: "success"});
                        },
                        patch: true,
                    }
                );
            });

            // initialize timepickers
            self.$startDatetimepicker = $('#start-datetimepicker-' + self.id).datetimepicker({
                defaultDate: start,
                format: self.displayFormat,
                sideBySide: true,
                widgetPositioning: {
                    horizontal: "right",
                    vertical: "bottom",
                }
            });
            self.$stopDatetimepicker = $('#stop-datetimepicker-' + self.id).datetimepicker({
                defaultDate: stop,
                format: self.displayFormat,
                sideBySide: true,
                widgetPositioning: {
                    horizontal: "right",
                    vertical: "bottom",
                }
            });

            // prepare assignment dropdown, duration, and warning
            self.$selector = $(".select-worker-" + self.id);
            self.$durationText = $("#durationText-" + self.id);
            self.$stopBeforeStartWarning = $("#stopBeforeStartWarning-" + self.id);
            self.$tooLongWarning = $("#tooLongWarning-" + self.id);
            self.$preferencesWarning = $("#preferencesWarning-" + self.id);

            self.setAssignmentDropdown();
            self.updateCheckDuration()

            // initalize click event for dropdown
            // NOTE that backbone events and the modal don't get along
            self.$startDatetimepicker.on("dp.change", function(e) {
                if (self.updateCheckDuration()) {
                    self.changeShiftProperty(e, "start");
                }
            });

            self.$stopDatetimepicker.on("dp.change", function(e) {
                if (self.updateCheckDuration()) {
                    self.changeShiftProperty(e, "stop");
                }
            });

            self.$selector.on("select2:close", function (e) {
                self.changeShiftProperty(e, "assignment");
            });

            // event for deleting the shift
            $(".delete-shift-" + self.id + ", .close-shift-" + self.id).click(function(e) {
                e.preventDefault();
                e.stopPropagation();
                self.deleteShift(e);
            });

            if (self.mode === "new") {
                $(".save-shift-" + self.id).click(function(e) {
                    e.preventDefault();
                    e.stopPropagation();

                    if (!_.isUndefined(self.scheduleModel) &&
                        self.scheduleModel.get("state") === "published" &&
                        !self.model.get("published")
                    ) {
                        self.model.save(
                            {published: true},
                            {
                                success: function() {
                                    $.notify({message: "The shift has been published"},{type: "success"});
                                },
                                error: function() {
                                    $.notify({message: "Unable to publish the shift."},{type: "success"});
                                },
                                patch: true,
                            }
                        );
                    } else {
                        $.notify({ message: 'Shift created' }, { type: 'success' });
                    }

                    self.callback(self.model);
                    $("#shiftControlModal-" + self.id).modal("hide");
                });
            }
        },
        close: function() {
            $('.description-' + self.id).off();
            ShiftModalView.__super__.close.apply(this);
        },
        updateCheckDuration: function() {
            var self = this,
                start = moment(self.$startDatetimepicker.data("date"),  self.displayFormat),
                stop = moment(self.$stopDatetimepicker.data("date"),  self.displayFormat),
                differenceSec = Math.abs(stop.diff(start, "seconds")),
                duration = start.preciseDiff(stop, false, true),
                eligibleUserModel = self.collection.get(self.model.get("user_id")),
                ok = true
            ;

            self.$durationText.text(duration);

            if (!_.isUndefined(eligibleUserModel) &&
                !eligibleUserModel.get("within_caps")
            ) {
                self.$preferencesWarning.removeClass("hidden");
            } else {
                self.$preferencesWarning.addClass("hidden");
            }

            if (!start.isBefore(stop)) {
                ok = false;
                self.$stopBeforeStartWarning.removeClass("hidden");
            }

            // 23 hours, in seconds
            if (ok && differenceSec > 23 * 60 * 60) {
                ok = false;
                self.$tooLongWarning.removeClass("hidden");
            }

            if (ok) {
                self.$tooLongWarning.addClass("hidden");
                self.$stopBeforeStartWarning.addClass("hidden");
            }

            return ok;
        },
        setAssignmentDropdown: function() {
            var self = this,
                user_id = self.model.get("user_id"),
                select2data = [],
                beyond_caps = {
                    text: "Violates Scheduling Rules",
                    children: [],
                },
                name,
                selected
            ;

            // reseting the data
            self.$selector.select2({"data": null});
            self.$selector.select2().empty();

            select2data.push({
                id: 0,
                text: "Unassigned",
                selected: user_id === 0,
            });

            // iterate through collection and sort/segment the users
            _.each(self.collection.models, function(model, index) {
                selected = false;
                name = model.get("name");

                if (model.id === user_id) {
                    selected = true;
                };

                // use email if name not defined
                if (_.isEmpty(name)) {
                    name = model.get("email");
                }

                if (model.get("within_caps")) {
                    select2data.push({
                        id: model.id,
                        text: name,
                        selected: selected,
                    });
                } else {
                    beyond_caps.children.push({
                        id: model.id,
                        text: name,
                        selected: selected,
                    });
                }
            });

            if (beyond_caps.children.length > 0) {
                select2data = select2data.concat(beyond_caps);
            }

            self.$selector.select2({
                data: select2data,
            });
        },
        deleteShift: function(e) {
            var self = this,
                success,
                error,
                successMessage,
                successType,
                errorMessage
            ;

            if (self.mode === "edit") {
                successMessage = "Shift deleted";
                successType = "success";
                errorMessage = "Unable to delete shift - please contact support if the problem persists.";

            } else if (self.mode === "new") {
                successMessage = "Cancelled shift creation";
                successType = "info";
                errorMessage = "A shift was created - refresh page and delete it. Please contact support";
            }

            success = function(model, response, opts) {
                $.notify({message: successMessage},{type: successType});
                $("#shiftControlModal-" + self.id).modal("hide");
            };

            error = function(model, response, opts) {
                $.notify({message: errorMessage},{type:"danger"});
            };

            self.model.destroy({
                success: success,
                error: error,
            });
        },
        changeShiftProperty: function(e, property) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                updateCollection = false,
                dataPayload = {},
                timezone = self.locationModel.get("timezone"),
                originalAttributes = {
                    start: self.model.get("start"),
                    stop: self.model.get("stop"),
                },
                startMoment = moment.tz(self.$startDatetimepicker.data("date"), self.displayFormat, timezone),
                stopMoment = moment.tz(self.$stopDatetimepicker.data("date"), self.displayFormat, timezone),
                start = startMoment.utc().format("YYYY-MM-DDTHH:mm:ss"),
                stop = stopMoment.utc().format("YYYY-MM-DDTHH:mm:ss"),
                userId = parseInt(self.$selector.select2().val()),
                name,
                success,
                error
            ;

            // prepare payload - it's specific to whichever form was clicked
            if (property === "start") {
                updateCollection = true;

                if (!startMoment.isSame(moment.utc(self.model.get("start")))) {
                    dataPayload["start"] = start;
                    dataPayload["stop"] = stop;
                }
            } else if (property === "stop") {
                updateCollection = true;

                if (!stopMoment.isSame(moment.utc(self.model.get("stop")))) {
                    dataPayload["start"] = start;
                    dataPayload["stop"] = stop;
                }
            } else if (property === "assignment") {
                if (userId !== self.model.get("user_id")) {
                    dataPayload["user_id"] = userId;
                }
            }

            // events may fire where the widgets were openend but not changed
            if (_.keys(dataPayload).length < 1) {
                return;
            }

            success = function(model, response, opts) {
                if (self.mode === "edit") {
                    $.notify({message: "Shift updated"},{type:"success"});
                }

                // if user_id was adjusted, front end object needs to get the user name too
                if (_.has(dataPayload, "user_id")) {
                    if (model.get("user_id") > 0) {
                        var collectionModel = self.collection.get(model.get("user_id")),
                            name = collectionModel.get("name") || collectionModel.get("email")
                        ;

                        model.set("user_name", name);
                    } else {
                        model.set("user_name", "Unassigned Shift");
                        model.set("user_id", 0);
                    }
                }

                if (updateCollection) {
                    self.updateEligibleUsers();
                }
                self.updateCheckDuration();
            };

            error = function(model, response, opts) {
                self.model.set(originalAttributes);
                $.notify({message: "This shift overlaps with an existing shift."},{type:"danger"});
            };

            // save model to server
            self.model.save(
                dataPayload,
                {
                    success: success,
                    error: error,
                    patch: true,
                }
            );
        },
        updateEligibleUsers: function() {
            var self = this,
                success,
                error
            ;

            success = function(collection, response, opts) {
                self.setAssignmentDropdown();
            };

            error = function(collection, response, opts) {
                $.notify({message:"There was saving the changes - please contact support if the problem persists."},{type:"danger"});
            };

            self.collection.fetch({
                success: success,
                error: error,
            });

            return;
        },
    });

    root.App.Views.Components.ShiftModalView = ShiftModalView;

})(this);
