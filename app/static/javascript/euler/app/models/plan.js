(function(root) {

    "use strict";

    var Models = root.App.Models,
        Plan = Models.Base.extend({
            endpoint: "plans",
        })
    ;

    root.App.Models.Plan = Plan;
})(this);
