(function(root) {

    "use strict";

    var Models = root.App.Models,
        Schedule = Models.Base.extend({
            endpoint: function() {
                var self = this,
                    organizationId = self.getUpstreamModelId("organizationId"),
                    locationId = self.getUpstreamModelId("locationId"),
                    roleId = self.getUpstreamModelId("roleId")
                ;

                return "organizations/" + organizationId + "/locations/" + locationId + "/roles/" + roleId + "/schedules";
            },
        })
    ;

    root.App.Models.Schedule = Schedule;
})(this);
