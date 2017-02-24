(function(root) {

    "use strict";

    var Models = root.App.Models,
        Collections = root.App.Collections,
        Organizations = Collections.Base.extend({
            model: Models.Organization,
            endpoint: "organizations/",
        })
    ;

    root.App.Collections.Organizations = Organizations;
})(this);
