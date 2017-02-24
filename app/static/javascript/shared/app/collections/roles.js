(function(root) {

    "use strict";

    var Models = root.App.Models,
        Collections = root.App.Collections,
        Roles = Collections.Base.extend({
            model: Models.Role,
            endpoint: function() {
                var self = this,
                    locationId = self.getUpstreamModelId("locationId")
                ;

                return "locations/" + locationId + "/roles/" + self.getParams();
            },
        })
    ;

    root.App.Collections.Roles = Roles;
})(this);
