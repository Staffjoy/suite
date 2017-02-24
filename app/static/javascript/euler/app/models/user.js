(function(root) {

    "use strict";

    var Models = root.App.Models,
        User = Models.Base.extend({
            endpoint: "users",
            editableProperties: {
                // I'm using Python data types . . . because why not
                username: {type: "str", name: "Username"},
                name: {type: "str", name: "Name"},
                email: {type: "str", name: "Email"},
                sudo: {type: "bool", name: "Sudo"},
                active: {type: "bool", name: "Account Active"},
            },
        })
    ;

    root.App.Models.User = User;
})(this);
