(function(root) {

    "use strict";

    var Models = root.App.Models,
        Schedule = Models.Base.extend({
            endpoint: function() {
                var self = this,
                    locationId = self.getUpstreamModelId("locationId"),
                    roleId = self.getUpstreamModelId("roleId")
                ;

                return "locations/" + locationId + "/roles/" + roleId + "/schedules";
            },
        })
    ;

    root.App.Models.Schedule = Schedule;
})(this);
