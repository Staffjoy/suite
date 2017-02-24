(function(root) {

    "use strict";

    var Models = root.App.Models,
        Collections = root.App.Collections,
        ScheduleTimeclocks = Collections.Timeclocks.extend({
            model: Models.ScheduleTimeclock,
            endpoint: function() {
                var self = this,
                    locationId = self.getUpstreamModelId("locationId"),
                    roleId = self.getUpstreamModelId("roleId"),
                    scheduleId = self.getUpstreamModelId("scheduleId")
                ;

                return "locations/" + locationId + "/roles/" + roleId +"/schedules/" + scheduleId + "/timeclocks/" + self.getParams();
            },
        })
    ;

    root.App.Collections.ScheduleTimeclocks = ScheduleTimeclocks;
})(this);
