(function(root) {

    "use strict";

    var Views = root.App.Views,
        Util = root.App.Util
    ;

    var ViewAvailability = Views.Base.extend({
        el: ".set-availability",
        initialize: function(opts) {
            ViewAvailability.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.el)) {
                    this.el = opts.el;
                }

                if (!_.isUndefined(opts.availability)) {
                    this.availability = opts.availability;
                }

                if (!_.isUndefined(opts.demand)) {
                    this.demand = opts.demand;
                }

                if (!_.isUndefined(opts.timeRange)) {
                    this.timeRange = opts.timeRange;
                }

                if (!_.isUndefined(opts.weekStart)) {
                    this.weekStart = opts.weekStart;
                }

                if (!_.isUndefined(opts.weekStartMoment)) {
                    this.weekStartMoment = opts.weekStartMoment;
                }

                this.daysInWeek = 7;
                this.shiftsPerHour = 1;
            }
        },
        render: function(opts) {
            var self = this,
                weekStartDay = self.weekStartMoment.format("dddd").toLowerCase(),
                upcomingDays = Util.getOrderedWeekArray(weekStartDay)
            ;

            // iterate through the upcoming days
            _.each(upcomingDays, function(dayName, index) {
                self.addDelegateView(
                    dayName,
                    new Views.Components.ViewAvailabilityColumn({
                        el: self.el,
                        dayName: dayName,
                        dayMoment: self.weekStartMoment.clone().add(index, "days"),
                        dayAvailability: self.availability[dayName],
                        dayDemand: self.demand[dayName],
                        timeRange: self.timeRange,
                    })
                );
            });
        },
    });

    root.App.Views.Components.ViewAvailability = ViewAvailability;

})(this);
