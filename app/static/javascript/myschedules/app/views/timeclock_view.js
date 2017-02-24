(function(root) {

    "use strict";

    var Views = root.App.Views,
        Models = root.App.Models
    ;

    var TimeclockView = Views.Base.extend({
        el: "#planner-main",
        events: {
            "click #timeclockButton": "timeclockButtonClick",
        },
        initialize: function(opts) {
            TimeclockView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.locationModel)) {
                    this.locationModel = opts.locationModel;
                }
            }

        },
        render: function(opts) {
            var data = {
                active: this.isActive(),
            };

            if (this.isActive()) {
                var timeclockModel = this.collection.first(),
                    timezone = jstz.determine().name(),
                    start = moment.utc(timeclockModel.get('start')).tz(timezone)
                ;

                data.clockedIn = start.format('h:mm a');
            }

            this.$el.html(ich.timeclock(data));
            this.$clockedIn = $('#clockedIn');
            this.$clock = $('#clock');
            this.$elapsed = $('#elapsed');
            this.$button = $('#timeclockButton');
            this.$duration = this.$el.find('.duration-container');
            this.startTime();
            this.startPolling();

            if (this.isActive()) {
                this.clockedIn();
            } else {
                this.$duration.hide();
                this.clockedOut();
            }

            return this;
        },
        timeclockButtonClick: function() {
            var self = this,
                $button = this.$button
            ;

            $button.addClass("disabled");

            if (self.isActive()) {
                var timeclock = self.collection.first();

                self.addUpstreamModels(timeclock);

                timeclock.save({
                    "close": true
                }, {
                    success: function() {
                        self.collection.remove(timeclock);
                        $.notify({ message: "Clocked out after " + moment.utc(timeclock.get('start')).preciseDiff(moment.utc(timeclock.get('stop'))) },{ type: "success" });
                        self.clockedOut();
                        $button.removeClass("disabled");
                    },
                    error: function() {
                        $.notify({ message: "There was an error loading the page - please contact support if the problem persists" }, { type: "danger" });
                        $button.removeClass("disabled");
                    },
                    patch: true,
                });
            } else {
                var timeclock = new Models.Timeclock();

                self.addUpstreamModels(timeclock);

                timeclock.save({}, {
                    success: function() {
                        var timezone = jstz.determine().name();

                        timeclock.set('start', moment.utc().format("YYYY-MM-DDTHH:mm:ss"));
                        self.collection.add(timeclock);
                        $.notify({ message: "Clocked in at " + moment.utc(timeclock.get('start')).tz(timezone).format('h:mm a')},{ type: "success" });
                        self.clockedIn();
                        $button.removeClass("disabled");
                    },
                    error: function() {
                        $.notify({ message: "There was an error loading the page - please contact support if the problem persists" }, { type: "danger" });
                        $button.removeClass("disabled");
                    },
                });
            }
        },
        close: function() {
            clearTimeout(this.clock);
            clearTimeout(this.poll);
            TimeclockView.__super__.close.call(this);
        },
        startTime: function() {
            var self = this,
                timezone = jstz.determine().name(),
                now = moment.utc().tz(timezone)
            ;

            self.$clock.html(now.format('h:mm a'));

            if (this.isActive()) {
                var timeclockModel = self.collection.first(),
                    elapsed = timeclockModel.getDuration(timezone, true)
                ;

                self.$elapsed.html(elapsed);
            }

            self.clock = setTimeout(self.startTime.bind(self), 500);
        },
        startPolling: function() {
            var self = this,
                active = self.isActive(),
                id = active ? self.collection.first().id : false
            ;

            self.collection.fetch({
                success: function(collection) {
                    if (active) {
                        if (!self.isActive()) {
                            self.clockedOut();
                        } else if (id !== self.collection.first().id) {
                            self.clockedIn();
                        }
                    } else {
                        if (self.isActive()) {
                            self.clockedIn();
                        }
                    }
                }
            });

            self.poll = setTimeout(self.startPolling.bind(self), 15000);
        },
        isActive: function() {
            return this.collection.models.length === 1;
        },
        addUpstreamModels: function(timeclock) {
            var self = this;

            timeclock.addUpstreamModel("locationId", self.collection.getUpstreamModelId("locationId"));
            timeclock.addUpstreamModel("roleId", self.collection.getUpstreamModelId("roleId"));
            timeclock.addUpstreamModel("userId", self.collection.getUpstreamModelId("userId"));
        },
        clockedIn: function() {
            var self = this,
                timeclockModel = self.collection.first(),
                timezone = jstz.determine().name(),
                start = moment.utc(timeclockModel.get('start')).tz(timezone)
            ;

            self.$clockedIn.html(start.format('h:mm a'));
            self.$duration.slideDown();
            self.$button.html('Clock Out');
        },
        clockedOut: function() {
            var self = this;

            self.$duration.slideUp();
            self.$button.html('Clock In');
        },
    });

    root.App.Views.TimeclockView = TimeclockView;
})(this);
