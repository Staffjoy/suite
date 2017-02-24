(function(root) {

    "use strict";

    var Collections = root.App.Collections,
        Models = root.App.Models,
        Views = root.App.Views,
        Util = root.App.Util
    ;

    var AvailabilityModalView = Views.Base.extend({
        el: ".modal-placeholder",
        events: {},
        initialize: function(opts) {
            /* uses a user availabilities model */

            AvailabilityModalView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.id)) {
                    this.id = opts.id;
                }

                if (!_.isUndefined(opts.el)) {
                    this.el = opts.el;
                }

                if (!_.isUndefined(opts.userName)) {
                    this.userName = opts.userName;
                }
            }
        },
        render: function(opts) {
            var self = this,
                $el = $(self.el),
                weekStart = self.model.get("start"),
                weekStartMoment = moment(weekStart),
                data = {
                    id: self.id,
                    weekName: weekStartMoment.format("D MMMM YYYY"),
                    userName: self.userName,
                },
                timeRange = {
                    min: 4,
                    max: 27,
                },
                demand
            ;

            if (_.isNull(self.model.get("demand"))) {
                demand = Util.generateFullDayAvailability();
            } else {
                demand = self.model.get("demand");
            }

            $el.html(ich.modal_user_availability(data));

            $("#availabilityModal-" + self.id).modal();

            self.addDelegateView(
                "set-availability",
                new Views.Components.ViewAvailability({
                    el: ".user-availability-placeholder",
                    availability: self.model.get("availability"),
                    demand: demand,
                    timeRange: timeRange,
                    weekStart: weekStart,
                    weekStartMoment: weekStartMoment,
                })
            );
        },
    });

    root.App.Views.Components.AvailabilityModalView = AvailabilityModalView;

})(this);
