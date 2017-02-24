(function(root) {

    "use strict";

    var Views = root.App.Views,
        Models = root.App.Models
    ;

    var LocationDashboardShiftsCardView = Views.Base.extend({
        el: ".location-dashboard-shifts-card-placeholder",
        events: {},
        initialize: function(opts) {
            LocationDashboardShiftsCardView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.locationModel)) {
                    this.locationModel = opts.locationModel;
                }

                if (!_.isUndefined(opts.locationShiftsCollection)) {
                    this.locationShiftsCollection = opts.locationShiftsCollection;
                }

                if (!_.isUndefined(opts.locationTimeclocksCollection)) {
                    this.locationTimeclocksCollection = opts.locationTimeclocksCollection;
                }

                if (!_.isUndefined(opts.locationTimeOffRequestsCollection)) {
                    this.locationTimeOffRequestsCollection = opts.locationTimeOffRequestsCollection;
                }

                if (!_.isUndefined(opts.rolesCollection)) {
                    this.rolesCollection = opts.rolesCollection;
                }
            }

            this.State = {
                UNASSIGNED: 0,
                CLOCKED_IN_VERY_EARLY: 1,
                COMING_IN_SOON: 2,
                CLOCKED_IN_EARLY: 3,
                LATE: 4,
                ON_SHIFT: 5,
                ON_BREAK: 6,
                LATE_CLOCK_OUT: 7,
                VERY_LATE_CLOCK_OUT: 8,
                ON_SHIFT_TIMECLOCK_DISABLED: 9,
            };

            this.earlyShiftThreshold = 15;
            this.lateShiftThreshold = 15;
        },
        render: function(opts) {
            var self = this,
                data = {
                    shifts: self.generateTemplateShiftData(),
                }
            ;
            data.unassociatedShifts = self.generateTemplateUnassociatedShiftData(data.shifts),
            data.isEmpty = _.isEmpty(data.shifts) && _.isEmpty(data.unassociatedShifts);

            self.$el.html(ich.location_dashboard_shifts_card(data));

            if (!!self.timeout) {
                clearTimeout(self.timeout);
            }

            $(function () {
                $('[data-toggle="tooltip"]').tooltip()
            })

            self.timeout = setTimeout(self.fetchAndRender.bind(self), 5000);

            return this;
        },
        close: function() {
            clearTimeout(self.timeout);
            LocationDashboardShiftsCardView.__super__.close.call(this);
        },
        fetchAndRender: function() {
            var self = this,
                invokeList = [],
                start = moment().subtract(24, 'hours').utc().format('YYYY-MM-DDTHH:mm:ss'),
                end = moment().add(24, 'hours').utc().format('YYYY-MM-DDTHH:mm:ss'),
                error,
                complete
            ;

            error = function(model, response, opts) {
                $.notify({message:ERROR_MESSAGE},{type:"danger"});
            };

            self.locationShiftsCollection.addParam('start', start);
            self.locationShiftsCollection.addParam('end', end);

            self.locationTimeOffRequestsCollection.addParam('start', start);
            self.locationTimeOffRequestsCollection.addParam('end', end);

            self.locationTimeclocksCollection.addParam('start', start);

            invokeList.push(self.locationShiftsCollection);
            invokeList.push(self.locationTimeclocksCollection);
            invokeList.push(self.locationTimeOffRequestsCollection);

            complete = _.invoke(invokeList, "fetch", {error: error});

            $.when.apply($, complete).done(function() {
                self.render();
            });
        },
        generateTemplateShiftData: function() {
            var self = this;

            return _.map(self.generateShiftData(), function(shift) {
                var data = _.extend({}, shift),
                    timezone = self.locationModel.get("timezone")
                ;

                data.roleId = shift.roleId;
                data.userId = shift.userId;
                data.background = self.generateBackground(shift.state);
                data.icon = self.generateIcon(shift.state);
                data.start = moment.utc(shift.start).tz(timezone).format('HH:mm:ss');
                data.stop = moment.utc(shift.stop).tz(timezone).format('HH:mm:ss');
                data.message = self.generateMessage(shift);
                data.timeclocks = self.generateTimeclocks(shift);
                data.tooltip = self.generateTooltip(shift.state);

                return data;
            });
        },
        generateTemplateUnassociatedShiftData: function(associatedShiftData) {
            var self = this,
                output_shifts = []
            ;


            // Look for open timeclocks that are not accounted for in associated data
            self.locationTimeclocksCollection.each(function(timeclock) {
                if (!!timeclock.get('stop')) {
                  // it's closed
                  return;
                }

                var timeclockUserId = timeclock.get('user_id'),
                    timeclockRoleId = timeclock.get('role_id'),
                    roleModel = self.rolesCollection.get(timeclockRoleId),
                    role = self.rolesCollection.get(timeclockRoleId),
                    users = role.get('users'),
                    user = _.findWhere(users, { id: timeclockUserId }),
                    match = false
                ;

                // See if timeclock is associated
                _.each(associatedShiftData, function(data) {
                    if (data.roleId == timeclockRoleId && timeclockUserId == data.userId) {
                        match = true;
                    }
                });

                if (!match) {
                    // Push to the output
                    output_shifts.push({
                      userId: timeclockUserId,
                      roleId: timeclockRoleId,
                      shiftState: self.State.ON_SHIFT_TIMECLOCK_DISABLED,
                      role: roleModel.get('name'),
                      name: user.name || user.email,
                    });
                }
            });
            return output_shifts;
        },
        generateTimeclocks: function(shift) {
            var self = this,
                timeclocks = self.locationTimeclocksCollection.filter(function(timeclock) {
                    var roleId = timeclock.get('role_id'),
                        userId = timeclock.get('user_id'),
                        start = timeclock.get('start'),
                        stop = timeclock.get('stop')
                    ;

                    if (roleId !== shift.roleId) {
                        return false;
                    }

                    if (userId !== shift.userId) {
                        return false;
                    }

                    if (!stop) {
                        return true;
                    }

                    if (moment.utc(shift.start).isSameOrBefore(moment.utc(stop))
                        && moment.utc(shift.stop).isSameOrAfter(moment.utc(start))
                        ) {

                        return true;
                    }

                    return false;
                }),
                formattedTimeclocks = _.map(timeclocks, function(timeclock) {
                    var start = timeclock.get('start'),
                        stop = timeclock.get('stop'),
                        timezone = self.locationModel.get('timezone')
                    ;

                    return {
                        start: moment.utc(start).tz(timezone).format('HH:mm:ss'),
                        stop: !!stop ? moment.utc(stop).tz(timezone).format('HH:mm:ss') : 'Now',
                    };
                });
            ;


            return formattedTimeclocks;
        },
        generateBackground: function(state) {
            var self = this,
                background
            ;

            switch (state) {
                case self.State.LATE_CLOCK_OUT:
                    background = 'warning';
                    break;
                case self.State.CLOCKED_IN_VERY_EARLY:
                case self.State.LATE:
                case self.State.VERY_LATE_CLOCK_OUT:
                    background = 'danger';
                    break;
                default:
                    background = '';
                    break;
            }

            return background;
        },
        generateIcon: function(state) {
            var self = this,
                icon
            ;

            switch (state) {
                case self.State.CLOCKED_IN_VERY_EARLY:
                case self.State.CLOCKED_IN_EARLY:
                case self.State.ON_SHIFT:
                case self.State.LATE_CLOCK_OUT:
                case self.State.VERY_LATE_CLOCK_OUT:
                    icon = 'fa-check';
                    break;
                case self.State.COMING_IN_SOON:
                    icon = 'fa-circle';
                    break;
                case self.State.LATE:
                    icon = 'fa-times';
                    break;
                case self.State.ON_BREAK:
                    icon = 'fa-pause';
                    break;
                case self.State.ON_SHIFT_TIMECLOCK_DISABLED:
                    icon = 'fa-circle-thin';
                    break;
                default:
                    icon = '';
                    break;
            }

            return icon;
        },
        generateTooltip: function(state) {
            var self = this,
                tooltip
            ;

            switch (state) {
                case self.State.CLOCKED_IN_VERY_EARLY:
                case self.State.CLOCKED_IN_EARLY:
                case self.State.ON_SHIFT:
                case self.State.LATE_CLOCK_OUT:
                case self.State.VERY_LATE_CLOCK_OUT:
                    tooltip = 'Clocked In';
                    break;
                case self.State.ON_SHIFT_TIMECLOCK_DISABLED:
                    tooltip = 'Timeclock disabled';
                    break;
                case self.State.COMING_IN_SOON:
                    tooltip = 'Coming in soon';
                    break;
                case self.State.LATE:
                    tooltip = 'Clocked out';
                    break;
                case self.State.ON_BREAK:
                    tooltip = 'On break';
                    break;
                default:
                    tooltip = '';
                    break;
            }

            return tooltip;
        },
        generateMessage: function(shift) {
            var self = this,
                state
            ;

            switch (shift.state) {
                case self.State.CLOCKED_IN_VERY_EARLY:
                    state = 'Clocked in very early';
                    break;
                case self.State.COMING_IN_SOON:
                    state = 'Starting in ' + moment.utc(shift.start).preciseDiff(moment.utc());
                    break;
                case self.State.CLOCKED_IN_EARLY:
                    state = "Clocked in early";
                    break;
                case self.State.LATE:
                    state = 'Late - ' + moment.utc(shift.start).preciseDiff(moment.utc());
                    break;
                case self.State.ON_BREAK:
                    state = 'On break for ' + self.generateTimeSinceLastClockout(shift);
                    break;
                case self.State.LATE_CLOCK_OUT:
                    state = 'Late clocking out';
                    break;
                case self.State.VERY_LATE_CLOCK_OUT:
                    state = 'Very late clocking out';
                    break;
                default:
                    state = '';
                    break;
            }

            return state;
        },
        generateTimeSinceLastClockout: function(shift) {
            var self = this,
                timeclocks = self.locationTimeclocksCollection.where({ user_id: shift.userId, role_id: shift.roleId }),
                timeclock = _.max(timeclocks, function(timeclock) {
                    return moment(timeclock.get('stop')).unix();
                }),
                stop = moment.utc(timeclock.get('stop')),
                now = moment.utc()
            ;

            return now.preciseDiff(stop);
        },
        generateSortedShifts: function() {
            var self = this,
                timezone = self.locationModel.get("timezone"),
                assignedShifts = self.locationShiftsCollection.filter(function(model) {
                    return model.has('user_id');
                }),
                sortedShifts = [],
                clockedInVeryEarly = [],
                comingInSoon = [],
                clockedInEarly = [],
                late = [],
                onShift = [],
                lateClockOut = [],
                veryLateClockOut = [],
                userRoleTimeclockMap = self.generateUserRoleTimeclockMap(),
                addShifts = function(shifts) {
                    shifts.sort(function(thisShift, thatShift) {
                        var thisStart = moment.utc(thisShift.shiftStart),
                            thisStop = moment.utc(thisShift.shiftStop),
                            thatStart = moment.utc(thatShift.shiftStart),
                            thatStop = moment.utc(thatShift.shiftStop)
                        ;

                        if (thisStart.isBefore(thatStart)) {
                            return -1;
                        }

                        if (thisStart.isAfter(thatStart)) {
                            return 1;
                        }

                        if (thisStop.isBefore(thatStop)) {
                            return -1;
                        }

                        if (thisStop.isAfter(thatStop)) {
                            return 1;
                        }

                        return 0;
                    });

                    _.each(shifts, function(shift) {
                        sortedShifts.push(shift);
                    });
                }
            ;

            _.each(self.generateDeduplicatedShifts(), function(shift) {
                var userId = shift.get('user_id'),
                    roleId = shift.get('role_id'),
                    userRoleTimeclocks = userRoleTimeclockMap[userId] || {},
                    timeclocks = userRoleTimeclocks[roleId] || {},
                    roleModel = self.rolesCollection.get(roleId),
                    shiftState = self.checkShiftState(shift, roleModel, timeclocks),
                    shiftData = {
                        userId: userId,
                        roleId: roleId,
                        userName: self.findUserName(shift),
                        shiftStart: shift.get('start'),
                        shiftStop: shift.get('stop'),
                        timeclocks: _.map(timeclocks, function(timeclock) {
                            return {
                                timeclockStart: timeclock.get('start'),
                                timeclockStop: timeclock.get('stop'),
                            };
                        }),
                        roleName: roleModel.get('name'),
                        shiftState: shiftState,
                    }
                ;

                switch (shiftState) {
                    case self.State.UNASSIGNED:
                        break;
                    case self.State.CLOCKED_IN_VERY_EARLY:
                        clockedInVeryEarly.push(shiftData);
                        break;
                    case self.State.COMING_IN_SOON:
                        comingInSoon.push(shiftData);
                        break;
                    case self.State.CLOCKED_IN_EARLY:
                        clockedInEarly.push(shiftData);
                        break;
                    case self.State.LATE:
                        late.push(shiftData);
                        break;
                    case self.State.ON_SHIFT:
                    case self.State.ON_BREAK:
                case self.State.ON_SHIFT_TIMECLOCK_DISABLED:
                        onShift.push(shiftData);
                        break;
                    case self.State.LATE_CLOCK_OUT:
                        lateClockOut.push(shiftData);
                        break;
                    case self.State.VERY_LATE_CLOCK_OUT:
                        veryLateClockOut.push(shiftData);
                        break;
                }
            });

            addShifts(clockedInVeryEarly);
            addShifts(comingInSoon);
            addShifts(clockedInEarly);
            addShifts(late);
            addShifts(onShift);
            addShifts(lateClockOut);
            addShifts(veryLateClockOut);

            return sortedShifts;
        },
        generateDeduplicatedShifts: function() {
            var self = this,
                deduplicatedShifts = [],
                userRoleShiftMap = self.generateUserRoleShiftMap()
            ;

            _.each(userRoleShiftMap, function(roleShiftMap, userId) {
                _.each(roleShiftMap, function(shifts, roleId) {
                    deduplicatedShifts.push(self.findCurrentShift(shifts));
                });
            });

            return deduplicatedShifts;
        },
        findCurrentShift: function(shifts) {
            var self = this,
                currentShift
            ;

            if (shifts.length === 1) {
                return _.first(shifts);
            }

            currentShift = _.find(shifts, function(shift) {
                var start = moment.utc(shift.get('start')),
                    stop = moment.utc(shift.get('stop')),
                    now = moment.utc()
                ;

                if (now.isSameOrAfter(start)
                    && now.isSameOrBefore(stop)) {

                    return true;
                }
            });

            if (!!currentShift) {
                return currentShift;
            }

            currentShift = _.min(shifts, function(shift) {
                var start = moment.utc(shift.get('start')),
                    stop = moment.utc(shift.get('stop')),
                    now = moment.utc(),
                    thisDiff = Math.abs(now.diff(start)),
                    thatDiff = Math.abs(now.diff(stop))
                ;

                if (thisDiff < thatDiff) {
                    return thisDiff;
                }

                return thatDiff;
            });

            return currentShift;
        },
        findUserName: function(shift) {
            var self = this,
                userId = shift.get('user_id'),
                roleId = shift.get('role_id'),
                role = self.rolesCollection.get(roleId),
                users = role.get('users'),
                user = _.findWhere(users, { id: userId })
            ;

            if (_.isUndefined(user)) {
                return '';
            }

            return user.name || user.email;
        },
        generateShiftData: function() {
            var self = this;

            return _.map(self.generateSortedShifts(), function(shiftData) {
                var roleModel = self.rolesCollection.get(shiftData.roleId),
                    users = roleModel.get('users'),
                    user = _.findWhere(users, { id: shiftData.userId })
                ;

                return {
                    userId: shiftData.userId,
                    name: user.name || user.email,
                    start: shiftData.shiftStart,
                    stop: shiftData.shiftStop,
                    role: roleModel.get('name'),
                    roleId: shiftData.roleId,
                    userId: shiftData.userId,
                    state: shiftData.shiftState,
                };
            });
        },
        generateUserRoleTimeclockMap: function() {
            var self = this;

            return self.locationTimeclocksCollection.reduce(function(memo, model) {
                var userId = model.get('user_id'),
                    roleId = model.get('role_id')
                ;

                if (!!memo[userId]) {
                    if(!!memo[userId][roleId]) {
                        memo[userId][roleId].push(model);
                    } else {
                        memo[userId][roleId] = [model];
                    }
                } else {
                    memo[userId] = {};
                    memo[userId][roleId] = [model];
                }

                return memo;
            }, {});
        },
        generateUserRoleShiftMap: function() {
            var self = this;

            return self.locationShiftsCollection.reduce(function(memo, model) {
                var userId = model.get('user_id'),
                    roleId = model.get('role_id')
                ;

                if (!!memo[userId]) {
                    if(!!memo[userId][roleId]) {
                        memo[userId][roleId].push(model);
                    } else {
                        memo[userId][roleId] = [model];
                    }
                } else {
                    memo[userId] = {};
                    memo[userId][roleId] = [model];
                }

                return memo;
            }, {});
        },
        checkShiftState: function(shift, roleModel, timeclocks) {
            var self = this,
                now = moment.utc(),
                shiftStart = moment.utc(shift.get('start')),
                shiftStop = moment.utc(shift.get('stop')),
                earlyShiftCutoff = moment.utc(shiftStart).subtract(self.earlyShiftThreshold, 'minutes'),
                lateShiftCutoff = moment.utc(shiftStop).add(self.lateShiftThreshold, 'minutes'),
                isClockedIn = _.some(timeclocks, function(timeclock) {
                    var timeclockStart = timeclock.get('start'),
                        timeclockStop = timeclock.get('stop')
                    ;

                    return !!timeclockStart && !timeclockStop;
                }),
                hasClockedIn = isClockedIn || _.some(timeclocks, function(timeclock) {
                    return moment.utc(timeclock.get('stop')).isSameOrAfter(shiftStart);
                })
            ;

            if (!shift.get('user_id')) {
                return self.State.UNASSIGNED;
            }

            if (!roleModel.get('enable_timeclock')) {
                if (now.isSameOrAfter(earlyShiftCutoff)
                    && now.isSameOrBefore(shiftStart)) {

                    return self.State.COMING_IN_SOON;
                }

                if (now.isSameOrAfter(shiftStart)
                    && now.isSameOrBefore(shiftStop)) {

                    return self.State.ON_SHIFT_TIMECLOCK_DISABLED;
                }

                return false;
            }

            if (isClockedIn
                && now.isSameOrBefore(earlyShiftCutoff)) {
                // It's already matched to a shift
                return self.State.CLOCKED_IN_VERY_EARLY;
            }

            if (!isClockedIn
                && now.isSameOrAfter(earlyShiftCutoff)
                && now.isSameOrBefore(shiftStart)) {

                return self.State.COMING_IN_SOON;
            }

            if (isClockedIn
                && now.isSameOrAfter(earlyShiftCutoff)
                && now.isSameOrBefore(shiftStart)) {

                return self.State.CLOCKED_IN_EARLY;
            }

            if (!hasClockedIn
                && now.isSameOrAfter(shiftStart)
                && now.isSameOrBefore(shiftStop)) {

                return self.State.LATE;
            }

            if (isClockedIn
                && now.isSameOrAfter(shiftStart)
                && now.isSameOrBefore(shiftStop)) {

                return self.State.ON_SHIFT;
            }

            if (!isClockedIn
                && hasClockedIn
                && now.isSameOrAfter(shiftStart)
                && now.isSameOrBefore(shiftStop)) {

                return self.State.ON_BREAK;
            }

            if (isClockedIn
                && now.isSameOrAfter(shiftStop)
                && now.isSameOrBefore(lateShiftCutoff)) {

                return self.State.LATE_CLOCK_OUT;
            }

            if (isClockedIn
                && now.isSameOrAfter(lateShiftCutoff)) {
                return self.State.VERY_LATE_CLOCK_OUT;
            }

            return false;
        },
    });

    root.App.Views.LocationDashboardShiftsCardView = LocationDashboardShiftsCardView;

})(this);
