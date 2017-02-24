(function(root) {

    "use strict";

    var Views = root.App.Views,
        Models = root.App.Models,
        Util = root.App.Util
    ;

    var WorkingHoursCard = Views.Base.extend({
        el: ".working-hours-card-placeholder",
        events: {
            "click .save-working-hours .btn" : "saveWorkingHours",
        },
        initialize: function(opts) {
            WorkingHoursCard.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.el)) {
                    this.el = opts.el;
                }

                if (!_.isUndefined(opts.organizationModel)) {
                    this.organizationModel = opts.organizationModel;
                }

                this.timeRange = {
                    min: 0,
                    max: 23,
                };

                this.daysInWeek = 7;
            }
        },
        render: function(opts) {
            var self = this,
                data = {
                    workerName: self.model.get('name'),
                }
            ;

            self.$el.on('show.bs.collapse', function (event) {
                var $target = $(event.target),
                    collapseId = $target.data('collapse-id'),
                    selector = '.collapse-button-' + collapseId
                ;

                $(selector).find('.glyphicon').removeClass('glyphicon-chevron-down').addClass('glyphicon-chevron-up');
            });

            self.$el.on('hide.bs.collapse', function (event) {
                var $target = $(event.target),
                    collapseId = $target.data('collapse-id'),
                    selector = '.collapse-button-' + collapseId
                ;

                $(selector).find('.glyphicon').removeClass('glyphicon-chevron-up').addClass('glyphicon-chevron-down');
            });

            self.$el.append(ich.working_hours_card(data));

            self.addDelegateView(
                "set-working-hours",
                new Views.Components.Timegrid({
                    timegridData: self.model.get('working_hours'),
                    timeRange: self.timeRange,
                    dayWeekStarts: self.organizationModel.get('day_week_starts'),
                    dangerMode: true,
                })
            );

            return this;
        },
        close: function() {
            if (this.hasChanged()) {
                $.notify({ message:'Working hours not saved.' }, { type:'warning' });
            }

            this.$el.off("hide.bs.collapse");
            this.$el.off("show.bs.collapse");

            WorkingHoursCard.__super__.close.call(this);
        },
        saveWorkingHours: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                timegridData = self.delegateViews["set-working-hours"].getTimegridData(),
                success,
                error
            ;

            success = function(collection, response, opts) {
                $.notify({message:"Working hours saved"}, {type:"success"});
                self.setChanged(false);
            };

            error = function(collection, response, opts) {
                $.notify({message:"Unable to save working hours. Please contact support if the problem persists."},{type: "danger"});
            };

            // update model
            self.model.set("working_hours", timegridData);
            self.model.save(
                { working_hours: JSON.stringify(timegridData) },
                { success: success, error: error, patch: true }
            );
        },
        setChanged: function(value) {
            var self = this;
            value = !!value;

            self.delegateViews["set-working-hours"].changed = value;
        },
        hasChanged: function() {
            var self = this;

            return self.delegateViews["set-working-hours"].changed;
        },
    });

    root.App.Views.WorkingHoursCard = WorkingHoursCard;

})(this);
