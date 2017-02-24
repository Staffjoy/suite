(function(root) {

    "use strict";

    var Models = root.App.Models,
        RecurringShift = Models.Base.extend({
            endpoint: function() {
                var self = this,
                    locationId = self.getUpstreamModelId("locationId"),
                    roleId = self.getUpstreamModelId("roleId")
                ;

                return "locations/" + locationId + "/roles/" + roleId + "/recurringshifts/";
            },
        })
    ;

    root.App.Models.RecurringShift = RecurringShift;
})(this);
