(function(root) {

    "use strict";

    var Models = root.App.Models,
        Role = Models.Base.extend({
            endpoint: function() {
                var self = this,
                    locationId = self.getUpstreamModelId("locationId")
                ;

                return "locations/" + locationId + "/roles";
            },
            editableProperties: {
                name: {type: "str", name: "Name"},
                enable_timeclock: {type: "bool", name: "Timeclock"},
                enable_time_off_requests: {type: "bool", name: "Time Off Requests"},
            },
        })
    ;

    root.App.Models.Role = Role;
})(this);
