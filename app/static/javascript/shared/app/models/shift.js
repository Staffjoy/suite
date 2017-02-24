(function(root) {

    "use strict";

    var Models = root.App.Models,
        Shift = Models.Base.extend({
            endpoint: function() {
                var self = this,
                    locationId = self.getUpstreamModelId("locationId"),
                    roleId = self.getUpstreamModelId("roleId")
                ;

                return "locations/" + locationId + "/roles/" + roleId + "/shifts";
            },
        })
    ;

    root.App.Models.Shift = Shift;
})(this);
