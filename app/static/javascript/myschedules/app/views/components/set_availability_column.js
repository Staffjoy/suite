(function(root) {

    "use strict";

    var Views = root.App.Views,
        Util = root.App.Util
    ;

    var SetAvailabilityColumn = Views.Base.extend({
        el: ".set-availability-placeholder",
        initialize: function(opts) {
            SetAvailabilityColumn.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.el)) {
                    this.el = opts.el;
                }

                if (!_.isUndefined(opts.dayName)) {
                    this.dayName = opts.dayName;
                }

                if (!_.isUndefined(opts.dayMoment)) {
                    this.dayMoment = opts.dayMoment;
                }

                if (!_.isUndefined(opts.dayAvailability)) {
                    this.dayAvailability = opts.dayAvailability;
                }

                if (!_.isUndefined(opts.dayDemand)) {
                    this.dayDemand = opts.dayDemand;
                }

                if (!_.isUndefined(opts.timeRange)) {
                    this.timeRange = opts.timeRange;
                }
                this.dayOffset = 4;
            }
        },
        render: function(opts) {
            var self = this,
                availabilityColumn = ".availability-column-content-" + self.dayName,
                noWorkersToday = Util.checkIfArrayOfZeroes(self.dayDemand),
                currentState,
                adjustedIndex,
                index
            ;

            self.$el.append(ich.set_availability_column({
                    columnNameLabel: self.dayMoment.format("dddd"),
                    columnName: self.dayName,
                    columnDayLabel: self.dayMoment.format("M/D"),
                })
            );

            // add cells to the column
            for (index=0; index < self.dayAvailability.length; index++) {

                // check if is available
                adjustedIndex = self.dayOffset + index;
                if (adjustedIndex < self.timeRange.min || adjustedIndex > self.timeRange.max) {
                    continue;
                }

                // if no workers needed for this day, column is shown but its disabled
                if (noWorkersToday) {
                    currentState = "disabled";

                // collect all availability between timeRange, even if business has
                // varying open/close times
                } else {
                    if (self.dayAvailability[index] === 1) {
                        currentState = "active";
                    } else {
                        currentState = "inactive";
                    }
                }

                $(availabilityColumn).append(ich.set_availability_block({
                        state: currentState,
                        index: index,
                        dayName: self.dayName,
                        blockId: self.dayName + "-" + index,
                        blockLabel: Util.formatIntIn12HourTime(index + self.dayOffset),
                        disabled: noWorkersToday,
                    })
                );
            }

            return this;
        },
        updateAvailability: function(index, oldState, newState) {
            var self = this,
                uniqueId = self.dayName + "-" + index,
                $cell = $("#" + uniqueId),
                newAvailabilityValue = {
                    active: 1,
                    inactive: 0,
                }
            ;

            // change the coloring
            $cell.removeClass(oldState);
            $cell.addClass(newState);

            // update the data-state in the html
            $cell.attr("data-state", newState);

            // update value in data model
            self.dayAvailability[index] = newAvailabilityValue[newState];

            return true;
        },
    });

    root.App.Views.Components.SetAvailabilityColumn = SetAvailabilityColumn;

})(this);
