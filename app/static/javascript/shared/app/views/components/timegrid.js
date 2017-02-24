(function(root) {

    "use strict";

    var Views = root.App.Views,
        Util = root.App.Util
    ;

    var Timegrid = Views.Base.extend({
        el: ".timegrid",
        initialize: function(opts) {
            Timegrid.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.el)) {
                    this.el = opts.el;
                }

                if (!_.isUndefined(opts.timegridData)) {
                    this.timegridData = opts.timegridData;
                }

                if (!_.isUndefined(opts.timeRange)) {
                    this.timeRange = opts.timeRange;
                }

                if (!_.isUndefined(opts.dayWeekStarts)) {
                    this.dayWeekStarts = opts.dayWeekStarts;
                }

                if (!_.isUndefined(opts.dangerMode)) {
                    this.dangerMode = opts.dangerMode;
                }

                if (!_.isUndefined(opts.disabledRange)) {
                    this.disabledRange = opts.disabledRange;
                }

                if (!_.isUndefined(opts.disabled)) {
                    this.disabled = opts.disabled;
                }

                if (!_.isUndefined(opts.start)) {
                    this.start = opts.start;
                }

                if (!_.isUndefined(opts.timezone)) {
                    this.timezone = opts.timezone;
                }

                if (!_.isUndefined(opts.timegridColumnButton)) {
                    this.timegridColumnButton = opts.timegridColumnButton;
                }

                if (!_.isUndefined(opts.mouseUpTouchEndCallback)) {
                    this.mouseUpTouchEndCallback = opts.mouseUpTouchEndCallback;
                }

                this.daysInWeek = 7;
                this.changed = false;
            }
        },
        render: function(opts) {
            var self = this,
                upcomingDays = Util.getOrderedWeekArray(self.dayWeekStarts),
                start = self.start && self.timezone ? moment.utc(self.start).tz(self.timezone) : false,
                dayLabel
            ;

            if (!self.timegridData) {
                self.timegridData = Util.generateFullDayAvailability();
            } else if (_.isString(self.timegridData)) {
                self.timegridData = JSON.parse(self.timegridData);
            }

            if (!self.disabledRange) {
                self.disabledRange = Util.generateFullDayAvailability(1);
            }

            // iterate through the upcoming days
            _.each(upcomingDays, function(dayName, index) {
                dayLabel = start ? start.clone().add(index, 'days').format('M/D') : null;
                self.addDelegateView(
                    dayName,
                    new Views.Components.TimegridColumn({
                        el: self.el,
                        dayName: dayName,
                        dayLabel: dayLabel,
                        timegridColumnData: self.timegridData[dayName],
                        timeRange: self.timeRange,
                        dangerMode: self.dangerMode,
                        disabledRange: self.disabledRange[dayName],
                        timegridColumnButton: self.timegridColumnButton,
                        date: self.start && self.timezone ? moment(self.start).tz(self.timezone).add(index, 'days').format('YYYY-MM-DD') : null,
                    })
                );
            });

            if (!self.disabled) {
                self.startTimegridEvent();
            }
        },
        startTimegridEvent: function() {
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

            $(".timegrid-content").on("mousedown touchstart", function(e) {
                e.preventDefault();
                e.stopPropagation();

                $mousedownTarget = $(e.target).closest(".timegrid-block");
                startingState = $mousedownTarget.attr("data-state");

                // only modifiable if in active or inactive states
                if (startingState === "active" || startingState === "inactive") {

                    changeColumn = $mousedownTarget.attr("data-dayName");
                    changeIndex = $mousedownTarget.attr("data-index");
                    newState = changesTo[startingState];

                    // adjust state of clicked cell
                    self.adjustTimegridData(changeColumn, changeIndex, startingState, newState);

                    // drag event
                    // currently only supported on desktop view - drag events are way harder for mobile
                    $(".timegrid-content").on("mousemove touchmove", function (d) {
                        d.preventDefault();
                        d.stopPropagation();

                        // .timegrid-content means cursor is on the column but the event
                        // should only trigger if it's in the cell. Also, it needs to do
                        // a .closest search of d.target to get the actual .timegrid-block
                        // but that gets expensive if the cursor is on the column - it does a search
                        // traversing all the way up to the body tag to find nothing
                        // this simple check makes the event do nothing if it's between columns

                        if (!$(d.target).hasClass("timegrid-content")) {

                            if (d.type === "touchmove") {
                                touch = d.originalEvent.touches[0];
                                $moveTarget = $(document.elementFromPoint(touch.clientX, touch.clientY)).closest(".timegrid-block");
                            } else {
                                $moveTarget = $(d.target).closest(".timegrid-block");
                            }

                            moveState = $moveTarget.attr("data-state");

                            // cells can only toggle 1 direction at a time
                            // this also effectively shuns disabled from being acted on
                            if (moveState === startingState) {

                                changeColumn = $moveTarget.attr("data-dayName");
                                changeIndex = $moveTarget.attr("data-index");

                                // adjust state of clicked cell
                                self.adjustTimegridData(changeColumn, changeIndex, moveState, newState);
                            }
                        }
                    });
                }
            });

            self.$el.on("mouseup touchend", function (e) {
                e.preventDefault();
                e.stopPropagation();

                $mousedownTarget = $(e.target).closest(".timegrid-block");
                startingState = $mousedownTarget.attr("data-state");

                if (startingState === 'disabled') {
                    return;
                }

                $(".timegrid-content").unbind("mousemove touchmove");

                if (_.isFunction(self.mouseUpTouchEndCallback)) {
                    self.mouseUpTouchEndCallback(e);
                }
            });

            return this;
        },
        close: function() {
            var self = this;

            self.$el.off("mouseup touchend");
            $(".timegrid-content").off("mousedown touchstart");

            Timegrid.__super__.close.call(this);
        },
        adjustTimegridData: function(dayName, index, oldState, newState) {
            var self = this;
            self.changed = true;

            return self.delegateViews[dayName].updateTimegrid(index, oldState, newState);
        },
        getTimegridData: function() {
            var self = this,
                result = {}
            ;

            _.each(_.keys(self.delegateViews), function(dayName, index) {
                result[dayName] = self.delegateViews[dayName].timegridColumnData;
            });

            return result;
        }
    });

    root.App.Views.Components.Timegrid = Timegrid;

})(this);
