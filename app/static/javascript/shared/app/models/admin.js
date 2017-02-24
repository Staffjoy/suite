(function(root) {

    "use strict";

    var Models = root.App.Models,
        Admin = Models.Base.extend({
            endpoint:  "admins",
        })
    ;

    root.App.Models.Admin = Admin;
})(this);
