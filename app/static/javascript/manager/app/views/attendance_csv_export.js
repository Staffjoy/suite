(function(root) {

    "use strict";

    var Views = root.App.Views,
        Models = root.App.Models,
        Collections = root.App.Collections
    ;

    var AttendanceCSVExportView = Views.Base.extend({
        el: ".attendance-csv-placeholder",
        events: {
            "click .btn.view-availability": "viewAvailability",
        },
        initialize: function(opts) {
            AttendanceCSVExportView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.locationId)) {
                    this.locationId = opts.locationId;
                }

                if (!_.isUndefined(opts.locationModel)) {
                    this.locationModel = opts.locationModel;
                }

                if (!_.isUndefined(opts.queryStart)) {
                    this.queryStart = opts.queryStart;
                }

                if (!_.isUndefined(opts.queryStop)) {
                    this.queryStop = opts.queryStop;
                }
            }

            this.displayFormat = "YYYY-MM-DD";
            this.quickDownloadBtn;
            this.startDatetimepicker;
            this.stopDatetimepicker;
        },
        render: function(opts) {
            var self = this;

            self.$el.append(ich.attendance_csv_card());

            self.quickDownloadBtn = $("#quick-csv-download");

            self.$el.on('show.bs.collapse', function (event) {
                var $target = $(event.target),
                    collapseId = $target.data('collapse-id'),
                    selector = '.collapse-btn-attendance-csv'
                ;

                $(selector).find('.glyphicon').removeClass('glyphicon-chevron-down').addClass('glyphicon-chevron-up');
                self.quickDownloadBtn.addClass("hidden");
            });

            self.$el.on('hide.bs.collapse', function (event) {
                var $target = $(event.target),
                    collapseId = $target.data('collapse-id'),
                    selector = '.collapse-btn-attendance-csv'
                ;

                $(selector).find('.glyphicon').removeClass('glyphicon-chevron-up').addClass('glyphicon-chevron-down');
                self.quickDownloadBtn.removeClass("hidden");
            });

            // initialize timepickers
            self.startDatetimepicker = $('#start-datetimepicker-csv').datetimepicker({
                defaultDate: moment(self.queryStart),
                format: self.displayFormat,
            });
            self.stopDatetimepicker = $('#stop-datetimepicker-csv').datetimepicker({
                defaultDate: moment(self.queryStop),
                format: self.displayFormat,
            });

            $(".download-csv-btn").click(function(e) {
                self.download_csv(e);
            });

            return this;
        },
        download_csv: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                start = self.startDatetimepicker.data("date"),
                stop = self.stopDatetimepicker.data("date"),
                csvUrl
            ;

            csvUrl = "/api/v2/organizations/" + ORG_ID + "/locations/" + self.locationId + "/attendance/" + "?startDate=" + start + "&endDate=" + stop + "&csv_export=true";

            window.open(csvUrl);
        },
    });

    root.App.Views.AttendanceCSVExportView = AttendanceCSVExportView;

})(this);
