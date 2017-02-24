(function(root) {

    "use strict";

    var Models = root.App.Models,
        Collections = root.App.Collections,
        TimeOffRequests = Collections.Base.extend({
            model: Models.TimeOffRequest,
            endpoint: function() {
                var self = this,
                    locationId = self.getUpstreamModelId("locationId"),
                    roleId = self.getUpstreamModelId("roleId"),
                    userId = self.getUpstreamModelId("userId")
                ;

                return "locations/" + locationId + "/roles/" + roleId + "/users/" + userId + "/timeoffrequests/" + self.getParams();
            },
            parse: function(response) {
                return response.data;
            },
        })
    ;

    root.App.Collections.TimeOffRequests = TimeOffRequests;
})(this);
