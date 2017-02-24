(function(root) {

    "use strict";

    var Views = root.App.Views,
        Models = root.App.Models,
        Collections = root.App.Collections,
        Util = root.App.Util
    ;

    var ClaimShiftsCard = Views.Base.extend({
        el: ".claim-shifts-placeholder",
        events: {
            "click .btn.claim-shift" : "claimShift",
        },
        initialize: function(opts) {
            ClaimShiftsCard.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.scheduleModel)) {
                    this.scheduleModel = opts.scheduleModel;
                }

                if (!_.isUndefined(opts.callback)) {
                    this.callback = opts.callback;
                }

                if (!_.isUndefined(opts.collection)) {
                    var shifts = opts.collection.groupBy(function(model) {
                        var start = model.get('start'),
                            stop = model.get('stop'),
                            key = start.concat(stop)
                        ;

                        model.key = key;

                        return key;
                    });
                    this.shifts = _.mapObject(shifts, function(val, key) {
                        return _.shuffle(val);
                    });
                } else {
                    this.shifts = {};
                }
            }
        },
        render: function(opts) {
            var self = this,
                uniqueShifts = _.chain(self.shifts).values().reduce(function(memo, value) {
                    var first = _.first(value);

                    memo.push(first);

                    return memo;
                }, []).valueOf(),
                data = {
                    shifts: self.createFormattedShifts(uniqueShifts),
                }
            ;

            self.$el.html(ich.claim_shifts_card(data));

            $(function () {
                $('[data-toggle="tooltip"]').tooltip()
            });

            // add event listener for when a model is removed from the collection
            self.collection.on("remove", function(model) {

                // remove the model from the list of claimable shifts
                $(".shift-info#" + model.id).remove();
            });

            return this;
        },
        createFormattedShifts: function(shifts) {
            var self = this,
                dayMoment,
                result = []
            ;

            _.each(shifts, function(shift, index) {

                var startLocalMoment = moment.utc(shift.get("start")).local(),
                    stopLocalMoment = moment.utc(shift.get("stop")).local(),
                    duration = Math.round(
                        (Math.floor((stopLocalMoment - startLocalMoment)/1000/60) / 60) * 100
                    ) / 100
                ;

                result.push({
                    date: startLocalMoment.format("M/D"),
                    dayName: startLocalMoment.format("dddd"),
                    dayNameMobile: startLocalMoment.format("ddd"),
                    length: duration,
                    start: startLocalMoment.format("h:mm a"),
                    startMobile: Util.momentMobileDisplay(startLocalMoment),
                    end: stopLocalMoment.format("hh:mm a"),
                    endMobile: Util.momentMobileDisplay(stopLocalMoment),
                    id: shift.key,
                    description: shift.get('description'),
                });
            });

            return result;
        },
        claimShift: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this,
                $target = $(e.target).closest(".card-element.shift-info"),
                shiftId = $target.attr("data-shift-id"),
                shiftModel = self.shifts[shiftId].shift(),
                $target = $(e.target),
                success = function(model, response, opts) {
                    $.notify({message:"Shift Claimed"},{type:"success"});
                    $target.text("Claimed").removeClass("btn-info").addClass("btn-success");
                    $target.closest(".card-element.shift-info").addClass("claimed unavailable");

                    // add shift to graph
                    self.callback(model);

                    // resync with api - can't show shifts that aren't claimable now
                    self.updateClaimableShifts();
                },
                error = function(model, response, opts) {
                    if (_.isEmpty(self.shifts[shiftId])) {
                        $.notify({message:"This shift has already been claimed"},{type:"danger"});
                        $target.text("Unavailable").removeClass("btn-info").addClass("btn-info");
                        $target.closest(".card-element.shift-info").addClass("unavailable");

                        self.updateClaimableShifts();
                    } else {
                        self.claimShift(e);
                    }
                }
            ;

            $(e.target).addClass("disabled");

            // add upstream models
            shiftModel.addUpstreamModel("locationId", LOCATION_ID);
            shiftModel.addUpstreamModel("roleId", ROLE_ID);

            // make patch request to claim it
            shiftModel.save(
                {user_id: USER_ID},
                {success: success, error: error, patch: true}
            );
        },
        updateClaimableShifts: function() {
            var self = this,
                unclaimedShiftsCollection = new Collections.ScheduleShifts(),
                error = function(coll, response, opts) {
                    $.notify({message:"There was a problem updating the page. Please contact support."},{type:"danger"});
                },
                success,
                $shiftRow,
                $shiftBtn,
                shiftId,
                i
            ;

            // upstream models
            unclaimedShiftsCollection.addUpstreamModel("locationId", LOCATION_ID);
            unclaimedShiftsCollection.addUpstreamModel("roleId", ROLE_ID);
            unclaimedShiftsCollection.addUpstreamModel("scheduleId", self.scheduleModel.get("id"));

            // add params
            unclaimedShiftsCollection.addParam("claimable_by_user", parseInt(USER_ID));

            success = function(coll, response, opts) {

                // strategy: loop through all claimable shifts in self.collection
                // get jquery selector, check if it doesn't have disabled class and
                // if that DOM's shift-id doesn't exist in new collection, disable it
                _.each(self.shifts, function(value, key, object) {
                    shiftId = key;
                    $shiftRow = $(_.findWhere($(".shift-info"), { id: shiftId }));
                    $shiftBtn = $shiftRow.find(".btn.claim-shift");

                    if (!$shiftBtn.hasClass("disabled") &&
                        !unclaimedShiftsCollection.some(function(model) {
                            return shiftId === model.get('start').concat(model.get('stop'));
                        })
                    ){
                        $shiftRow.addClass("unavailable");
                        $shiftBtn.text("Unavailable").addClass("disabled");
                    }
                });

            };

            unclaimedShiftsCollection.fetch({
                success: success,
                error: error,
            });
        },
    });

    root.App.Views.Components.ClaimShiftsCard = ClaimShiftsCard;

})(this);
