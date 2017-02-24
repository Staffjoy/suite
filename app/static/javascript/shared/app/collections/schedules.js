(function(root) {

    "use strict";

    var Models = root.App.Models,
        Collections = root.App.Collections,
        Schedules = Collections.Base.extend({
            model: Models.Schedule,
            endpoint: function() {
                var self = this,
                    locationId = self.getUpstreamModelId("locationId"),
                    roleId = self.getUpstreamModelId("roleId")
                ;

                return "locations/" + locationId + "/roles/" + roleId +"/schedules/" + self.getParams();
            },
            parse: function(response) {
                return response.data;
            },
        })
    ;

    root.App.Collections.Schedules = Schedules;
})(this);
