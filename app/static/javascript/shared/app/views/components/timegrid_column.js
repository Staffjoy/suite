(function(root) {

    "use strict";

    var Views = root.App.Views,
        Util = root.App.Util
    ;

    var TimegridColumn = Views.Base.extend({
        initialize: function(opts) {
            TimegridColumn.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.el)) {
                    this.el = opts.el;
                }

                if (!_.isUndefined(opts.dayName)) {
                    this.dayName = opts.dayName;
                }

                if (!_.isUndefined(opts.dayLabel)) {
                    this.dayLabel = opts.dayLabel;
                }

                if (!_.isUndefined(opts.timegridColumnData)) {
                    this.timegridColumnData = opts.timegridColumnData;
                }

                if (!_.isUndefined(opts.timeRange)) {
                    this.timeRange = opts.timeRange;
                }

                if (!_.isUndefined(opts.dangerMode)) {
                    this.dangerMode = opts.dangerMode;
                }

                if (!_.isUndefined(opts.disabledRange)) {
                    this.disabledRange = opts.disabledRange;
                }

                if (!_.isUndefined(opts.timegridColumnButton)) {
                    this.timegridColumnButton = opts.timegridColumnButton;
                }

                if (!_.isUndefined(opts.date)) {
                    this.date = opts.date;
                }
            }
        },
        render: function(opts) {
            var self = this,
                timegridColumn = ".timegrid-column-content-" + self.dayName,
                currentState,
                adjustedIndex,
                index,
                opts,
                value,
                label,
                data
            ;

            self.$el.append(ich.timegrid_column({
                    columnNameLabel: self.dayName.charAt(0).toUpperCase() + self.dayName.slice(1),
                    columnName: self.dayName,
                    columnDayLabel: self.dayLabel,
                    timegridColumnButton: !!self.timegridColumnButton,
                })
            );

            // add cells to the column
            for (index=0; index < self.timegridColumnData.length; index++) {

                if (_.isNumber(self.timegridColumnData[index])) {
                    value = self.timegridColumnData[index];
                    label = Util.formatIntIn12HourTime(index);
                } else {
                    value = self.timegridColumnData[index].data;
                    label = self.timegridColumnData[index].label;
                }

                if (self.disabledRange[index] === 0) {
                    currentState = 'disabled';
                } else if (value === 1) {
                    currentState = "active";
                } else {
                    currentState = "inactive";
                }

                data = {
                    state: currentState,
                    index: index,
                    dayName: self.dayName,
                    dangerMode: self.dangerMode,
                    blockId: self.dayName + "-" + index,
                    blockLabel: label,
                    disabled: currentState === 'disabled',
                }

                if (!!self.timegridColumnData[index].subLabel) {
                    data.subLabel = self.timegridColumnData[index].subLabel;
                }

                $(timegridColumn).append(ich.timegrid_block(data));

            }

            if (!!self.timegridColumnButton) {
                opts = self.timegridColumnButton.opts;
                opts.el = '.timegrid-column-button-view-container-' + self.dayName;
                opts.date = self.date;
                opts.timegridColumn = self;

                self.addDelegateView(
                    'timegrid-column-button-view-' + self.dayName,
                    new self.timegridColumnButton.view(opts)
                );
            }

            return this;
        },
        updateTimegrid: function(index, oldState, newState) {
            var self = this,
                uniqueId = self.dayName + "-" + index,
                $cell = $("#" + uniqueId),
                newTimegridColumnData = {
                    active: 1,
                    inactive: 0,
                }
            ;

            // change the coloring
            $cell.removeClass(oldState);
            $cell.addClass(newState);

            // update the data-state in the html
            $cell.attr("data-state", newState);

            // update value in data model
            self.timegridColumnData[index] = newTimegridColumnData[newState];

            return true;
        },
        disable: function() {
            var self = this,
                uniqueId,
                $cell,
                state,
                newTimegridColumnData = {
                    active: 1,
                    inactive: 0,
                }
            ;

            _.each(_.range(0, self.timegridColumnData.length), function(element, index, list) {
                uniqueId = self.dayName + "-" + index;
                $cell = $("#" + uniqueId);
                state = $cell.attr('data-state');

                self.updateTimegrid(index, state, 'disabled');
                $cell.removeClass('cursor-clickable');
                self.timegridColumnData[index] = 0;
            });
        },
        enable: function() {
            var self = this,
                uniqueId,
                $cell,
                state,
                newTimegridColumnData = {
                    active: 1,
                    inactive: 0,
                }
            ;

            _.each(_.range(0, self.timegridColumnData.length), function(element, index, list) {
                uniqueId = self.dayName + "-" + index;
                $cell = $("#" + uniqueId);
                state = $cell.attr('data-state');

                if (self.disabledRange[index] === 0) {
                    self.updateTimegrid(index, state, 'disabled');
                } else {
                    self.updateTimegrid(index, state, 'inactive');
                    $cell.addClass('cursor-clickable');
                }
                self.timegridColumnData[index] = 0;
            });
        },
    });

    root.App.Views.Components.TimegridColumn = TimegridColumn;

})(this);
