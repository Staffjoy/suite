(function(root) {

    "use strict";

    var Timezone = Backbone.Model.extend({
        urlRoot: "/api/v2/timezones/",
        credentials: function() {
            return {
                username: API_KEY,
                password: "",
            };
        },
    });

    root.App.Models.Timezone = Timezone;
})(this);
