(function(root) {

    "use strict";

    var Models = root.App.Models,
        Collections = root.App.Collections,
        ScheduleTimeOffRequests = Collections.Base.extend({
            model: Models.TimeOffRequest,
            endpoint: function() {
                var self = this,
                    locationId = self.getUpstreamModelId("locationId"),
                    roleId = self.getUpstreamModelId("roleId"),
                    scheduleId = self.getUpstreamModelId("scheduleId")
                ;

                return "locations/" + locationId + "/roles/" + roleId +"/schedules/" + scheduleId + "/timeoffrequests/" + self.getParams();
            },
            parse: function(response) {
                return response.data;
            },
        })
    ;

    root.App.Collections.ScheduleTimeOffRequests = ScheduleTimeOffRequests;
})(this);
