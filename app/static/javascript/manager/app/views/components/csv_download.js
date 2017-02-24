(function(root) {

    "use strict";

    var Collections = root.App.Collections,
        Models = root.App.Models,
        Views = root.App.Views,
        Util = root.App.Util
    ;

    var CSVDownloadView = Views.Base.extend({
        el: ".csv-download-placeholder",
        events: {},
        initialize: function(opts) {
            CSVDownloadView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.data)) {
                    this.data = opts.data;
                }
            }
        },
        render: function(opts) {
            var self = this;

            self.$el.html(ich.csv_schedule_download(self.data));

            return this;
        },
    });

    root.App.Views.Components.CSVDownloadView = CSVDownloadView;

})(this);
