(function(root) {

    "use strict";

    var Views = root.App.Views,
        Models = root.App.Models,
        Util = root.App.Util
    ;

    var SchedulingWizardView = Views.Base.extend({
        el: ".wizard-placeholder",
        initialize: function(opts) {
            SchedulingWizardView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.roleName)) {
                    this.roleName = opts.roleName;
                }

                if (!_.isUndefined(opts.roleId)) {
                    this.roleId = opts.roleId;
                }

                if (!_.isUndefined(opts.orgModel)) {
                    this.orgModel = opts.orgModel;
                }

                if (!_.isUndefined(opts.showDemandCallback)) {
                    this.showDemandCallback = opts.showDemandCallback;
                }

                if (!_.isUndefined(opts.showShiftsCallback)) {
                    this.showShiftsCallback = opts.showShiftsCallback;
                }

                if (!_.isUndefined(opts.renderHeaderAction)) {
                    this.renderHeaderAction = opts.renderHeaderAction;
                }
            }
        },
        render: function(opts) {
            var self = this,
                state = self.model.get('state'),
                start = moment.utc(self.model.get('start')),
                daysBeforeStart = self.orgModel.get('shifts_assigned_days_before_start'),
                momentBeforeStart = start.subtract(daysBeforeStart, 'days'),
                now = moment.utc(),
                timeUntilAssignment = momentBeforeStart.preciseDiff(now, false, true, true),
                data = {
                    roleId: self.roleId,
                    roleName: self.roleName,
                    isFlex: self.orgModel.isFlex(),
                    isBoss: self.orgModel.isBoss(),
                    timeUntilAssignment: timeUntilAssignment,
                    chomped: self.model.has('chomp_end'),
                },
                success,
                error
            ;

            if (state === 'initial') {
                self.$el.append(ich.scheduling_wizard_initial_view(data));
            } else if (state === 'unpublished') {
                data.stateUnpublished = true;
                self.$el.append(ich.scheduling_wizard_unpublished_view(data));
            }

            self.addEvents();

            self.$wizard = self.$el.find('#wizard-' + self.roleId);

            return this;
        },
        close: function() {
            $("#wizard-" + self.roleId + " .wizard-button").off();
            SchedulingWizardView.__super__.close.call(this);
        },
        addEvents: function() {
            var self = this;

            $("#wizard-" + self.roleId + " .wizard-button").off();
            $("#wizard-" + self.roleId + " .wizard-button").on("click", function(e) {
                switch($(e.target).data('action')) {
                    case 'chomp':
                        self.chompButtonClicked(e);
                        break;
                    case 'manual':
                        self.manualButtonClicked(e);
                        break;
                    case 'publish':
                        self.publishButtonClicked(e);
                        break;
                    case 'mobius-modal':
                        self.mobiusModalClicked(e);
                        break;
                }
            });

            $("#wizardModal-" + self.roleId + " .wizard-modal-button").on("click", function(e) {
                switch($(e.target).data("action")) {
                    case "mobius-confirm":
                        self.mobiusModalConfirmed(e);
                        break;
                }

                self.renderHeaderAction();
            });
        },
        chompButtonClicked: function(event) {
            var self = this,
                state = self.model.get('state'),
                start = moment(self.model.get('start')),
                daysBeforeStart = self.orgModel.get('shifts_assigned_days_before_start'),
                momentBeforeStart = start.subtract(daysBeforeStart, 'days'),
                now = moment.utc(),
                timeUntilAssignment = momentBeforeStart.isBefore(now) ? 'soon' : 'in ' + momentBeforeStart.preciseDiff(now, false, true, true),
                data = {
                    roleId: self.roleId,
                    roleName: self.roleName,
                    isFlex: self.orgModel.isFlex(),
                    isBoss: self.orgModel.isBoss(),
                    timeUntilAssignment: timeUntilAssignment,
                    chomped: self.model.has('chomp_end'),
                },
                success,
                error
            ;

            success = function(model) {
                // // the demand attr needs to be JSON for request, but an object in model
                self.model.set("demand", JSON.parse(model.get("demand")));

                data.stateUnpublished = true;
                self.$wizard.hide();
                self.$wizard.html(ich.scheduling_wizard_unpublished_view(data));
                self.addEvents();
                self.showDemandCallback();
            };

            error = function(model) {
                $.notify({message: ERROR_MESSAGE},{type: "danger"});

                // the demand attr needs to be JSON for request, but an object in model
                self.model.set("demand", JSON.parse(model.get("demand")));
            };

            if (state === 'unpublished') {
                self.model.save({
                        demand: JSON.stringify(Util.generateFullDayAvailability(0)),
                    },
                    {success: success, error: error, patch: true}
                );
            } else {
                self.model.save({
                        demand: JSON.stringify(Util.generateFullDayAvailability(0)),
                        state: 'unpublished',
                    },
                    {success: success, error: error, patch: true}
                );
            }

        },
        manualButtonClicked: function(event) {
            var self = this,
                state = self.model.get('state'),
                start = moment(self.model.get('start')),
                daysBeforeStart = self.orgModel.get('shifts_assigned_days_before_start'),
                momentBeforeStart = start.subtract(daysBeforeStart, 'days'),
                now = moment.utc(),
                timeUntilAssignment = momentBeforeStart.preciseDiff(now, false, true, true),
                data = {
                    roleId: self.roleId,
                    roleName: self.roleName,
                    isFlex: self.orgModel.isFlex(),
                    isBoss: self.orgModel.isBoss(),
                    timeUntilAssignment: timeUntilAssignment,
                    chomped: self.model.has('chomp_end'),
                },
                success,
                error
            ;

            success = function(model) {
                // the demand attr needs to be JSON for request, but an object in model
                if (_.isString(model.get("demand"))) {
                    model.set("demand", JSON.parse(model.get("demand")));
                }

                data.stateUnpublished = true;
                self.$wizard.html(ich.scheduling_wizard_unpublished_view(data));
                self.addEvents();
                self.showShiftsCallback();
            };

            error = function(model) {
                $.notify({message: ERROR_MESSAGE},{type: "danger"});

                // the demand attr needs to be JSON for request, but an object in model
                if (_.isString(model.get("demand"))) {
                    model.set("demand", JSON.parse(model.get("demand")));
                }
            };

            self.model.save({
                    state: 'unpublished',
                },
                {success: success, error: error, patch: true}
            );
        },
        publishButtonClicked: function(event) {
            var self = this,
                success,
                error
            ;

            success = function(model) {
                $.notify({message:"Shifts have been published and workers have been notified."}, {type:"success"});

                // the demand attr needs to be JSON for request, but an object in model
                if (_.isString(model.get("demand"))) {
                    model.set("demand", JSON.parse(model.get("demand")));
                }

                self.hide();
            };

            error = function(model) {
                $.notify({message: ERROR_MESSAGE},{type: "danger"});

                // the demand attr needs to be JSON for request, but an object in model
                if (_.isString(model.get("demand"))) {
                    model.set("demand", JSON.parse(model.get("demand")));
                }
            };

            self.model.save({
                    state: 'published',
                },
                {success: success, error: error, patch: true}
            );
        },
        mobiusModalConfirmed: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                success,
                error
            ;

            success = function(model) {
                $.notify({message:"Schedule processing started"}, {type:"success"});

                // the demand attr needs to be JSON for request, but an object in model
                if (_.isString(model.get("demand"))) {
                    model.set("demand", JSON.parse(model.get("demand")));
                }

                $(".scheduling-messages").append(ich.scheduling_message({
                    info: true,
                    message: "The schedule for " + self.roleName + " is being processed. You will receive an email when processing is complete.",
                }));

                $("#wizardModal-" + self.roleId).modal("hide");
                self.hide();
            };

            error = function(model) {
                $.notify({message: ERROR_MESSAGE},{type: "danger"});

                // the demand attr needs to be JSON for request, but an object in model
                if (_.isString(model.get("demand"))) {
                    model.set("demand", JSON.parse(model.get("demand")));
                }
            };

            self.model.save({
                    state: 'mobius-queue',
                },
                {success: success, error: error, patch: true}
            );
        },
        mobiusModalClicked: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this;

            $("#wizardModal-" + self.roleId).modal();
        },
        hide: function() {
            this.$wizard.hide();
        },
        show: function() {
            this.$wizard.show();
        },
    });

    root.App.Views.SchedulingWizardView = SchedulingWizardView;

})(this);
