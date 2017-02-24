(function(root) {

    "use strict";

    var Views = root.App.Views,
        Models = root.App.Models
    ;

    var ScheduleMonitoringView = Views.Base.extend({
        el: "#euler-container",
        events: {
            "click .btn.requeue-schedule": "requeue_schedule",
            "click .btn.view-org": "view_org",
        },
        initialize: function(opts) {
            ScheduleMonitoringView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.el)) {
                    this.el = opts.el;
                }
            }
            this.collection.on('reset', this.render, this);

            // have view reload on 30 second interval
            this.reload = function() {
                var self = this;
                self.timer = setTimeout(function() {
                    self.update_page();
                }, 3000);
            };
        },
        close: function() {
            clearTimeout(this.timer);
            ScheduleMonitoringView.__super__.close.call(this);
        },
        render: function(opts) {
            var self = this,
                model = self.collection.first(),
                data = {
                    chomp: _.map(model.get("chomp"), function(model) {

                        var tempMoment = moment.utc(),
                            elapsedSeconds = tempMoment.diff(moment(model.chomp_start)) / 1000
                        ;

                        return {
                            organization: model.organization,
                            organizationId: model.organization_id,
                            location: model.location,
                            locationId: model.location_id,
                            role: model.role,
                            roleId: model.role_id,
                            scheduleId: model.schedule_id,
                            schedulingSystem: model.schedule_system,
                            state: model.state,
                            paid: model.paid,
                            plan: model.plan,
                            processingTime: tempMoment.preciseDiff(moment.utc(model.chomp_start)),
                            lastUpdate: tempMoment.preciseDiff(moment.utc(model.last_update)),
                            processingState: model.state === "chomp-processing",
                            dangerState: elapsedSeconds > 3300,
                            type: "chomp",
                        };
                    }),
                    mobius: _.map(model.get("mobius"), function(model) {

                        var tempMoment = moment.utc(),
                            elapsedSeconds = tempMoment.diff(moment(model.mobius_start)) / 1000
                        ;

                        return {
                            organization: model.organization,
                            organizationId: model.organization_id,
                            location: model.location,
                            locationId: model.location_id,
                            role: model.role,
                            roleId: model.role_id,
                            scheduleId: model.schedule_id,
                            schedulingSystem: model.schedule_system,
                            state: model.state,
                            paid: model.paid,
                            plan: model.plan,
                            processingTime: tempMoment.preciseDiff(moment.utc(model.mobius_start)),
                            lastUpdate: tempMoment.preciseDiff(moment.utc(model.last_update)),
                            processingState: model.state === "mobius-processing",
                            dangerState: elapsedSeconds > 6900,
                            type: "mobius",
                        };
                    }),
                }
            ;

            self.$el.html(ich.schedule_monitoring(data));

            this.reload();

            return this;
        },
        requeue_schedule: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target).closest(".requeue-schedule"),
                organizationId = $target.attr("data-organizationId"),
                locationId = $target.attr("data-locationId"),
                roleId = $target.attr("data-roleId"),
                scheduleId = $target.attr("data-scheduleId"),
                scheduleModel = new Models.Schedule({
                    id: parseInt(scheduleId)
                }),
                type = $target.attr("data-type"),
                payload,
                success,
                error
            ;

            if (type === "chomp") {
                payload = {state: "chomp-queue"};
            } else if (type === "mobius") {
                payload = {state: "mobius-queue"};
            }

            scheduleModel.addUpstreamModel("organizationId", organizationId);
            scheduleModel.addUpstreamModel("locationId", locationId);
            scheduleModel.addUpstreamModel("roleId", roleId);

            success = function(model, response, opts) {
                self.update_page();
            };

            error = function(model, response, opts) {
                $.notify({message:"Failed to requeue the schedule"},{type:"danger"});
            };

            scheduleModel.save(
                payload,
                {
                    success: success,
                    error: error,
                    patch: true,
                }
            );
        },
        view_org: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target).closest(".view-org"),
                id = $target.attr("data-organizationId")
            ;

            Backbone.history.navigate("organizations/" + id, {trigger:true});
        },
        update_page: function() {
            var self = this,
                error
            ;

            error = function(collection, response, opts) {
                $.notify({message:"Failed to refresh page"},{type:"danger"});
            };

            self.collection.fetch({
                error: error,
                reset: true,
            });
        },
    });

    root.App.Views.ScheduleMonitoringView = ScheduleMonitoringView;

})(this);
