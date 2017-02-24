(function(root) {

    "use strict";

    var Views = root.App.Views,
        Util = root.App.Util
    ;

    var ListShiftsCard = Views.Base.extend({
        el: ".list-shifts-placeholder",
        events: {},
        initialize: function(opts) {
            ListShiftsCard.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.weekStartMoment)) {
                    this.weekStartMoment = opts.weekStartMoment;
                }
            }
            this.$table;
        },
        render: function(opts) {
            var self = this,
                data = {
                    title: "Shifts This Week"
                }
            ;

            self.$el.html(ich.list_shifts_card(data));

            // add listener for adding new model to collection
            self.collection.on("add", function(model) {
                self.renderTable();
            });

            self.$table = $(".list-shifts-table");

            self.renderTable();
            return this;
        },
        renderTable: function() {
            var self = this,
                renderData = {
                    data: _.map(self.collection.models, function(shift) {
                        var startLocalMoment = moment.utc(shift.get("start")).local(),
                            stopLocalMoment = moment.utc(shift.get("stop")).local(),
                            start = Util.momentMobileDisplay(startLocalMoment),
                            end = Util.momentMobileDisplay(stopLocalMoment)
                        ;

                        return {
                            date: startLocalMoment.format("M/D"),
                            dayName: startLocalMoment.format("ddd"),
                            start: start,
                            end: end,
                            description: shift.get('description') || '',
                        };
                    })
                }
            ;

            self.$table.html(ich.list_shifts_table(renderData));

            $(function () {
                $('[data-toggle="tooltip"]').tooltip()
            });
        },
        addToList: function(model) {
            var self = this;
            self.collection.add(model);
        },
    });

    root.App.Views.Components.ListShiftsCard = ListShiftsCard;

})(this);
