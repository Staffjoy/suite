(function(root) {

    "use strict";

    var Models = root.App.Models,
        Collections = root.App.Collections,
        RecurringShifts = Collections.Base.extend({
            model: Models.RecurringShift,
            endpoint: function() {
                var self = this,
                    locationId = self.getUpstreamModelId("locationId"),
                    roleId = self.getUpstreamModelId('roleId')
                ;

                return "locations/" + locationId + "/roles/" + roleId + '/recurringshifts/' + self.getParams();
            },
            parse: function(response) {
                return response.data;
            }
        })
    ;

    root.App.Collections.RecurringShifts = RecurringShifts;
})(this);
