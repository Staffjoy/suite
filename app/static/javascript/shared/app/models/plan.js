(function(root) {

    "use strict";

    var Plan = Backbone.Model.extend({
        urlRoot: "/api/v2/plans/",
        credentials: function() {
            return {
                username: API_KEY,
                password: "",
            };
        },
    });

    root.App.Models.Plan = Plan;
})(this);
