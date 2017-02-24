(function(root) {

    "use strict";

    var Views = root.App.Views,
        Models = root.App.Models,
        Collections = root.App.Collections
    ;

    var OrganizationSettingsView = Views.Base.extend({
        el: "#manage-main",
        events: {
            "click .org-properties span.card-element-active": "editProperty",

            "click .danger-zone .btn": "editActive",
        },
        initialize: function(opts) {
            OrganizationSettingsView.__super__.initialize.apply(this);
            this.topNavVisible = "settings";

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.adminsCollection)) {
                    this.adminsCollection = opts.adminsCollection;
                }

                if (!_.isUndefined(opts.locationsCollection)) {
                    this.locationsCollection = opts.locationsCollection;
                }

                if (!_.isUndefined(opts.plansCollection)) {
                    this.plansCollection = opts.plansCollection;
                }

                if (!_.isUndefined(opts.rootModel)) {
                    this.rootModel = opts.rootModel;
                }
            }
        },
        render: function(opts) {
            var self = this,
                adminsCollection = new Collections.Admins(),
                data = _.extend({}, self.model.toJSON(), opts),
                admins = self.adminsCollection.models[0].get("data"),
                defaultTimeclock = self.model.get("enable_timeclock_default"),
                defaultTimeOffRequest = self.model.get("enable_time_off_requests_default"),
                plan = self.model.get("plan"),
                currentPlan = self.plansCollection.get(plan),
                schedulingPreferencesTitle
            ;

            data["planName"] = currentPlan.get("name");

            // repackage adminsCollection without data child
            _.each(admins, function(admin, index, list) {
                var adminModel = new Models.Admin(admin);

                adminsCollection.add(adminModel);
            });

            self.$el.html(ich.organization_settings(data));

            // create org schedule preference card for boss package
            if (self.model.isBoss()) {
                self.addDelegateView(
                    "org-scheduling-preferences",
                    new Views.SchedulingPreferencesCardView({
                        el: "div.organization-scheduling-preferences",
                        model: self.model,
                        roleId: self.roleId,
                        locationId: self.locationId,
                        template: "org-preferences",
                        strings: {
                            title: "Organization Scheduling Settings",
                        },
                    })
                );

                self.addDelegateView(
                    "time-off-request-preferences",
                    new Views.TimeOffRequestPreferencesCardView({
                        collection: self.locationsCollection,
                        defaultTimeOffRequest: defaultTimeOffRequest,
                    })
                );
            }

            self.addDelegateView(
                "timeclock-preferences",
                new Views.TimeclockPreferencesCardView({
                    collection: self.locationsCollection,
                    defaultTimeclock: defaultTimeclock,
                })
            );

            // add delegate admin view
            self.addDelegateView(
                "org-admin-card",
                new Views.AdminsCardView({
                    collection: adminsCollection,
                    orgModel: self.model,
                    locationId: self.locationId,
                })
            );

            self.addDelegateView(
                "location-manager-card",
                new Views.LocationManagersOrganizationCardView({
                    locationsCollection: self.locationsCollection,
                    locationManagerData: self.locationsCollection.reduce(function(memo, location) {
                        _.each(location.get('managers'), function(manager) {
                            if (!_.has(memo, manager.id)) {
                                memo[manager.id] = manager;
                            }

                            if (!_.has(memo[manager.id], 'locations')) {
                                memo[manager.id].locations = {};
                            }

                            memo[manager.id].locations[location.id] = undefined;
                        });

                        return memo;
                    }, {})
                })
            );

            this.$el.on('show.bs.collapse', function (event) {
                var $target = $(event.target),
                    collapseId = $target.data('collapse-id'),
                    selector = '.collapse-btn-' + collapseId
                ;

                $(selector).find('.glyphicon').removeClass('glyphicon-chevron-down').addClass('glyphicon-chevron-up');
            });

            this.$el.on('hide.bs.collapse', function (event) {
                var $target = $(event.target),
                    collapseId = $target.data('collapse-id'),
                    selector = '.collapse-btn-' + collapseId
                ;

                $(selector).find('.glyphicon').removeClass('glyphicon-chevron-up').addClass('glyphicon-chevron-down');
            });

            return this;
        },
        editProperty: function(e) {
            var self = this,
                $target = $(e.target).closest(".card-element-active"),
                param = $target.attr("data-param")
            ;
            e.preventDefault();
            e.stopPropagation();

            Backbone.history.navigate("/settings/" + param, {trigger: true});
        },
        editActive: function(e) {
            e.preventDefault();
            e.stopPropagation();
            Backbone.history.navigate("/settings/active", {trigger: true});
        },
        getAction: function() {
            var self = this;

            return {
                label: 'Admin',
                callback: function() {
                    self.addDelegateView(
                        "add-admin-modal",
                        new Views.Components.AddAdminModalView({
                            adminCardView: self.delegateViews["org-admin-card"],
                        })
                    );
                },
            };
        },
    });

    root.App.Views.OrganizationSettingsView = OrganizationSettingsView;

})(this);
