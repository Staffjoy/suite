(function(root) {

    "use strict";

    var Views = root.App.Views,
        Collections = root.App.Collections
    ;

    var TimecardView = Views.Base.extend({
        el: ".timecard-placeholder",
        initialize: function(opts) {
            TimecardView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.locationModel)) {
                    this.locationModel = opts.locationModel;
                }

                if (!_.isUndefined(opts.timeOffRequestsCollection)) {
                    this.timeOffRequestsCollection = opts.timeOffRequestsCollection;
                }
            }
        },
        render: function(opts) {
            var self = this,
                timezone = jstz.determine().name(),
                inactiveTimeclocks = self.collection.filter(function(model) { return model.has('stop'); }),
                collection = new Collections.Base(),
                total,
                data = {}
            ;

            collection.sortBy('start');
            collection.add(inactiveTimeclocks);
            collection.add(self.timeOffRequestsCollection.models);

            total = collection.reduce(function(memo, model) {
                return memo += model.has('minutes_paid') ? model.get('minutes_paid') * 60 * 1000 : moment.utc(model.get('stop')).tz(timezone).diff(moment.utc(model.get('start')).tz(timezone));
            }, 0)

            data = {
                timeclocks: collection.map(function(model) {
                    var start = moment.utc(model.get('start')).tz(timezone),
                        stop = moment.utc(model.get('stop')).tz(timezone),
                        duration
                    ;

                    if (model.has('state') && model.get('state') === 'approved_paid') {
                        duration = moment.preciseDiff(0, model.get('minutes_paid') * 60 * 1000);
                    } else if (!model.has('state')) {
                        duration = model.getDuration(timezone);
                    }

                    return {
                        day: start.format('M/D'),
                        start: start.format('h:mm a'),
                        stop: stop.format('h:mm a'),
                        duration: duration,
                        timeOffRequest: model.has('state'),
                        approvedPaid: model.get('state') === 'approved_paid',
                        approvedUnpaid: model.get('state') === 'approved_unpaid',
                        sick: model.get('state') === 'sick',
                    };
                }),
                total: moment.preciseDiff(0, total),
            };

            this.$el.html(ich.timecard_card(data));

            return this;
        },
    });

    root.App.Views.Components.TimecardView = TimecardView;
})(this);
