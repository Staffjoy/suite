(function(root) {

    "use strict";

    var Models = root.App.Models,
        UserRole = Models.Base.extend({
            endpoint: function() {
                var self = this,
                    locationId = self.getUpstreamModelId("locationId"),
                    roleId = self.getUpstreamModelId("roleId")
                ;

                return "locations/" + locationId + "/roles/" + roleId + "/users";
            },
            editableProperties: {
                internal_id: {type: "str", name: "Worker ID"},
            },
        })
    ;

    root.App.Models.UserRole = UserRole;
})(this);
