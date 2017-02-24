(function(root) {

    "use strict";

    var Models = root.App.Models,
        Timeclock = Models.Base.extend({
            endpoint: function() {
                var self = this,
                    locationId = self.getUpstreamModelId("locationId"),
                    roleId = self.getUpstreamModelId("roleId"),
                    userId = self.getUpstreamModelId("userId")
                ;

                return "locations/" + locationId + "/roles/" + roleId +"/users/" + userId + "/timeclocks/";
            },
            getDuration: function(timezone, includeSeconds) {
                var self = this,
                    start = moment.utc(self.get('start')).tz(timezone),
                    stop =  self.has('stop') ? moment.utc(self.get('stop')).tz(timezone) : moment.utc().tz(timezone)
                ;

                return start.preciseDiff(stop, !!includeSeconds);
            },
        })
    ;

    root.App.Models.Timeclock = Timeclock;
})(this);
