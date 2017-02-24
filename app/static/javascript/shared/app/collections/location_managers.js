(function(root) {

    "use strict";

    var Models = root.App.Models,
        Collections = root.App.Collections,
        LocationManagers = Collections.Base.extend({
            model: Models.LocationManager,
            endpoint: function() {
                var self = this,
                    locationId = self.getUpstreamModelId("locationId")
                ;

                return "locations/" + locationId + "/managers/" + self.getParams();
            },
        })
    ;

    root.App.Collections.LocationManagers = LocationManagers;
})(this);
