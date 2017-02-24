(function(root) {

    "use strict";

    var Models = root.App.Models,
        Collections = root.App.Collections,
        Plans = Collections.Base.extend({
            model: Models.Plan,
            endpoint: "plans/",
            parse: function(response) {
                return response.data;
            },
        })
    ;

    root.App.Collections.Plans = Plans;
})(this);
