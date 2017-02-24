(function(root) {

    "use strict";

    var Models = root.App.Models,
        LocationManager = Models.Base.extend({
            endpoint: function() {
                var self = this,
                    locationId = self.getUpstreamModelId("locationId")
                ;

                return "locations/" + locationId + "/managers";
            },
            parse: function(response) {
                return _.isUndefined(response) ? response : response.data;
            },
        })
    ;

    root.App.Models.LocationManager = LocationManager;
})(this);
