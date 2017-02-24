(function(root) {

    "use strict";

    var Views = root.App.Views,
        Util = root.App.Util
    ;

    var ViewAvailabilityColumn = Views.Base.extend({
        el: ".set-availability-placeholder",
        initialize: function(opts) {
            ViewAvailabilityColumn.__super__.initialize.apply(this);

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
                currentState,
                adjustedIndex,
                index
            ;

            self.$el.append(ich.view_availability_column({
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

                if (self.dayDemand[index] < 1) {
                    currentState = "disabled";
                } else if (self.dayAvailability[index] === 1) {
                    currentState = "active";
                } else {
                    currentState = "inactive";
                }

                $(availabilityColumn).append(ich.view_availability_cell({
                        state: currentState,
                        index: index,
                        dayName: self.dayName,
                        blockId: self.dayName + "-" + index,
                        blockLabel: Util.formatIntIn12HourTime(index + self.dayOffset),
                    })
                );
            }

            return this;
        },
    });

    root.App.Views.Components.ViewAvailabilityColumn = ViewAvailabilityColumn;

})(this);
