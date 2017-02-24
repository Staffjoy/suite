(function(root) {

    "use strict";

    var Views = root.App.Views,
        Util = root.App.Util
    ;

    var StaffingLevelsGraph = Views.Base.extend({
        el: ".coverage-graph-placeholder",
        events: {},
        initialize: function(opts) {
            StaffingLevelsGraph.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.el)) {
                    this.el = opts.el;
                }
                if (!_.isUndefined(opts.id)) {
                    this.id = opts.id;
                }
                if (!_.isUndefined(opts.startTime)) {
                    this.startTime = opts.startTime;
                }
                if (!_.isUndefined(opts.endTime)) {
                    this.endTime = opts.endTime;
                }
                if (!_.isUndefined(opts.data)) {
                    this.data = opts.data;
                }
            }
        },
        render: function(opts) {
            var self = this,
                data = {
                    title: "Staffing Levels",
                    id: self.id
                }
            ;

            self.$el.append(ich.graph_placeholder(data));

            // Coverage chart
            $(".highcharts-graph#" + self.id).highcharts({
                chart: {
                    type: 'area',
                },
                plotOptions: {
                    area: {
                        stacking: 'normal',
                        marker: {
                            enabled: false,
                        },
                    },
                },
                credits: {
                    enabled: false
                },
                title: {
                    text: '',
                },
                xAxis: {
                    allowDecimals: false,
                    tickInterval: 8,
                    title: {
                        text: 'Time'
                    },
                    min: self.startTime,
                    max: self.endTime * 4,
                    labels: {
                        formatter: function () {
                            return ((this.value / 4) % 24);
                        },
                    },
                },
                yAxis: {
                    allowDecimals: false,
                    title: {
                        text: ""
                    },
                },
                legend: {
                    enabled: true,
                },
                tooltip: {
                    shared: true,
                    formatter: function() {
                        var hour = Math.floor(this.points[0].x / 4),
                            minute = (this.points[0].x % 4 === 0) ? "00" : ((this.points[0].x % 4) * 15),
                            result = "<strong>" + hour + ":" + minute + "</strong><br/>",
                            total = 0
                        ;

                        // add each role
                        _.each(this.points, function(point) {
                            result += point.series.name + ": <strong>" + point.y + "</strong><br/>";
                            total += point.y;
                        });

                        // get the total
                        result += "Total: <strong>" + total + "</strong>";

                        return result;
                    }
                },
                series: self.getCoverageSeries(),
            });

            return this;
        },
        getCoverageSeries: function() {
            var self = this,
                result = []
            ;

            _.each(_.keys(self.data), function(roleName, index) {
                result.push({
                    name: roleName,
                    data: self.data[roleName].coverage,
                    step: true,
                    color: Util.chooseColor(index),
                });
            });

            return result;
        },
        updateSeries: function(model) {
            var self = this,
                $graph = $(".highcharts-graph#" + self.id).highcharts(),
                seriesIndex,
                i
            ;

            // get the index of the series we want
            for (i=0; i < $graph.series.length; i++) {
                if ($graph.series[i].name === model.roleName) {
                    seriesIndex = i;
                    break;
                }
            }

            if (seriesIndex < 0) {
                return $.notify({message:"There was an error loading the page - please contact support"},{type: "danger"});
            }

            $graph.series[seriesIndex].setData(self.data[model.roleName].coverage, true);
        },
        updateRange: function(start, end) {
            var self = this,
                $graph = $(".highcharts-graph#" + self.id).highcharts()
            ;

            self.startTime = start;
            self.endTime = end;

            $graph.xAxis[0].update({
                min: start,
                max: end,
            });
        },
    });

    root.App.Views.Components.StaffingLevelsGraph = StaffingLevelsGraph;

})(this);
