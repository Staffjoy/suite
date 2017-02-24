(function(root) {

    "use strict";

    var Models = root.App.Models,
        Preference = Models.Base.extend({
            endpoint: function() {
                var self = this,
                    locationId = self.getUpstreamModelId("locationId"),
                    roleId = self.getUpstreamModelId("roleId"),
                    scheduleId = self.getUpstreamModelId("scheduleId")
                ;

                return "locations/" + locationId + "/roles/" + roleId + "/schedules/" + scheduleId + "/preferences/";
            },
            parse: function(response) {
                return response.data;
            },
        })
    ;

    root.App.Models.Preference = Preference;
})(this);
