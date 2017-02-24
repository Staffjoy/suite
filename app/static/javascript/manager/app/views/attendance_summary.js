(function(root) {

    "use strict";

    var Views = root.App.Views,
        Models = root.App.Models
    ;

    var AttendanceSummaryView = Views.Base.extend({
        el: ".attendance-summary-placeholder",
        events: {},
        initialize: function(opts) {
            AttendanceSummaryView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.locationId)) {
                    this.locationId = opts.locationId;
                }

                if (!_.isUndefined(opts.rolesCollection)) {
                    this.rolesCollection = opts.rolesCollection;
                }
            }
        },
        render: function(opts) {
            var self = this
            ;

            // collapse/expand events
            self.$el.on('show.bs.collapse', function (event) {
                var $target = $(event.target),
                    collapseId = $target.data('collapse-id'),
                    selector = '.collapse-btn-attendance-summary'
                ;

                $(selector).find('.glyphicon').removeClass('glyphicon-chevron-down').addClass('glyphicon-chevron-up');
            });

            self.$el.on('hide.bs.collapse', function (event) {
                var $target = $(event.target),
                    collapseId = $target.data('collapse-id'),
                    selector = '.collapse-btn-attendance-summary'
                ;

                $(selector).find('.glyphicon').removeClass('glyphicon-chevron-up').addClass('glyphicon-chevron-down');
            });

            self.$el.html(ich.attendance_summary_card());
            self.renderTable();

            return this;
        },
        renderTable: function() {
            var self = this,
                data = {data: _.map(self.collection.models, function(model) {
                    var roleModel = self.rolesCollection.get(model.get("role_id")),
                        users = roleModel.get("users"),
                        userObj = _.findWhere(users, {id: model.get("user_id")})
                    ;

                    return {
                        name: _.isNull(userObj.name) ? userObj.email : userObj.name,
                        role: roleModel.get("name"),
                        logged_time: moment.unix(0).preciseDiff(moment.unix(model.get("logged_time"))),
                        scheduled_time: moment.unix(0).preciseDiff(moment.unix(model.get("scheduled_time"))),
                        shift_count: model.get("shift_count"),
                        timeclock_count: model.get("timeclock_count"),
                    };
                })};
            ;

            $("#attendance-table-summary").html(ich.attendance_summary_table(data));
        },
        updateUserModelData: function(userId, roleId, addSeconds, deductSeconds, timeclockAdjustment) {
            timeclockAdjustment = timeclockAdjustment || 0;

            var self = this,
                modelIndex = self.collection.getIndexBy("user_id", parseInt(userId)),
                model,
                logged_time,
                timeclock_count
            ;

            // add a summary for person if they just had a 1st record created for them
            if (modelIndex < 0) {
                self.collection.add(
                    new Models.Base({
                        role_id: roleId,
                        user_id: userId,
                        logged_time: addSeconds,
                        scheduled_time: 0,
                        timeclock_count: 1,
                        shift_count: 0,
                    })
                );
            }

            // update an existing record
            else {
                model = self.collection.models[modelIndex];
                logged_time = model.get("logged_time");
                logged_time = logged_time + addSeconds - deductSeconds;
                timeclock_count = model.get("timeclock_count") + timeclockAdjustment,

                model.set({
                    logged_time: logged_time,
                    timeclock_count: timeclock_count
                });
                self.collection.models[modelIndex] = model;
            }

            self.renderTable();
        },
    });

    root.App.Views.AttendanceSummaryView = AttendanceSummaryView;

})(this);
