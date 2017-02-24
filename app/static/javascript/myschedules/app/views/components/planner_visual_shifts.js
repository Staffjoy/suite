(function(root) {

    "use strict";

    var Views = root.App.Views,
        Util = root.App.Util
    ;

    var PlannerVisualShifts = Views.Base.extend({
        el: ".visual-shifts-placeholder",
        events: {},
        initialize: function(opts) {
            PlannerVisualShifts.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.el)) {
                    this.el = opts.el;
                }

                if (!_.isUndefined(opts.timeRange)) {
                    this.timeRange = opts.timeRange;
                }

                if (!_.isUndefined(opts.userModel)) {
                    this.userModel = opts.userModel;
                }

                if (!_.isUndefined(opts.weekStartMoment)) {
                    this.weekStartMoment = opts.weekStartMoment;
                }
                this.daysInWeek = 7;
                this.setDateRangeLabels();
            }
        },
        render: function(opts) {
            var self = this,
                data = {
                    title: "Shifts This Week"
                },
                seriesData = self.arrangeShifts(),
                calendarChart
            ;

            self.$el.html(ich.visual_shifts_card(data));

            // visual shifts graph
            $(".visual-shifts-placeholder .highcharts-graph").highcharts({
                chart: {
                    type: 'columnrange',
                },
                credits: {
                    enabled: false,
                },
                plotOptions: {
                    series: {
                        pointRange: 2,
                        borderWidth: 3,
                        borderRadius: 3,
                        states: {
                            hover: {
                                enabled: false,
                            },
                        },
                    },
                    columnrange: {
                        grouping: false,
                        shadow: false,
                        dataLabels: {
                            // NOTE: highcharts wants to print a data label at each end of the column
                            // align left makes them stack vertically, so it looks like one label.
                            // Then we can take the formatter and highjack the data label for anything
                            align: "left",
                            verticalAlign: "top",
                            enabled: true,
                            inside: true,
                            shadow: false,
                            color: "#fff",
                            style: {
                                textShadow: false,
                            },
                            useHTML: true,
                            formatter: function() {
                                var screenWidth = $("body").width(),
                                    compact = screenWidth <= 768,   // bootstrap xs view size
                                    width = this.point.pointWidth - 2 * this.series.borderWidth,
                                    display = "<div class='shift-label' style='width:" + width + "px;'>"
                                ;

                                if (!!this.point.description) {
                                    display += "<span class='fa fa-tag'></span>";
                                }

                                display += this.point.fullStart + " - </br>" + this.point.fullStop + "</div>";

                                return display;
                            },
                        },
                    },
                },
                title: {
                    text: '',
                },
                xAxis: {
                    categories: self.categories,
                    opposite: true,
                    title: {
                        text: null,
                    },
                    tickWidth: 0,
                },
                yAxis: {
                    allowDecimals: false,
                    title: {
                        text: 'Time',
                    },
                    reversed: true,
                    min: self.timeRange.min,
                    max: self.timeRange.max,
                    labels: {
                        formatter: function () {
                            return Util.formatIntIn12HourTime(this.value, false, true);
                        },
                    },
                    tickPositioner: function() {
                        var min = this.userOptions.min - this.userOptions.min % 2,
                            max = this.userOptions.max,
                            result = [],
                            tickWidth = 4,
                            i
                        ;

                        for (i=0; i <= Math.ceil((max-min)/tickWidth); i++) {
                            result.push(min + tickWidth * i);
                        }

                        return result;
                    },
                },
                tooltip: {
                    backgroundColor: "rgba(255,255,255,0)",
                    borderWidth: 0,
                    shadow: false,
                    useHTML: true,
                    formatter: function() {
                        return "<div class='shift-tooltip'>" +
                                this.point.name + "<br/><strong>" +
                                this.point.fullStart + " - " +
                                this.point.fullStop + "</strong><br/>" +
                                "<div class='shift-tooltip-description'>" +
                                this.point.description + "</div></div>";
                    },
                },
                legend: {
                    enabled: false,
                },
                series: [
                    {
                        name: "schedule",
                        data: seriesData,
                    },
                ],
            });

            // add listener for adding new model to collection
            self.collection.on("add", function(model) {
                calendarChart = $(".visual-shifts-placeholder .highcharts-graph").highcharts();
                calendarChart.series[0].setData(self.arrangeShifts(), true);
            });

            return this;
        },
        arrangeShifts: function() {
            var self = this,
                data = [],
                i
            ;

            // make 1 empty shift for each day of the week
            // this doesn't render anything or throw an error, but it ensures
            // each day of the week is visible
            for (i=0; i <  self.daysInWeek; i++) {
                data.push({
                    name: self.categories[i],
                    x: i,
                });
            }

            // pack up each shift
            _.each(self.collection.models, function(shift, index) {
                var shiftStartLocalMoment = moment.utc(shift.get("start")).local(),
                    shiftStopLocalMoment = moment.utc(shift.get("stop")).local()
                ;

                // check for split scenario
                if (shiftStartLocalMoment.date() !== shiftStopLocalMoment.date()) {
                    data.push(self.prepareShiftForGraph(shift, "start"));
                    data.push(self.prepareShiftForGraph(shift, "stop"));
                } else {
                    data.push(self.prepareShiftForGraph(shift));
                }
            });

            data.sort(function(a, b) {
                if (a.x > b.x) {
                    return 1;
                }

                if (a.x < b.x) {
                    return -1;
                }

                if (a.low > b.low) {
                    return 1
                }

                if (a.low < b.low) {
                    return -1
                }

                return 0;
            });

            return data;
        },
        prepareShiftForGraph: function(shift, splithalf) {
            var self = this,
                color = Util.chooseColor(0),
                previousColor = Util.greyscaleColor(color),
                startMoment = moment.utc(shift.get("start")).local(),
                stopMoment = moment.utc(shift.get("stop")).local(),
                startDateLabel = startMoment.format("ddd M/D"),
                stopDateLabel = stopMoment.format("ddd M/D"),
                nowMoment = moment(),
                currentDay,
                shiftDayMoment,
                dateLabel,
                result = {}
            ;

            if (!_.isUndefined(splithalf)) {
                if (splithalf === "start") {
                    result.low = startMoment.hour() + (Math.floor(startMoment.minute() / 60 * 4) / 4);
                    result.high = 24;
                    currentDay = self.dayIndex[startDateLabel];
                } else {
                    result.low = 0;
                    result.high = stopMoment.hour() + (Math.ceil(stopMoment.minute() / 60 * 4) / 4);
                    currentDay = self.dayIndex[stopDateLabel];
                }
            } else {
                result.low = startMoment.hour() + (Math.floor(startMoment.minute() / 60 * 4) / 4);
                result.high = stopMoment.hour() + (Math.ceil(stopMoment.minute() / 60 * 4) / 4);
                currentDay = self.dayIndex[startDateLabel];
            }

            // a fragmented shift might be overlapping to another week - don't want to add that
            if (_.isUndefined(currentDay)) {
                return;
            }

            result.x = currentDay;
            result.name = startDateLabel;
            result.fullStart = startMoment.format("h:mm a");
            result.fullStop = stopMoment.format("h:mm a");
            result.description = shift.get('description') || '';

            // go fancy for schedule for current day
            if (startMoment.isBefore(nowMoment) &&
                stopMoment.isAfter(nowMoment)
            ) {
                result.color = Util.adjustColor(color, 1, true);
            }
            // if schedule already passed
            else if (stopMoment.isBefore(nowMoment)) {
                result.color = previousColor;
            }
            // otherwise it's after
            else {
                result.color = color;
            }

            return result;
        },
        setDateRangeLabels: function() {
            var self = this,
                days = [],
                dayIndex = {},
                currentDate,
                currentMoment = self.weekStartMoment.clone(),
                i
            ;

            for (i = 0; i < this.daysInWeek; i++) {
                // format current day, then add
                currentDate = currentMoment.format("ddd M/D");
                days.push(currentDate);
                dayIndex[currentDate] = i;
                currentMoment = currentMoment.add(1, "days");
            }

            self.dayIndex = dayIndex;
            self.categories = days;
        },
        addToGraph: function(model) {
            var self = this;
            self.collection.add(model);
        },
    });

    root.App.Views.Components.PlannerVisualShifts = PlannerVisualShifts;

})(this);
