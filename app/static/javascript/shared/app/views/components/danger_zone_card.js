(function(root) {

    "use strict";

    var Views = root.App.Views;

    var DangerZoneCard = Views.Base.extend({
        el: ".danger-zone-placeholder",
        events: {
            "click .danger-zone-btn": "dangerZoneButtonClicked",
        },
        initialize: function(opts) {
            DangerZoneCard.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.description)) {
                    this.description = opts.description;
                }

                if (!_.isUndefined(opts.buttonLabel)) {
                    this.buttonLabel = opts.buttonLabel;
                }

                if (!_.isUndefined(opts.dangerZoneCallback)) {
                    this.dangerZoneCallback = opts.dangerZoneCallback;
                }

                if (!_.isUndefined(opts.confirmationMessage)) {
                    this.confirmationMessage = opts.confirmationMessage;
                }
            }
        },
        render: function() {
            var self = this,
                data = {
                    description: self.description,
                    buttonLabel: self.buttonLabel,
                    confirmationMessage: self.confirmationMessage,
                }
            ;

            self.$el.html(ich.danger_zone(data));

            return this;
        },
        dangerZoneButtonClicked: function(event) {
            var self = this;

            if (self.dangerZoneCallback) {
                self.dangerZoneCallback(event);
                $('body').css('overflow', 'visible');
            }
        },
    });

    root.App.Views.DangerZoneCard = DangerZoneCard;

})(this);
