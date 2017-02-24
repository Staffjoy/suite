(function(root) {

    "use strict";

    var Views = root.App.Views,
        Util = root.App.Util
    ;

    var SetAvailability = Views.Base.extend({
        el: ".set-availability",
        initialize: function(opts) {
            SetAvailability.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.el)) {
                    this.el = opts.el;
                }

                if (!_.isUndefined(opts.availability)) {
                    this.availability = opts.availability;
                }

                if (!_.isUndefined(opts.timeRange)) {
                    this.timeRange = opts.timeRange;
                }

                if (!_.isUndefined(opts.scheduleModel)) {
                    this.scheduleModel = opts.scheduleModel;
                }
                this.daysInWeek = 7;
                this.changed = false;
            }
        },
        render: function(opts) {
            var self = this,
                weekStart = self.scheduleModel.get("start"),
                currentState = self.scheduleModel.get("state"),
                weekStartMoment = moment(weekStart),
                weekStartDay = weekStartMoment.format("dddd").toLowerCase(),
                upcomingDays = Util.getOrderedWeekArray(weekStartDay)
            ;

            if (currentState === "demand") {
                self.scheduleModel.set({
                    demand: Util.generateFullDayAvailability(),
                })
            }

            // iterate through the upcoming days
            _.each(upcomingDays, function(dayName, index) {
                self.addDelegateView(
                    dayName,
                    new Views.Components.SetAvailabilityColumn({
                        el: self.el,
                        dayName: dayName,
                        dayMoment: weekStartMoment.clone().add(index, "days"),
                        dayAvailability: self.availability[dayName],
                        dayDemand: self.scheduleModel.get("demand")[dayName],
                        timeRange: self.timeRange,
                    })
                );
            });

            self.startAvailabilityEvent();
        },
        startAvailabilityEvent: function() {
            var self = this,
                $mousedownTarget,
                $moveTarget,
                startingState,
                moveState,
                newState,
                changeColumn,
                changeIndex,
                touch,
                changesTo = {
                    active: "inactive",
                    inactive: "active",
                }
            ;

            $(".availability-content").on("mousedown touchstart", function(e) {
                e.preventDefault();
                e.stopPropagation();

                $mousedownTarget = $(e.target).closest(".availability-block");
                startingState = $mousedownTarget.attr("data-state");

                // only modifiable if in active or inactive states
                if (startingState === "active" || startingState === "inactive") {

                    changeColumn = $mousedownTarget.attr("data-dayName");
                    changeIndex = $mousedownTarget.attr("data-index");
                    newState = changesTo[startingState];

                    // adjust state of clicked cell
                    self.adjustAvailability(changeColumn, changeIndex, startingState, newState);

                    // drag event
                    // currently only supported on desktop view - drag events are way harder for mobile
                    $(".availability-content").on("mousemove touchmove", function (d) {
                        d.preventDefault();
                        d.stopPropagation();

                        // .availability-content means cursor is on the column but the event
                        // should only trigger if it's in the cell. Also, it needs to do
                        // a .closest search of d.target to get the actual .availability-block
                        // but that gets expensive if the cursor is on the column - it does a search
                        // traversing all the way up to the body tag to find nothing
                        // this simple check makes the event do nothing if it's between columns

                        if (!$(d.target).hasClass("availability-content")) {

                            if (d.type === "touchmove") {
                                touch = d.originalEvent.touches[0];
                                $moveTarget = $(document.elementFromPoint(touch.clientX, touch.clientY)).closest(".availability-block");
                            } else {
                                $moveTarget = $(d.target).closest(".availability-block");
                            }

                            moveState = $moveTarget.attr("data-state");

                            // cells can only toggle 1 direction at a time
                            // this also effectively shuns disabled from being acted on
                            if (moveState === startingState) {

                                changeColumn = $moveTarget.attr("data-dayName");
                                changeIndex = $moveTarget.attr("data-index");

                                // adjust state of clicked cell
                                self.adjustAvailability(changeColumn, changeIndex, moveState, newState);
                            }
                        }
                    });
                }
            });

            $(document).on("mouseup touchend", function () {
                $(".availability-content").unbind("mousemove touchmove");
            });

            return this;
        },
        adjustAvailability: function(dayName, index, oldState, newState) {
            var self = this;
            self.changed = true;

            return self.delegateViews[dayName].updateAvailability(index, oldState, newState);
        },
        getAvailability: function() {
            var self = this,
                result = {}
            ;

            _.each(_.keys(self.delegateViews), function(dayName, index) {
                result[dayName] = self.delegateViews[dayName].dayAvailability;
            });

            return result;
        }
    });

    root.App.Views.Components.SetAvailability = SetAvailability;

})(this);
