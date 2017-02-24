(function(root) {

    "use strict";

    var Views = root.App.Views,
        Collections = root.App.Collections
    ;

    var PreferencesCardView = Views.Base.extend({
        el: ".preferences-placeholder",
        events: {
            "click .save-preferences .btn" : "fakeSave",
            "click .set-preference" : "setPreference",
        },
        initialize: function(opts) {
            PreferencesCardView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.userModel)) {
                    this.userModel = opts.userModel;
                }

                if (!_.isUndefined(opts.organizationModel)) {
                    this.organizationModel = opts.organizationModel;
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

                if (!_.isUndefined(opts.timeOffRequestsCollection)) {
                    this.timeOffRequestsCollection = opts.timeOffRequestsCollection;
                }
            }

            this.timeRange = {
                min: 0,
                max: 23,
            };

            this.blockGroupSize = 6;

            this.ranges = [
                {
                    label: 'Night',
                    subLabel: '12am-6am',
                    start: 0,
                    end: 6,
                },
                {
                    label: 'Morning',
                    subLabel: '6am-12pm',
                    start: 6,
                    end: 12,
                },
                {
                    label: 'Afternoon',
                    subLabel: '12pm-6pm',
                    start: 12,
                    end: 18,
                },
                {
                    label: 'Evening',
                    subLabel: '6pm-12am',
                    start: 18,
                    end: 24,
                },
            ];
        },
        render: function(opts) {
            var self = this,
                disabledRange,
                data = {}
            ;

            self.$el.html(ich.preferences_card(data));

            self.addDelegateView(
                "set-preferences",
                new Views.Components.Timegrid({
                    timegridData: self.generateTimegridData(),
                    timeRange: self.timeRange,
                    dayWeekStarts: self.organizationModel.get('day_week_starts'),
                    dangerMode: false,
                    disabledRange: self.generateDisabledRangeData(),
                    start: self.scheduleModel.get('start'),
                    timezone: self.locationModel.get("timezone"),
                    timegridColumnButton: self.roleModel.get('data').enable_time_off_requests ? {
                        view: Views.Components.TimeOffRequestButtonView,
                        opts: {
                            preferenceModel: self.model,
                            userModel: self.userModel,
                            organizationModel: self.orgModel,
                            scheduleModel: self.scheduleModel,
                            roleModel: self.roleModel,
                            locationModel: self.locationModel,
                            timeOffRequestsCollection: self.timeOffRequestsCollection,
                            savePreferences: self.savePreferences.bind(self),
                        },
                    } : false,
                    mouseUpTouchEndCallback: self.savePreferences.bind(self),
                })
            );

            return this;
        },
        generateDisabledRangeData: function() {
            var self = this;

            if (!self.userModel.get('working_hours')) {
                // logic to handle null working_hours is in the timegrid column
                return self.userModel.get('working_hours');
            }

            return _.mapObject(self.userModel.get('working_hours'), function(value) {
                return _.map(self.ranges, function(range) {
                    return value.slice(range.start, range.end).indexOf(1) != -1 ? 1 : 0;
                });
            });
        },
        generateTimegridData: function() {
            var self = this,
                preferenceData = self.model.get('preference')
            ;

            if (_.isString(preferenceData)) {
                preferenceData = JSON.parse(preferenceData);
            }

            return _.mapObject(preferenceData, function(value) {
                return _.map(self.ranges, function(range) {
                    return {
                        label: range.label,
                        subLabel: range.subLabel,
                        data: value.slice(range.start, range.end).indexOf(1) != -1 ? 1 : 0,
                    };
                });
            });
        },
        convertTimegridData: function(timegridData) {
            var self = this;

            return _.mapObject(timegridData, function(value) {
                return _.reduce(value, function(memo, val) {
                    _.each(_.range(self.blockGroupSize), function() {
                        memo.push(_.isNumber(val) ? val : val.data);
                    });

                    return memo;
                }, []);
            });
        },
        fakeSave: function(e) {
            e.preventDefault();
            e.stopPropagation();

            $.notify({message:"Preferences saved"}, {type:"success"});
        },
        savePreferences: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                timegridData = self.convertTimegridData(self.delegateViews["set-preferences"].getTimegridData()),
                userId = self.userModel.id,
                success,
                error
            ;

            success = function(model, response, opts) {
                self.setChanged(false);

                if (_.isString(self.model.get('preference'))) {
                    self.model.set('preference', JSON.parse(self.model.get('preference')));
                }

                if (self.model.isNew()) {
                    self.model.set('id', userId);
                }
            };

            error = function(model, response, opts) {
                $.notify({message:"Unable to save preferences. Please contact support if the problem persists."},{type: "danger"});
            };

            // update model

            if (self.model.isNew()) {
                self.model.set("preference", JSON.stringify(timegridData));
                self.model.set("user_id", userId);
                self.model.save(
                    {},
                    {
                        success: success,
                        error: error,
                        type: "POST",
                    }
                );
            } else {
                self.model.save(
                    {
                        preference: JSON.stringify(timegridData),
                    }, {
                        success: success,
                        error: error,
                        patch: true,
                    }
                );
            }
        },
        setPreference: function(event) {
            var self = this,
                target = event.target,
                $target = $(target),
                preference = $target.data('preference'),
                preferenceData = self.model.get('preference'),
                disabledRange = self.userModel.get('working_hours'),
                populatePreference
            ;

            if (_.isString(preferenceData)) {
                preferenceData = JSON.parse(preferenceData);
            }

            populatePreference = function(start, end) {
                _.each(preferenceData, function(hours, day) {
                    for (var i = start; i <= end; i++) {
                        if (!!disabledRange && disabledRange[day][i] === 0) {
                            continue;
                        }

                        hours[i] = 1;
                    }
                });

                self.model.save({'preference': JSON.stringify(preferenceData)}, {patch: true});
            };

            switch (preference) {
                case 'mornings':
                    populatePreference(6, 11);
                    break;
                case 'afternoons':
                    populatePreference(12, 17);
                    break;
                case 'evenings':
                    populatePreference(18, 23);
                    break;
                case 'nights':
                    populatePreference(0, 5);
                    break;
            }

            self.render();
        },
        setChanged: function(value) {
            var self = this;
            value = !!value;

            self.delegateViews["set-preferences"].changed = value;
        },
        hasChanged: function() {
            var self = this;

            return self.delegateViews["set-preferences"].changed;
        },
    });

    root.App.Views.Components.PreferencesCardView = PreferencesCardView;
})(this);
