(function(root) {

    "use strict";

    var Models = root.App.Models,
        Collections = root.App.Collections,
        UserRoles = Collections.Base.extend({
            model: Models.UserRole,
            endpoint: function() {
                var self = this,
                    locationId = self.getUpstreamModelId("locationId"),
                    roleId = self.getUpstreamModelId("roleId")
                ;

                return "locations/" + locationId + "/roles/" + roleId +"/users/";
            },
        })
    ;

    root.App.Collections.UserRoles = UserRoles;
})(this);
