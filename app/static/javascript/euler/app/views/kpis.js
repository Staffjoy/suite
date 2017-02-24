(function(root) {

    "use strict";

    var Util = root.App.Util,
        Views = root.App.Views,
        Models = root.App.Models
    ;

    var KpisView = Views.Base.extend({
        el: "#euler-container",
        events: {
            "click .start-kiosk-mode": "kioskMode",
        },
        initialize: function() {
            KpisView.__super__.initialize.apply(this);
        },
        render: function() {
            var self = this,
                interval,
                data,
                peopleSchedulePerWeek
            ;

            data = {
                peopleClockedIn: self.model.get('people_clocked_in'),
                peopleOnShifts: self.model.get('people_on_shifts'),
                peopleOnlineInLastDay: self.model.get('people_online_in_last_day'),
            };

            peopleSchedulePerWeek = _.chain(self.model.get('people_scheduled_per_week'))
                .pairs()
                .map(function(pair) { pair[0] = moment.utc(_.first(pair)).valueOf(); return pair; })
                .sortBy(function(pair) { return _.first(pair); })
                .value();

            self.$el.html(ich.kpis(data));
            self.createChart(peopleSchedulePerWeek);

            interval = function() {
                self.model.fetch({
                    success: function(model) { if (!model.changedAttributes()) { self.render.apply(self); } },
                });
            };

            if (_.isUndefined(self.interval)) {
                self.interval = setInterval(interval, 300000);
            }

            return this;
        },
        close: function() {
            clearInterval(self.interval);
            KpisView.__super__.close.call(this);
        },
        createChart: function(data) {
            var self = this,
                $peopleSchedulePerWeek = self.$el.find('.people-scheduled-per-week'),
                opts
            ;

            opts = {
                chart: {
                    zoomType: 'x',
                    backgroundColor:'transparent',
                    height: 600,
                    style: {
                        fontFamily: '"Open Sans", "Helvetica Neue", Helvetica, Arial, sans-serif;',
                    }
                },
                credits: {
                    enabled: false
                },
                title: {
                    text: 'People Scheduled Per Week',
                    style: {
                        color: "#666",
                        padding: "10px 5px 0px 5px",
                        fontSize: "23px",
                    },
                },
                xAxis: {
                    type: 'datetime',
                    allowDecimals: false,
                    labels: {
                        rotation: -45,
                    },
                    title: {
                        text: "Week"
                    },
                    tickInterval:7*60*60*24*1000,
                },
                yAxis: {
                    min: 0,
                    allowDecimals: false,
                    title: {
                        text: "People"
                    }
                },
                legend: {
                    enabled: false
                },
                plotOptions: {
                    series: {
                        animation: false
                    }
                },

                series: [{
                    type: 'line',
                    name: 'People Schedule Per Week',
                    data: data,
                    color: "#48B7AB",
                    dataLabels: {
                        enabled: true,
                        color: '#423A3F',
                    },
                }]
            };

            $peopleSchedulePerWeek.highcharts(opts);
        },
        kioskMode: function(e) { 
            e.preventDefault();
            e.stopPropagation();

            // Set to full screen width
            $("#outer-container").css("width", "100%");
            this.render();

            // Once you're in this view, you shouldn't have to leave
            // (optimized for TVs)
            $("#euler-nav").hide();
            $("#bootstrap-footer").hide();
            $("#main-header").hide();
            $(".start-kiosk-mode").hide();

        },
    });

    root.App.Views.KpisView = KpisView;

})(this);
