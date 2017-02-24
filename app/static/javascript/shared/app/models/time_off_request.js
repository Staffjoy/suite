(function(root) {

    "use strict";

    var Models = root.App.Models,
        TimeOffRequest = Models.Base.extend({
            endpoint: function() {
                var self = this,
                    locationId = self.getUpstreamModelId("locationId"),
                    roleId = self.getUpstreamModelId("roleId"),
                    userId = self.getUpstreamModelId("userId")
                ;

                return "locations/" + locationId + "/roles/" + roleId + "/users/" + userId + "/timeoffrequests";
            },
        })
    ;

    root.App.Models.TimeOffRequest = TimeOffRequest;
})(this);
