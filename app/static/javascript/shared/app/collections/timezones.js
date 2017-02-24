(function(root) {

    "use strict";

    var Models = root.App.Models,
        Timezones = Backbone.Collection.extend({
            model: Models.Timezone,
            url: "/api/v2/timezones/",
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

    root.App.Collections.Timezones = Timezones;
})(this);
