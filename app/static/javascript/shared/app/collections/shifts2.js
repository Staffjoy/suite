(function(root) {

    "use strict";

    var Models = root.App.Models,
        Collections = root.App.Collections,
        Shifts = Collections.Base.extend({
            model: Models.Shift,
            endpoint: function() {
                var self = this,
                    locationId = self.getUpstreamModelId("locationId"),
                    roleId = self.getUpstreamModelId("roleId")
                ;

                return "locations/" + locationId + "/roles/" + roleId + "/shifts/" + self.getParams();
            },
            parse: function(response) {
                if (_.has(this.params, "include_summary")) {
                    return response.summary;
                } else {
                    return response.data;
                }
            },
        })
    ;

    root.App.Collections.Shifts = Shifts;
})(this);
