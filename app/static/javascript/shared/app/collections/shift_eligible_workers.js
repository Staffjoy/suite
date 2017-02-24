(function(root) {

    "use strict";

    var Models = root.App.Models,
        Collections = root.App.Collections,
        ShiftEligibleWorkers = Collections.Base.extend({
            model: Models.Base,
            endpoint: function() {
                var self = this,
                    locationId = self.getUpstreamModelId("locationId"),
                    roleId = self.getUpstreamModelId("roleId"),
                    shiftId = self.getUpstreamModelId("shiftId")
                ;

                return "locations/" + locationId + "/roles/" + roleId + "/shifts/" + shiftId + "/users/";
            },
            parse: function(response) {
                return response.data;
            },
        })
    ;

    root.App.Collections.ShiftEligibleWorkers = ShiftEligibleWorkers;
})(this);
