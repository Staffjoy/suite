(function(root) {

    "use strict";

    var Models = root.App.Models,
        Kpis = Models.Base.extend({
            endpoint: "internal/kpis/",
            parse: function(response) {
                return response.data;
            },
        })
    ;

    root.App.Models.Kpis = Kpis;
})(this);
