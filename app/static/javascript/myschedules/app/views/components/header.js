(function(root) {

    "use strict";

    var Views = root.App.Views;

    var HeaderView = Views.Base.extend({
        el: ".planner-header-container",
        initialize: function(opts) {
            HeaderView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.models)) {
                    this.models = opts.models;
                }
            }
            this.$timeclockButton;
            this.$timeclockButtonSpan;
            this.$mySchedulesButton;
            this.$headerName;
        },
        render: function() {
            var self = this;

            self.$el.html(ich.header());

            self.$headerName = $(".planner-header-name");
            self.$timeclockButton = $("#timeclock-btn");
            self.$mySchedulesButton = $("#my-schedules-btn");
            self.$timeclockButtonSpan = self.$timeclockButton.find(".timeclock-nav-icon");

            return this;
        },
        populateName: function() {
            var self = this,
                organization = self.models.organization.attributes.data.name,
                location = self.models.location.attributes.data.name,
                role = self.models.role.attributes.data.name
            ;

            self.$headerName.text(organization + " | " + location + " | " + role);
        },
        showTimeclockButton: function(enable_timeclock) {
            var self = this;

            self.$mySchedulesButton.addClass("hidden");

            if (enable_timeclock) {
                self.$timeclockButton.removeClass("hidden");

                // pulse if an active timeclock
                if (!_.isUndefined(self.models.timeclocks) && !self.models.timeclocks.isEmpty()) {
                    self.$timeclockButton.addClass("timeclock-nav-btn pulse");
                    self.$timeclockButton.removeClass("btn-default");
                    self.$timeclockButtonSpan.addClass("timeclock-nav-active");
                    self.$timeclockButtonSpan.removeClass("timeclock-nav-inactive");
                } else {
                    self.$timeclockButton.removeClass("timeclock-nav-btn pulse");
                    self.$timeclockButton.addClass("btn-default");
                    self.$timeclockButtonSpan.removeClass("timeclock-nav-active");
                    self.$timeclockButtonSpan.addClass("timeclock-nav-inactive");
                }
            }
        },
        showMySchedulesButton: function() {
            var self = this;

            self.$mySchedulesButton.removeClass("hidden");
            self.$timeclockButton.addClass("hidden");
        }
    });

    root.App.Views.Components.HeaderView = HeaderView;
})(this);
