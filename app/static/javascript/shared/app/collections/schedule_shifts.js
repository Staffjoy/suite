(function(root) {

    "use strict";

    var Models = root.App.Models,
        Collections = root.App.Collections,
        ScheduleShifts = Collections.Base.extend({
            model: Models.Shift,
            endpoint: function() {
                var self = this,
                    locationId = self.getUpstreamModelId("locationId"),
                    roleId = self.getUpstreamModelId("roleId"),
                    scheduleId = self.getUpstreamModelId("scheduleId")
                ;

                return "locations/" + locationId + "/roles/" + roleId +"/schedules/" + scheduleId + "/shifts/" + self.getParams();
            },
            parse: function(response) {
                if (_.has(this.params, "include_summary")) {
                    return response.summary;
                } else {
                    return response.data;
                }
            },
        })
    ;

    root.App.Collections.ScheduleShifts = ScheduleShifts;
})(this);
