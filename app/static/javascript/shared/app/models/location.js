(function(root) {

    "use strict";

    var Models = root.App.Models,
        Location = Models.Base.extend({
            endpoint:  "locations",
            editableProperties: {
                name: {type: "str", name: "Name"},
            },
        })
    ;

    root.App.Models.Location = Location;
})(this);
