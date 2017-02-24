(function(root) {

    "use strict";

    var Models = root.App.Models,
        ScheduleTimeclock = Models.Timeclock.extend({
            endpoint: function() {
                var self = this,
                    locationId = self.getUpstreamModelId("locationId"),
                    roleId = self.getUpstreamModelId("roleId"),
                    scheduleId = self.getUpstreamModelId("scheduleId")
                ;

                return "locations/" + locationId + "/roles/" + roleId +"/schedules/" + scheduleId + "/timeclocks/";
            },
        })
    ;

    root.App.Models.ScheduleTimeclock = ScheduleTimeclock;
})(this);
