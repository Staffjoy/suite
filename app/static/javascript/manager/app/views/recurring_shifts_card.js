(function(root) {

    "use strict";

    var Views = root.App.Views,
        Models = root.App.Models,
        Util = root.App.Util
    ;

    var RecurringShiftsCardView = Views.Base.extend({
        el: ".recurring-shifts-placeholder",
        events: {
            'click .recurring-shift-edit': 'editShift',
        },
        initialize: function(opts) {
            RecurringShiftsCardView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.userModel)) {
                    this.userModel = opts.userModel;
                }

                if (!_.isUndefined(opts.recurringShiftsCollection)) {
                    this.recurringShiftsCollection = opts.recurringShiftsCollection;
                }

                if (!_.isUndefined(opts.roleModel)) {
                    this.roleModel = opts.roleModel;
                }

                if (!_.isUndefined(opts.userRolesCollection)) {
                    this.userRolesCollection = opts.userRolesCollection;
                }

                if (!_.isUndefined(opts.orgModel)) {
                    this.orgModel = opts.orgModel;
                }

                if (!_.isUndefined(opts.showDescription)) {
                    this.showDescription = opts.showDescription;
                }
            }
        },
        render: function(opts) {
            var self = this,
                data = {
                    user: !!self.userModel,
                    isEmpty: self.recurringShiftsCollection.isEmpty(),
                    shifts: self.recurringShiftsCollection.map(function(model) {
                        var data = {
                            dayOfWeek: Util.capitalize(model.get('start_day')),
                            start: self.formatStart(model),
                            duration: self.formatDuration(model),
                            worker: self.generateName(model),
                            quantity: model.get('quantity'),
                            id: model.id,
                        };

                        return data;
                    }),
                    showDescription: self.showDescription,
                    showTotalRow: self.recurringShiftsCollection.models.length > 1,
                    durationTotal: self.calculateTotalDuration(),
                }
            ;

            self.$el.html(ich.recurring_shifts_card(data));

            return this;
        },
        formatStart: function(recurringShiftsModel) {
            return moment.utc(0).add(recurringShiftsModel.get('start_hour'), 'hours').add(recurringShiftsModel.get('start_minute'), 'minutes').format('h:mm A');
        },
        formatDuration: function(recurringShiftsModel) {
            return moment.utc(0).preciseDiff(moment.utc(0).add(recurringShiftsModel.get('duration_minutes'), 'minutes'));
        },
        calculateTotalDuration: function() {
            var self = this;

            return moment.utc(0).preciseDiff(moment.utc(0).add(self.recurringShiftsCollection.reduce(function(memo, model) {
                return memo += model.get('duration_minutes');
            }, 0), 'minutes'));
        },
        generateName: function(recurringShiftModel) {
            var self = this,
                userId = recurringShiftModel.get('user_id'),
                userModel,
                name
            ;


            if (userId === 0) {
                return;
            }

            if (_.isUndefined(self.userRolesCollection)) {
                return;
            }

            userModel = self.userRolesCollection.get(userId);
            name = userModel.get('name');

            if (!!name) {
                return name;
            }

            return userModel.get('email');
        },
        editShift: function(event) {
            event.stopPropagation();
            event.preventDefault();

            var self = this,
                $target = $(event.target),
                id = $target.data('id'),
                opts = {
                    userRolesCollection: self.userRolesCollection,
                    recurringShiftModel: self.findRecurringShiftModel(id),
                    edit: id !== 'recurringShiftCreate',
                    userModel: self.findUserModel(id),
                    orgModel: self.orgModel,
                    callback: function() {
                        self.recurringShiftsCollection.fetch({
                            success: self.render.bind(self),
                        });
                    },
                    recurringShiftsCollection: self.recurringShiftsCollection,
                },
                modal = new Views.Components.RecurringShiftsModalView(opts)
            ;

            self.addDelegateView(
                'recurring-shifts-modal',
                modal
            );
        },
        findUserModel: function(shiftId) {
            var self = this,
                shift = self.recurringShiftsCollection.get(shiftId),
                userId = !!shift ? shift.get('user_id') : 0
            ;

            if (!!self.userModel) {
                return self.userModel;
            }

            if (userId !== 0) {
                return self.userRolesCollection.get(shift.get('user_id'));
            }

            return false;
        },
        findRecurringShiftModel: function(id) {
            var self = this,
                model
            ;

            if (id === 'recurringShiftCreate') {
                return false;
            }

            model = self.recurringShiftsCollection.get(id);
            model.addUpstreamModel('locationId', self.recurringShiftsCollection.getUpstreamModelId('locationId'));
            model.addUpstreamModel('roleId', self.recurringShiftsCollection.getUpstreamModelId('roleId'));

            return model;
        },
    });

    root.App.Views.RecurringShiftsCardView = RecurringShiftsCardView;

})(this);
