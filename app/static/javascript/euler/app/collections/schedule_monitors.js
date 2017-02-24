(function(root) {

    "use strict";

    var Models = root.App.Models,
        Collections = root.App.Collections,
        ScheduleMonitors = Collections.Base.extend({
            model: Models.Base,
            endpoint: "internal/schedulemonitoring/",
            parse: function(response) {
                return response.data;
            },
        })
    ;

    root.App.Collections.ScheduleMonitors = ScheduleMonitors;
})(this);
