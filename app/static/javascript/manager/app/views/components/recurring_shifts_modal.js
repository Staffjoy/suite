(function(root) {

    "use strict";

    var Models = root.App.Models,
        Views = root.App.Views,
        Util = root.App.Util
    ;

    var RecurringShiftsModalView = Views.Base.extend({
        el: ".recurring-shifts-modal-placeholder",
        events: {
            'click .save-button': 'saveShift',
            'click .delete-button': 'deleteShift',
            'click .select-option': 'updateDropdown',
        },
        initialize: function(opts) {
            RecurringShiftsModalView.__super__.initialize.apply(this);

            // required for using select2 text search inside modal
            $.fn.modal.Constructor.prototype.enforceFocus = function() {};

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.userRolesCollection)) {
                    this.userRolesCollection = opts.userRolesCollection;
                }

                if (!_.isUndefined(opts.recurringShiftModel)) {
                    this.recurringShiftModel = opts.recurringShiftModel;
                }

                if (!_.isUndefined(opts.userModel)) {
                    this.userModel = opts.userModel;
                }

                if (!_.isUndefined(opts.edit)) {
                    this.edit = opts.edit;
                }

                if (!_.isUndefined(opts.orgModel)) {
                    this.orgModel = opts.orgModel;
                }

                if (!_.isUndefined(opts.callback)) {
                    this.callback = opts.callback;
                }

                if (!_.isUndefined(opts.recurringShiftsCollection)) {
                    this.recurringShiftsCollection = opts.recurringShiftsCollection;
                }
            }
        },
        render: function(opts) {
            var self = this,
                data = {
                    edit: self.edit,
                    unassigned: !self.userModel,
                    name: !!self.userRolesCollection ? false : self.userModel.get('name'),
                },
                dayWeekStarts = self.orgModel.get('day_week_starts'),
                days = Util.getOrderedWeekArray(dayWeekStarts).map(function(day) {
                    return Util.capitalize(day);
                }),
                startDay = !!self.recurringShiftModel ? Util.capitalize(self.recurringShiftModel.get('start_day')) : Util.capitalize(dayWeekStarts),
                quantity = !!self.recurringShiftModel ? self.recurringShiftModel.get('quantity') : 1,
                startHour = !!self.recurringShiftModel ? self.recurringShiftModel.get('start_hour') : 9,
                startMinute = !!self.recurringShiftModel ? self.recurringShiftModel.get('start_minute') : 0,
                duration = !!self.recurringShiftModel ? self.recurringShiftModel.get('duration_minutes') : 480,
                durationHour = Math.floor(duration / 60),
                durationMinute = duration % 60
            ;

            self.$el.html(ich.recurring_shifts_modal(data));

            self.$workerSelect = $('.recurring-shift-worker-select');
            self.$quantityList = $('.recurring-shifts-quantity .dropdown-menu');
            self.$quantityButton = $('.recurring-shifts-quantity button');
            self.$dayList = $('.recurring-shifts-day-of-week .dropdown-menu');
            self.$dayButton = $('.recurring-shifts-day-of-week button');
            self.$hoursList = $('.recurring-shifts-duration-hours .dropdown-menu');
            self.$hoursButton = $('.recurring-shifts-duration-hours button');
            self.$minutesList = $('.recurring-shifts-duration-minutes .dropdown-menu');
            self.$minutesButton = $('.recurring-shifts-duration-minutes button');
            self.$startTimepicker = $('#recurring-shifts-start-timepicker');

            self.renderWorkerSelect();
            self.renderQuantityDropdown(quantity);
            self.renderDayOfWeekDropdown(days, startDay);
            self.renderStarTimePicker(startHour, startMinute);
            self.renderDurationHourDropdown(durationHour);
            self.renderDurationMinuteDropdown(durationMinute);

            $("#recurring-shifts-modal").modal();

            $("#recurring-shifts-modal").on("hide.bs.modal", function(e) {
                $('body').removeClass('modal-open');
                self.close();
            });
        },
        close: function() {
            $('.recurring-shift-worker-select').off();
            $("#recurring-shifts-modal").off("hidden.bs.modal");

            RecurringShiftsModalView.__super__.close.call(this);
        },
        renderWorkerSelect: function() {
            var self = this;

            self.$workerSelect.select2({
                data: (function() {
                    var data = {};

                    if (!!self.userRolesCollection) {
                        data = self.userRolesCollection.map(function(model) {
                            return {
                                id: model.id,
                                text: model.get('name'),
                            };
                        });

                        data.unshift({
                            id: 0,
                            text: 'Unassigned'
                        });
                    }

                    return data;
                })(),
            });

            if (!!self.userModel) {
                self.$workerSelect.val(self.userModel.id).trigger('change');
            }
        },
        renderQuantityDropdown: function(quantity) {
            var self = this;

            self.$quantityButton.val(quantity);
            self.$quantityButton.find('.dropdown-value').html(quantity);

            _.each(_.range(1, 101), function(value, index, list) {
                self.$quantityList.append(
                    "<li class='select-option' data-type='quantity' data-value='" + value + "'>" + value + "</li>"
                );
            });

            self.$workerSelect.on('select2:select', function(event) {
                var userId = event.params.data.id;

                if (userId === '0') {
                    self.$quantityButton.prop('disabled', false);
                } else {
                    self.$quantityButton.prop('disabled', true);
                    self.$quantityButton.val(1);
                    self.$quantityButton.find('.dropdown-value').html(1);
                }
            });
        },
        renderDayOfWeekDropdown: function(days, startDay) {
            var self = this;

            self.$dayButton.val(startDay);
            self.$dayButton.find('.dropdown-value').html(startDay);

            _.each(days, function(value, index, list) {
                self.$dayList.append(
                    "<li class='select-option' data-type='day' data-value='" + value + "'>" + value + "</li>"
                );
            });
        },
        renderStarTimePicker: function(startHour, startMinute) {
            var self = this;

            self.$startTimepicker.timepicker({
                template: false,
                showSeconds: false,
                defaultTime: moment.utc(0).add(startHour, 'hours').add(startMinute, 'minutes').format('h:mm A'),
            });
        },
        renderDurationHourDropdown: function(durationHour) {
            var self = this;

            self.$hoursButton.val(durationHour);
            self.$hoursButton.find('.dropdown-value').html(durationHour);

            _.each(_.range(1, 24), function(value, index, list) {
                self.$hoursList.append(
                    "<li class='select-option' data-type='hour' data-value='" + value + "'>" + value + "</li>"
                );
            });
        },
        renderDurationMinuteDropdown: function(durationMinute) {
            var self = this;

            self.$minutesButton.val(durationMinute);
            self.$minutesButton.find('.dropdown-value').html(durationMinute);

            _.each(_.range(0, 60), function(value, index, list) {
                self.$minutesList.append(
                    "<li class='select-option' data-type='minute' data-value='" + value + "'>" + value + "</li>"
                );
            });
        },
        updateDropdown: function(event) {
            var self = this,
                $target = $(event.target),
                type = $target.data('type'),
                value = $target.data('value'),
                $minutesButton,
                $button
            ;

            switch (type) {
                case 'quantity':
                    $button = self.$quantityButton;
                    break;
                case 'day':
                    $button = self.$dayButton;
                    break;
                case 'hour':
                    $button = self.$hoursButton;

                    if (value === 23) {
                        self.$minutesButton.val(0);
                        self.$minutesButton.find('.dropdown-value').html(0);
                        self.$minutesButton.prop('disabled', true);
                    } else {
                        self.$minutesButton.prop('disabled', false);
                    }
                    break;
                case 'minute':
                    $button = self.$minutesButton;
                    break;
            }

            $button.val(value);
            $button.find('.dropdown-value').html(value);
        },
        saveShift: function(event) {
            event.stopPropagation();

            var self = this,
                worker = self.$workerSelect.select2().val() || self.userModel.id,
                quantity = parseInt(self.$quantityButton.val()) || 1,
                dayOfWeek = self.$dayButton.val().toLowerCase(),
                startMoment = moment(self.$startTimepicker.timepicker().val(), "h:mm A"),
                startHour = startMoment.hour(),
                startMinute = startMoment.minute(),
                durationHour = parseInt(self.$hoursButton.val()),
                durationMinute = parseInt(self.$minutesButton.val()),
                duration = (durationHour * 60) + durationMinute
            ;

            if (!!self.recurringShiftModel) {
                self.recurringShiftModel.save(
                    {
                        "user_id": worker,
                        "duration_minutes": duration,
                        "quantity": quantity,
                        "start_day": dayOfWeek,
                        "start_hour": startHour,
                        "start_minute": startMinute,
                    },
                    {
                        success: function(model, response, opts) {
                            $.notify({message:"Recurring shift saved"},{type: "success"});
                            $("#recurring-shifts-modal").modal('hide');
                            self.callback();
                        },
                        error: function(model, response, opts) {
                            $.notify({message:"Unable to save recurring shift"},{type: "danger"});
                        },
                        patch: true,
                    }
                );
            } else {
                var model = new Models.RecurringShift();

                model.addUpstreamModel('locationId', self.recurringShiftsCollection.getUpstreamModelId('locationId'));
                model.addUpstreamModel('roleId', self.recurringShiftsCollection.getUpstreamModelId('roleId'));

                model.save(
                    {
                        "user_id": worker,
                        "duration_minutes": duration,
                        "quantity": quantity,
                        "start_day": dayOfWeek,
                        "start_hour": startHour,
                        "start_minute": startMinute,
                    },
                    {
                        success: function(model, response, opts) {
                            $.notify({message:"Recurring shift created"},{type: "success"});
                            $("#recurring-shifts-modal").modal('hide');
                            self.callback();
                        },
                        error: function(model, response, opts) {
                            $.notify({message:"Unable to create recurring shift"},{type: "danger"});
                        },
                    }
                );
            }
        },
        deleteShift: function(event) {
            event.stopPropagation();

            var self = this;

            self.recurringShiftModel.destroy({
                success: function(model, response, opts) {
                    $.notify({message:"Recurring shift deleted"},{type: "success"});
                    $("#recurring-shifts-modal").modal('hide');
                    self.callback();
                },
                error: function(model, response, opts) {
                    $.notify({message:"Unable to delete recurring shift"},{type: "danger"});
                },
            });
        },
    });

    root.App.Views.Components.RecurringShiftsModalView = RecurringShiftsModalView;

})(this);
