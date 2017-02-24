(function(root) {

    "use strict";

    var Collections = root.App.Collections,
        Views = root.App.Views,
        Util = root.App.Util
    ;

    var SchedulingGanttGraph = Views.Base.extend({
        el: ".shift-summary-graph-placeholder",
        events: {
            "click .shift-label": "clickShiftDataLabel",
            "click .shift-tooltip": "clickShiftDataLabel",
        },
        initialize: function(opts) {
            SchedulingGanttGraph.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.el)) {
                    this.el = opts.el;
                }
                if (!_.isUndefined(opts.id)) {
                    this.id = opts.id;
                }
                if (!_.isUndefined(opts.modalId)) {
                    this.modalId = opts.modalId;
                }
                if (!_.isUndefined(opts.startTime)) {
                    this.startTime = opts.startTime;
                }
                if (!_.isUndefined(opts.endTime)) {
                    this.endTime = opts.endTime;
                }
                if (!_.isUndefined(opts.locationModel)) {
                    this.locationModel = opts.locationModel;
                }
                if (!_.isUndefined(opts.dayMoment)) {
                    this.dayMoment = opts.dayMoment;
                }
                if (!_.isUndefined(opts.data)) {
                    this.data = opts.data;

                    var colors = {};
                    _.each(_.keys(this.data), function(roleName, index) {
                        colors[roleName] = Util.chooseColor(index);
                    });
                    this.colors = colors;
                }
            }
        },
        render: function(opts) {
            var self = this,
                data = {
                    title: "Shifts",
                    id: self.id
                }
            ;

            self.$el.append(ich.graph_placeholder(data));
            self.setContainerHeight();

            // Shift Summary chart
            $(".highcharts-graph#" + self.id).highcharts({
                chart: {
                    type: 'columnrange',
                    inverted: true
                },
                credits: {
                    enabled: false
                },
                plotOptions: {
                    series: {
                        cursor: "pointer",
                        pointWidth: 20,
                        borderWidth: 3,
                        borderRadius: 3,
                    },
                    columnrange: {
                        grouping: false,
                        pointPadding: 5,
                        shadow: false,
                        dataLabels: {
                            // NOTE: highcharts wants to print a data label at each end of the column
                            // align left makes them stack vertically, so it looks like one label.
                            // Then we can take the formatter and highjack the data label for anything
                            align: "left",
                            enabled: true,
                            inside: true,
                            shadow: false,
                            color: "#fff",
                            style: {
                                textShadow: false,
                            },
                            useHTML: true,
                            formatter: function() {
                                var start = this.point.startMoment.format("h:mm a"),
                                    end = this.point.stopMoment.format("h:mm a"),
                                    width = this.point.plotLow - this.point.plotHigh - 2 * this.series.borderWidth,
                                    display = "<div class='shift-label cursor-clickable' data-id='" + this.point.id + "' data-series-name='" + this.series.name + "' style='width:" + width + "px;'>"
                                ;

                                if (!!this.point.description) {
                                    display += "<span class='fa fa-tag'></span>";
                                }

                                display +=  start + " - " + end + " " + this.point.name + "</div>";

                                return display;
                            },
                        },
                        events: {
                            click: function(e) {
                                e.preventDefault();
                                e.stopPropagation();

                                self.openModalById(e.point.role, e.point.id);
                            },
                        },
                    },
                },
                title: {
                    text: '',
                },
                xAxis: {
                    labels: {
                        enabled: false
                    },
                    title: {
                        text: null
                    },
                    tickWidth: 0,
                },
                yAxis: {
                    allowDecimals: false,
                    title: {
                        text: 'Time'
                    },
                    min: self.startTime,
                    max: self.endTime,
                    labels: {
                        formatter: function () {
                            return (this.value % 24);
                        },
                    },
                },
                tooltip: {
                    backgroundColor: "rgba(255,255,255,0)",
                    borderWidth: 0,
                    shadow: false,
                    useHTML: true,
                    formatter: function() {
                        var start = this.point.startMoment.format("h:mm a"),
                            end = this.point.stopMoment.format(" h:mm a"),
                            tooltip = "<div class='shift-tooltip cursor-clickable' data-id='" + this.point.id + "' data-series-name='" + this.series.name + "'>" +
                               this.series.name + " (" + this.key + ")<br/><strong>" + start + " - " + end + "</strong><br/>";
                        ;

                        if (!!this.point.description) {
                            tooltip += "<div class='shift-tooltip-description'>" + this.point.description + "</div>";
                        }

                        tooltip += "<span class='edit-click'>edit</span></div>";

                        return tooltip;
                    }
                },
                legend: {
                    enabled: true,
                },
                series: self.getArrayOfShifts(),
            });

            return this;
        },
        addGraphShift: function(model) {
            var self = this,
                highcharts = $(".highcharts-graph#" + self.id).highcharts(),
                series = self.getArrayOfShifts(),
                i
            ;

            self.setContainerHeight();

            // update data for all
            for (i=0; i < series.length; i++) {
                highcharts.series[i].update(series[i], false);
            }

            // re-render once all data is updated
            highcharts.reflow();
            highcharts.redraw();
        },
        updateGraphShift: function(model, remove) {
            remove = !!remove;

            var self = this,
                highcharts = $(".highcharts-graph#" + self.id).highcharts(),
                seriesIndex = -1,
                pointIndex,
                color,
                labelColor,
                name,
                i,
                j
            ;

            // get the index of the series we want
            for (i=0; i < highcharts.series.length; i++) {
                if (highcharts.series[i].name === model.roleName) {
                    seriesIndex = i;
                    break;
                }
            }

            if (seriesIndex < 0) {
                return $.notify({message:"There was an error updating the page - please contact support"},{type: "danger"});
            }

            // get index of highcharts point to update
            // do this by matching by the id
            pointIndex = highcharts.series[seriesIndex].data.getIndexBy("id", model.id);

            if (pointIndex < 0) {
                return $.notify({message:"There was an error loading the page - please contact support"},{type: "danger"});
            }

            // remove the shift
            if (remove) {
                highcharts.series[seriesIndex].data[pointIndex].remove();

            // update the shift
            } else {
                highcharts.series[seriesIndex].data[pointIndex].update(
                    self.prepareShiftForGraph(model)
                );
            }
        },
        clickShiftDataLabel: function(e) {
            /* needed in case someone clicks on the data label */

            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target).closest(".cursor-clickable"),
                id = parseInt($target.attr("data-id")),
                series = $target.attr("data-series-name")
            ;

            self.openModalById(series, id);
        },
        openModalById: function(series, id) {
            var self = this,
                shift = self.data[series].shifts.get(id),
                eligibleWorkersCollection = new Collections.ShiftEligibleWorkers(),
                success,
                error = function(collection, response, opts) {
                    $.notify({message:"There was an error loading the page - please contact support"},{type: "danger"});
                }
            ;

            // add upstream models - all ids are stored in the shift :)
            eligibleWorkersCollection.addUpstreamModel(
                "locationId",
                shift.getUpstreamModelId("locationId")
            );
            eligibleWorkersCollection.addUpstreamModel(
                "roleId",
                shift.getUpstreamModelId("roleId")
            );
            eligibleWorkersCollection.addUpstreamModel(
                "shiftId",
                shift.id
            );

            success = function(collection, response, opts) {
                self.addDelegateView(
                    "modal-view-" + shift.id,
                    new Views.Components.ShiftModalView({
                        el: self.modalId,
                        collection: collection,
                        model: shift,
                        mode: "edit",
                        locationModel: self.locationModel,
                        id: shift.id,
                    })
                );

                $("#shiftControlModal-" + shift.id).on("hidden.bs.modal", function(e) {
                    self.delegateViews["modal-view-" + shift.id].close();
                });

            };

            eligibleWorkersCollection.fetch({
                success: success,
                error: error,
            });
        },
        getArrayOfShifts: function() {
            var self = this,
                shifts = [],
                x = 1, // Iterator
                result = []
            ;

            // 1) Flatten all of the shifts to a single list for sorting, and make highcharts objects
            _.each(_.keys(self.data), function(roleName, index) {
                _.each(self.data[roleName].shifts.models, function(shift) {
                    shifts.push(self.prepareShiftForGraph(shift));
                });
            });

            // 2) Sort and transform
            shifts = _.sortBy(shifts, "high");
            shifts = _.sortBy(shifts, "low");

            // highcharts graph needs to know the shifts vertical position
            _.each(shifts, function(shift) {
                shift.x = x;
                x++;
            });

            // 3) assemble into a final highcharts object
            _.each(_.keys(self.data), function(roleName, index) {
                result.push({
                    color: self.colors[roleName],
                    name: roleName,
                    data: _.where(shifts, {role: roleName}),
                    states: {
                        hover: {
                            borderColor: Util.adjustColor(self.colors[roleName], 1, true),
                        },
                    },
                });
            });

            return result;
        },
        prepareShiftForGraph: function(shift) {
            var self = this,
                timezone = self.locationModel.get("timezone"),
                startMoment = moment.utc(shift.get("start")).tz(timezone),
                stopMoment = moment.utc(shift.get("stop")).tz(timezone),
                start = startMoment.hour() + (Math.floor(startMoment.minute() / 60 * 4) / 4),
                end = stopMoment.hour() + (Math.ceil(stopMoment.minute() / 60 * 4) / 4),
                unassignedColor = "#eee",
                name,
                color,
                dataLabelColor
            ;

            if (self.dayMoment.date() !== startMoment.date()) {
                start = 0;
            }

            if (self.dayMoment.date() !== stopMoment.date()) {
                end = 24;
            }

            if (shift.get("user_id") === 0) {
                name = "Unassigned Shift";
                color = unassignedColor;
                dataLabelColor = this.colors[shift.roleName];
            } else {
                name = shift.get("user_name");
                color = this.colors[shift.roleName];
                dataLabelColor = "#fff";
            }

            return {
                role: shift.roleName,
                startMoment: startMoment,
                stopMoment: stopMoment,
                low: start,
                high: end,
                id: shift.id,
                user_id: shift.get("user_id"),
                name: name,
                borderColor: this.colors[shift.roleName],
                color: color,
                dataLabels: {color: dataLabelColor},
                description: shift.get('description') || '',
            };
        },
        setContainerHeight: function() {
            var self = this,
                totalShifts = 0,
                height = 200,   // starting height
                cellHeight = 25 // height of one shift bar
            ;

            // get total number of shifts
            _.each(_.keys(self.data), function(roleName) {
                totalShifts += self.data[roleName].shifts.models.length;
            });

            height = height + (cellHeight * totalShifts);
            $("#" + self.id).css("height", height);
        },
        updateRange: function(start, end) {
            var self = this,
                highcharts = $(".highcharts-graph#" + self.id).highcharts()
            ;

            self.startTime = start;
            self.endTime = end;

            highcharts.yAxis[0].update({
                min: start,
                max: end,
            });
        },
    });

    root.App.Views.Components.SchedulingGanttGraph = SchedulingGanttGraph;

})(this);
