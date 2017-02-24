(function(root) {

    "use strict";

    var Models = root.App.Models,
        Collections = root.App.Collections,
        LocationAttendance = Collections.Base.extend({
            model: Models.Base,
            endpoint: function() {
                var self = this,
                    locationId = self.getUpstreamModelId("locationId")
                ;

                return "locations/" + locationId + "/attendance/" + self.getParams();
            },
        })
    ;

    root.App.Collections.LocationAttendance = LocationAttendance;
})(this);
