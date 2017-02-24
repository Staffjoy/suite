(function(root) {

    "use strict";

    var Views = root.App.Views,
        Util = root.App.Util
    ;

    var WeekSummaryCardView = Views.Base.extend({
        el: ".week-summary-card-container",
        events: {},
        initialize: function(opts) {
            WeekSummaryCardView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.data)) {
                    this.shiftSummaries = _.map(opts.data, function(shiftSummaryCollection) {
                        var shiftSummaryData = {},
                            unassignedShiftsSummary = shiftSummaryCollection.findWhere({ user_id: 0 });
                        ;

                        shiftSummaryData.roleName = shiftSummaryCollection.roleName;
                        shiftSummaryData.data = [];

                        shiftSummaryCollection.remove(unassignedShiftsSummary, { silent: true });
                        shiftSummaryCollection.push(unassignedShiftsSummary, { silent: true });

                        shiftSummaryCollection.each(function(shiftSummary) {
                            shiftSummaryData.data.push(_.extend({},
                                shiftSummary.attributes,
                                {duration: Util.formatMinutesDuration(shiftSummary.get("minutes"))}
                            ));
                        });

                        return shiftSummaryData;
                    });
                }
            }
        },
        render: function(opts) {
            var self = this,
                data
            ;

            data = {
                shiftSummaries: self.shiftSummaries,
            };

            self.$el.append(ich.week_summary_card(data));

            return this;
        },
    });

    root.App.Views.WeekSummaryCardView = WeekSummaryCardView;

})(this);
