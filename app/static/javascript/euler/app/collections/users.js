(function(root) {

    "use strict";

    var Models = root.App.Models,
        Collections = root.App.Collections,
        Users = Collections.Base.extend({
            model: Models.User,
            endpoint: "users/",
        })
    ;

    root.App.Collections.Users = Users;
})(this);
