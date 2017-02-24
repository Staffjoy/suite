(function(root) {

    "use strict";

    var Models = root.App.Models,
        Collections = root.App.Collections,
        Locations = Collections.Base.extend({
            model: Models.Location,
            endpoint: function() {
                var self = this;

                return "locations/" + self.getParams();
            },
        })
    ;

    root.App.Collections.Locations = Locations;
})(this);
