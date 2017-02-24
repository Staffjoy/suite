(function(root) {

    "use strict";

    var Views = root.App.Views;

    var MessagesView = Views.Base.extend({
        el: ".messages-header",
        initialize: function(opts) {
            MessagesView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.rootModel)) {
                    this.rootModel = opts.rootModel;
                }
            }
        },
        render: function() {
            var self = this,
                data = {},
                paidUntil = self.model.get('data').paid_until,
                now = moment.utc(),
                trialDays = self.model.get('data').trial_days,
                createdAt = moment.utc(self.model.get('data').created_at),
                trialUntil = createdAt.add(trialDays + 1, 'days')
            ;

            if (!paidUntil || moment.utc(paidUntil).isBefore(now)) {
                if (trialUntil.isAfter(now)) {
                    var trialDaysRemaining = trialUntil.diff(now, 'days');

                    if (trialDaysRemaining <= 1) {
                        data.message = "There is less than one day remaining in your trial.";
                    } else {
                        data.message = "There are " + trialDaysRemaining + " days remaining in your trial.";
                    }
                    data.klass = "inactive"

                    if (self.rootModel.isOrgAdmin()) {
                        data.message += " Click here to set up billing.";
                        data.url = "/billing/organizations/" + ORG_ID;
                    }
                } else {
                    data.message = "Your trial has expired.";
                    data.klass = "warning";

                    if (self.rootModel.isOrgAdmin()) {
                        data.message += " Click here to set up billing.";
                        data.url = "/billing/organizations/" + ORG_ID;
                    }
                }
            } else if (!self.model.get('data').active) {
                data.message = "Scheduling is deactivated for your organization.";
                data.klass = "warning org-inactive";

                if (self.rootModel.isOrgAdmin()) {
                    data.url = "#settings";
                }
            }

            self.$el.html(ich.message(data));

            return this;
        },
        refresh: function() {
            var self = this;
            self.model.fetch({async:false});
            self.render();
        },
    });

    root.App.Views.Components.MessagesView = MessagesView;
})(this);
