(function(root) {

    "use strict";

    var Models = root.App.Models,
        Collections = root.App.Collections,
        Admins = Collections.Base.extend({
            model: Models.Admin,
            endpoint: "admins/",
        })
    ;

    root.App.Collections.Admins = Admins;
})(this);
