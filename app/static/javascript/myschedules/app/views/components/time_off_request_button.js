(function(root) {

    "use strict";

    var Views = root.App.Views,
        Models = root.App.Models
    ;

    var TimeOffRequestButtonView = Views.Base.extend({
        events: {
            'click .request-time-off': 'requestTimeOff',
            'click .cancel-time-off-request': 'cancelTimeOffRequest',
            'touchend .request-time-off': 'requestTimeOff',
            'touchend .cancel-time-off-request': 'cancelTimeOffRequest',
        },
        initialize: function(opts) {
            var date;

            TimeOffRequestButtonView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.preferenceModel)) {
                    this.preferenceModel = opts.preferenceModel;
                }

                if (!_.isUndefined(opts.userModel)) {
                    this.userModel = opts.userModel;
                }

                if (!_.isUndefined(opts.orgModel)) {
                    this.orgModel = opts.orgModel;
                }

                if (!_.isUndefined(opts.scheduleModel)) {
                    this.scheduleModel = opts.scheduleModel;
                }

                if (!_.isUndefined(opts.locationModel)) {
                    this.locationModel = opts.locationModel;
                }

                if (!_.isUndefined(opts.roleModel)) {
                    this.roleModel = opts.roleModel;
                }

                if (!_.isUndefined(opts.timegridColumn)) {
                    this.timegridColumn = opts.timegridColumn;
                }

                if (!_.isUndefined(opts.timeOffRequestsCollection)) {
                    this.timeOffRequestsCollection = opts.timeOffRequestsCollection;
                }

                if (!_.isUndefined(opts.savePreferences)) {
                    this.savePreferences = opts.savePreferences;
                }

                if (!_.isUndefined(opts.date)) {
                    this.date = opts.date;
                    date = this.date;
                }

                this.initModel();
            }
        },
        initModel: function() {
            var self = this;

            self.model = self.timeOffRequestsCollection.find(
                function(model) {
                    return model.get('start').startsWith(self.date);
                }
            ) || new Models.TimeOffRequest({
                start: self.date,
            });

            self.model.addUpstreamModel('locationId', self.locationModel.id);
            self.model.addUpstreamModel('roleId', self.roleModel.id);
            self.model.addUpstreamModel('userId', self.userModel.id);
        },
        render: function() {
            var self = this,
                data = {},
                state = self.model.get('state')
            ;

            if (self.model.isNew()) {
                data.new = true;
            } else {
                if (!state) {
                    data.pending = true;
                } else if (state === 'approved_paid' || state === 'approved_unpaid' || state === 'sick') {
                    data.approved = true;
                } else if (state === 'denied') {
                    data.denied = true;
                }
            }

            if (data.pending || data.approved) {
                self.timegridColumn.disable();
            }

            self.$el.html(ich.time_off_request_button(data));

            return this;
        },
        requestTimeOff: function(event) {
            var self = this;

            self.model.createRequest();
            self.model.save({
                date: self.date
            }, {
                success: function(model) {
                    self.timegridColumn.disable();
                    self.savePreferences(event);
                    self.render();
                },
                error: function() {
                    $.notify({message:"There was a problem making your time off request. Please contact support."},{type:"danger"});
                },
            });
        },
        cancelTimeOffRequest: function(event) {
            var self = this;

            self.model.destroy({
                success: function(model) {
                    self.initModel();
                    self.timegridColumn.enable();
                    self.render();
                },
                error: function() {
                    $.notify({message:"There was a problem cancelling your time off request. Please contact support."},{type:"danger"});
                },
            });
        },
    });

    root.App.Views.Components.TimeOffRequestButtonView = TimeOffRequestButtonView;
})(this);
