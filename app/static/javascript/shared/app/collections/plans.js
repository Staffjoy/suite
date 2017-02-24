(function(root) {

    "use strict";

    var Models = root.App.Models,
        Plans = Backbone.Collection.extend({
            model: Models.Plan,
            url: "/api/v2/plans/",
            credentials: function() {
                return {
                    username: API_KEY,
                    password: "",
                };
            },
            parse: function(response) {
                return response.data;
            },
        })
    ;

    root.App.Collections.Plans = Plans;
})(this);
