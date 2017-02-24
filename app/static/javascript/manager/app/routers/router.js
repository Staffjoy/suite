(function(root) {

    "use strict";

    var Util = root.App.Util,
        Views = root.App.Views,
        Models = root.App.Models,
        Collections = root.App.Collections
    ;

    var Router = Backbone.Router.extend({
        initialize: function(options) {
            this.appView = options.appView;

            var self = this,
                orgModel = new Models.Organization(),
                rootModel = new Models.Root(),
                locationsCollection = new Collections.Locations(),
                messagesView = new Views.Components.MessagesView({
                    model: orgModel,
                    rootModel: rootModel,
                }),
                headerView,
                error,
                complete
            ;

            error = function(collection, response, opts) {
                $.notify({message:ERROR_MESSAGE},{type:"danger"});
            };

            locationsCollection.addParam('archived', false);

            complete = _.invoke([orgModel, rootModel, locationsCollection], "fetch", {error: error});

            headerView = new Views.Components.HeaderView({
                model: orgModel,
                rootModel: rootModel,
                collection: locationsCollection,
                loaded: complete,
            }),
            self.appView.registerView(headerView);

            // get the roles and then carry that into the fetches for schedules
            $.when.apply($, complete).done(function() {
                var data = _.first(locationsCollection.models);

                locationsCollection.remove(data);
                locationsCollection.add(data.get('data'));

                messagesView.render();
                headerView.render();
            });

            // Make these accessible elsewhere
            self.headerView = headerView;
            self.messagesView = messagesView;
            self.complete = complete;
        },
        routes: {
            "locations" : "locations",
            "locations/:id" : "location_dashboard",
            "locations/:id/scheduling" : "location_scheduling",
            "locations/:id/scheduling/:date" : "location_scheduling",
            "locations/:id/calendar" : "location_scheduling",               // legacy route - keep until 2016-03-15
            "locations/:id/calendar/:date" : "location_scheduling",         // legacy route - keep until 2016-03-15
            "locations/:id/attendance" : "location_attendance",
            "locations/:id/attendance/:date" : "location_attendance",
            "locations/:id/preferences" : "location_preferences",
            "locations/:id/preferences/:params" : "location_preferences_edit",
            "locations/:id/roles" : "location_roles",
            "locations/:id/roles/:id/preferences" : "location_role_preferences",
            "locations/:id/roles/:id/preferences/add-worker" : "add_worker",
            "locations/:id/roles/:id/preferences/:params" : "location_role_preferences_edit",
            "locations/:id/roles/:id/users/:id" : "location_role_user",
            "locations/:id/roles/:id/users/:id/preferences/:param" : "location_role_user_preferences_edit",
            "locations/:id/new-role" : "new_role",
            "new-location" : "new_location",
            "settings" : "organization_settings",
            "settings/:params" : "organization_settings_edit",
            "home" : "locations",
            "*action" : "locations",
        },
        locations: function() {
            var self = this,
                error,
                rootModel = new Models.Root(),
                locationsCollection = new Collections.Locations(),
                locationsView = new Views.LocationsView({
                    collection: locationsCollection,
                    rootModel: rootModel,
                }),
                complete
            ;

            self.headerView.suppress();

            error = function(collection, response, opts) {
                $.notify({message:ERROR_MESSAGE},{type:"danger"});
            };

            locationsCollection.addParam('recurse', true);
            locationsCollection.addParam('archived', false);

            complete = _.invoke([rootModel, locationsCollection], "fetch", {error: error});

            $.when.apply($, self.complete.concat(complete)).done(function() {
                var locationManager = _.where(rootModel.get('access').location_manager, { organization_id: parseInt(ORG_ID) });

                if (!rootModel.isOrgAdmin() && locationManager.length === 1) {
                    self.location_scheduling(_.first(locationManager).location_id);

                    return;
                }

                var data = _.first(locationsCollection.models);

                locationsCollection.remove(data);
                locationsCollection.add(data.get('data'));

                self.appView.showView(locationsView);
            });
        },
        location_dashboard: function(location_id) {
            var self = this,
                orgModel = new Models.Organization(),
                locationModel = new Models.Location({ id: location_id }),
                locationShiftsCollection = new Collections.LocationShifts(),
                locationTimeclocksCollection = new Collections.LocationTimeclocks(),
                locationTimeOffRequestsCollection = new Collections.LocationTimeOffRequests(),
                rolesCollection = new Collections.Roles(),
                locationDashboardView = new Views.LocationDashboardView({
                    locationModel: locationModel,
                    locationShiftsCollection: locationShiftsCollection,
                    locationTimeclocksCollection: locationTimeclocksCollection,
                    locationTimeOffRequestsCollection: locationTimeOffRequestsCollection,
                    rolesCollection: rolesCollection,
                }),
                start = moment().subtract(24, 'hours').utc().format('YYYY-MM-DDTHH:mm:ss'),
                end = moment().add(24, 'hours').utc().format('YYYY-MM-DDTHH:mm:ss'),
                invokeList = [],
                complete,
                error
            ;

            self.headerView.showLocation(location_id);

            locationShiftsCollection.addUpstreamModel('locationId', location_id);
            locationShiftsCollection.addParam('start', start);
            locationShiftsCollection.addParam('end', end);

            locationTimeOffRequestsCollection.addUpstreamModel('locationId', location_id);
            locationTimeOffRequestsCollection.addParam('start', start);
            locationTimeOffRequestsCollection.addParam('end', end);

            locationTimeclocksCollection.addUpstreamModel('locationId', location_id);
            locationTimeclocksCollection.addParam('start', start);

            rolesCollection.addUpstreamModel("locationId", location_id);
            rolesCollection.addParam('recurse', true);

            error = function() {
                $.notify({message:ERROR_MESSAGE},{type:"danger"});
            };

            invokeList.push(orgModel);
            invokeList.push(locationModel);
            invokeList.push(locationShiftsCollection);
            invokeList.push(locationTimeclocksCollection);
            invokeList.push(locationTimeOffRequestsCollection);
            invokeList.push(rolesCollection);

            complete = _.invoke(invokeList, "fetch", {error: error});

            $.when.apply($, self.complete.concat(complete)).done(function() {
                locationModel.set(locationModel.get('data'));
                locationModel.unset('data');

                rolesCollection.add(rolesCollection.models.pop().get("data"));

                self.appView.showView(locationDashboardView);
            });
        },
        location_scheduling: function(location_id, date) {
            var self = this,
                locationsCollection = new Collections.Locations(),
                locationModel,
                displayTimezone = false,
                timezoneWarning = false,
                currentTimezoneOffset,
                allTimezoneOffsets,
                rolesCollection = new Collections.Roles(),
                rolesUsersCollection = new Collections.Roles(),
                orgModel = new Models.Organization(),
                weekStartsOn,
                locationSchedulesView,
                csvFormat = false,
                error,
                complete
            ;

            self.headerView.showLocation(location_id);

            error = function(model, response, opts) {
                $.notify({message:ERROR_MESSAGE},{type:"danger"});
            };

            // add upstream model
            rolesCollection.addUpstreamModel("locationId", location_id);
            rolesUsersCollection.addUpstreamModel("locationId", location_id);

            locationsCollection.addParam('archived', false);
            rolesCollection.addParam('archived', false);
            rolesUsersCollection.addParam("recurse", true);

            // NOTE: data from orgModel could be pulled from the topnav but
            // if loading this page directly, async makes it unreliable
            complete = _.invoke([orgModel, locationsCollection, rolesCollection, rolesUsersCollection], "fetch", {error: error});

            // get the roles and then carry that into the fetches for schedules
            $.when.apply($, self.complete.concat(complete)).done(function() {

                // repack it to get around the 'data' thing
                orgModel.set(orgModel.get("data"));
                orgModel.unset("data");

                locationsCollection.add(locationsCollection.models.pop().get("data"));
                locationModel = locationsCollection.get(location_id);

                // Collection.length wasn't accurate compared to Collection.models.length
                if (locationsCollection.models.length > 1) {

                    allTimezoneOffsets = _.map(
                        locationsCollection.pluck("timezone"), function(timezone) {
                            return moment.tz(timezone)._offset;
                        }
                    );

                    // show timezone if multiple locations with different timezones
                    if (_.uniq(allTimezoneOffsets).length > 1) {
                        displayTimezone = true;
                    }

                }

                currentTimezoneOffset = moment().utcOffset();

                // always show timezone (with a warning) if in different geo
                if (currentTimezoneOffset !== moment.tz(locationModel.get("timezone"))._offset) {
                    displayTimezone = true;
                    timezoneWarning = true;
                }

                weekStartsOn = orgModel.get("day_week_starts");

                if (orgModel.get("enable_shiftplanning_export")) {
                    csvFormat = "shiftplanning";
                }

                rolesCollection.add(rolesCollection.models.pop().get("data"));
                rolesUsersCollection.add(rolesUsersCollection.models.pop().get("data"));

                // go to new roles page if no role exists
                if (rolesCollection.models.length === 0) {
                    return Backbone.history.navigate("locations/" + location_id + "/new-role", {trigger: true});
                }

                locationSchedulesView = new Views.SchedulingControllerView({
                    orgModel: orgModel,
                    locationModel: locationModel,
                    rolesCollection: rolesCollection,
                    rolesUsersCollection: rolesUsersCollection,
                    displayTimezone: displayTimezone,
                    timezoneWarning: timezoneWarning,
                    csvFormat: csvFormat,
                    currentDate: date,
                    weekStartsOn: weekStartsOn,
                    renderHeaderAction: self.headerView.readerHeaderActionButton.bind(self.headerView),
                });

                self.appView.showView(locationSchedulesView);
            });
        },
        location_attendance: function(location_id, date) {
            var self = this,
                orgModel = new Models.Organization(),
                locationsCollection = new Collections.Locations(),
                locationModel,
                allTimezoneOffsets,
                currentTimezoneOffset,
                displayTimezone = false,
                timezoneWarning = false,
                rolesCollection = new Collections.Roles({
                    locationId: location_id,
                }),
                attendanceControllerView,
                weekStartsOn,
                complete,
                error
            ;

            self.headerView.showLocation(location_id);

            // upstream models
            rolesCollection.addUpstreamModel("locationId", location_id);

            // recurse params
            rolesCollection.addParam("recurse", true);

            locationsCollection.addParam("archived", false);

            error = function(model, response, opts) {
                $.notify({message:ERROR_MESSAGE},{type:"danger"});
            };

            // async fetch of multiple models/collection
            complete = _.invoke([orgModel, locationsCollection, rolesCollection], "fetch", {error: error});

            $.when.apply($, self.complete.concat(complete)).done(function() {

                // unpack/repack everything
                rolesCollection.add(rolesCollection.models.pop().get("data"));

                if (rolesCollection.models.length === 0) {
                    return Backbone.history.navigate("locations/" + location_id + "/new-role", {trigger: true});
                }

                locationsCollection.add(locationsCollection.models.pop().get("data"));
                locationModel = locationsCollection.get(location_id);

                orgModel.set(orgModel.get("data"));
                orgModel.unset("data");

                weekStartsOn = orgModel.get("day_week_starts");

                // Collection.length wasn't accurate compared to Collection.models.length
                if (locationsCollection.models.length > 1) {

                    allTimezoneOffsets = _.map(
                        locationsCollection.pluck("timezone"), function(timezone) {
                            return moment.tz(timezone)._offset;
                        }
                    );

                    // show timezone if multiple locations with different timezones
                    if (_.uniq(allTimezoneOffsets).length > 1) {
                        displayTimezone = true;
                    }
                }

                currentTimezoneOffset = moment().utcOffset();

                // always show timezone (with a warning) if in different geo
                if (currentTimezoneOffset !== moment.tz(locationModel.get("timezone"))._offset) {
                    displayTimezone = true;
                    timezoneWarning = true;
                }

                attendanceControllerView = new Views.AttendanceControllerView({
                    collection: rolesCollection,
                    locationId: location_id,
                    locationModel: locationModel,
                    orgModel: orgModel,
                    displayTimezone: displayTimezone,
                    timezoneWarning: timezoneWarning,
                    weekStartsOn: weekStartsOn,
                    renderHeaderAction: self.headerView.readerHeaderActionButton.bind(self.headerView),
                    currentDate: date,
                });

                self.appView.showView(attendanceControllerView);
            });
        },
        location_preferences: function(location_id) {
            var self = this,
                locationModel = new Models.Location({
                    id: location_id,
                }),
                orgModel = new Models.Organization(),
                rootModel = new Models.Root(),
                locationPreferencesView = new Views.LocationPreferencesView({
                    model: locationModel,
                    orgModel: orgModel,
                    rootModel: rootModel,
                    headerView: self.headerView,
                }),
                complete,
                error
            ;

            self.headerView.showLocation(location_id);

            locationModel.addParam('recurse', true);

            error = function(model, response, opts) {
                $.notify({message:ERROR_MESSAGE},{type:"danger"});
            };

            complete = _.invoke([locationModel, orgModel, rootModel], "fetch", {error: error});

            $.when.apply($, self.complete.concat(complete)).done(function() {

                // repack to get around "data" thing
                locationModel.set(locationModel.get("data"));
                locationModel.unset("data");

                self.appView.showView(locationPreferencesView);
            });
        },
        location_preferences_edit: function(location_id, param) {
            var self = this,
                locationModel = new Models.Location({
                    id: location_id,
                }),
                locationParamEditView = new Views.Components.EditParameterView({
                    el: "#manage-main",
                    model: locationModel,
                    param: param,
                    editParamSuccess: function() {
                        router.headerView.refresh();
                    },
                    navigateToSettings: function() {
                        return Backbone.history.navigate("locations/" + location_id + "/preferences", {trigger: true});
                    },
                }),
                success,
                error
            ;

            self.headerView.showLocation(location_id);

            success = function(model, response, opts) {
                self.appView.showView(locationParamEditView);
            };

            error = function(model, response, opts) {
                $.notify({message:"Location or param not found"}, {type:"danger"});
            };

            locationModel.fetch({success: success, error: error});
        },
        location_roles: function(location_id) {
            var self = this,
                rolesCollection = new Collections.Roles({
                    locationId: location_id,
                }),
                locationRolesView = new Views.LocationRolesView({
                    locationId: location_id,
                    collection: rolesCollection,
                }),
                success,
                error
            ;

            self.headerView.showLocation(location_id);

            // add upstream model
            rolesCollection.addUpstreamModel("locationId", location_id);

            success = function(collection, response, opts) {
                rolesCollection.add(rolesCollection.models.pop().get("data"));
                self.appView.showView(locationRolesView);
            };

            error = function(collection, response, opts) {
                $.notify({message:ERROR_MESSAGE},{type:"danger"});
            };

            rolesCollection.fetch({
                success: success,
                error: error,
                data: {
                    recurse: true,
                    archived: false,
                }
            });
        },
        location_role_preferences: function(location_id, role_id) {
            var self = this,
                roleModel = new Models.Role({
                    id: role_id,
                }),
                orgModel = new Models.Organization(),
                recurringShiftsCollection = new Collections.RecurringShifts(),
                rolePreferencesView = new Views.RolePreferencesView({
                    orgModel: orgModel,
                    locationId: location_id,
                    model: roleModel,
                    recurringShiftsCollection: recurringShiftsCollection
                }),
                complete,
                error
            ;

            roleModel.addUpstreamModel("locationId", location_id);
            roleModel.addParam('recurse', true);
            roleModel.addParam('archived', false);

            recurringShiftsCollection.addUpstreamModel('locationId', location_id);
            recurringShiftsCollection.addUpstreamModel('roleId', role_id);

            self.headerView.showLocation(location_id);

            error = function(model, response, opts) {
                $.notify({message:ERROR_MESSAGE},{type:"danger"});
            };

            complete = _.invoke([orgModel, roleModel, recurringShiftsCollection], "fetch", {error: error});

            $.when.apply($, self.complete.concat(complete)).done(function() {
                orgModel.set(orgModel.get('data'));
                orgModel.unset('data');
                roleModel.set(roleModel.get("data"));
                roleModel.unset("data");
                roleModel.clearParams();
                recurringShiftsCollection.each(function(model) {
                    model.addUpstreamModel('locationId', location_id);
                    model.addUpstreamModel('roleId', role_id);
                });
                self.appView.showView(rolePreferencesView);
            });

        },
        add_worker: function(location_id, role_id) {
            var self = this,
                roleModel = new Models.Role({
                    id: role_id,
                }),
                orgModel = new Models.Organization({
                    id: ORG_ID,
                }),
                addWorkerView = new Views.AddWorkerView({
                    model: roleModel,
                    orgModel: orgModel,
                }),
                success,
                error
            ;

            roleModel.addUpstreamModel("locationId", location_id);

            self.headerView.suppress();

            error = function(model, response, opts) {
                $.notify({message:ERROR_MESSAGE},{type:"danger"});
            };

            success = function(model, response, opts) {
                roleModel.set(model.get('data'));
                roleModel.unset('data');
                orgModel.fetch({
                    success: function(m, r, o) {
                        orgModel.set(m.get('data'));
                        orgModel.unset('data');
                        self.appView.showView(addWorkerView);
                    },
                    error: error,
                });
            };

            roleModel.fetch({
                success: success,
                error: error,
                data: {
                    recurse: true,
                    archived: false,
                },
            });
        },
        location_role_preferences_edit: function(location_id, role_id, param) {
            var self = this,
                roleModel = new Models.Role({
                    id: role_id,
                }),
                roleParamEditView = new Views.Components.EditParameterView({
                    el: "#manage-main",
                    model: roleModel,
                    param: param,
                    navigateToSettings: function() {
                        return Backbone.history.navigate("locations/" + location_id + "/roles/" + role_id + "/preferences", {trigger: true});
                    },
                }),
                success,
                error
            ;

            // add upstream model
            roleModel.addUpstreamModel("locationId", location_id);

            self.headerView.showLocation(location_id);

            success = function(model, response, opts) {
                self.appView.showView(roleParamEditView);
            };

            error = function(model, response, opts) {
                $.notify({message:"Role or param not found"}, {type:"danger"});
            };

            roleModel.fetch({
                success: success,
                error: error,
            });
        },
        location_role_user: function(location_id, role_id, user_id) {
            var self = this,
                organizationModel = new Models.Organization(),
                userRoleModel = new Models.UserRole({
                    id: user_id,
                }),
                roleModel = new Models.Role({
                    id: role_id,
                }),
                recurringShiftsCollection = new Collections.RecurringShifts(),
                userRoleView = new Views.UserRoleView({
                    organizationModel: organizationModel,
                    locationId: location_id,
                    roleId: role_id,
                    model: userRoleModel,
                    roleModel: roleModel,
                    recurringShiftsCollection: recurringShiftsCollection
                }),
                sortedModels,
                complete,
                error
            ;

            // add upstream models
            userRoleModel.addUpstreamModel("locationId", location_id);
            userRoleModel.addUpstreamModel("roleId", role_id);
            roleModel.addUpstreamModel("locationId", location_id);

            recurringShiftsCollection.addUpstreamModel('locationId', location_id);
            recurringShiftsCollection.addUpstreamModel('roleId', role_id);
            recurringShiftsCollection.addParam('user_id', user_id);

            self.headerView.showLocation(location_id);

            error = function(model, response, opts) {
                $.notify({message:"Role or param not found"}, {type:"danger"});
            };

            complete = _.invoke([organizationModel, roleModel, userRoleModel, recurringShiftsCollection], "fetch", {error: error});

            $.when.apply($, self.complete.concat(complete)).done(function() {
                // repack it to get around the 'data' thing
                userRoleModel.set(userRoleModel.get("data"));
                userRoleModel.unset("data");

                organizationModel.set(organizationModel.get("data"));
                organizationModel.unset("data");

                recurringShiftsCollection.each(function(model) {
                    model.addUpstreamModel('locationId', location_id);
                    model.addUpstreamModel('roleId', role_id);
                });

                self.appView.showView(userRoleView);
            });
        },
        location_role_user_preferences_edit: function(location_id, role_id, user_id, param) {
            var self = this,
                userRoleModel = new Models.UserRole({
                    id: user_id,
                }),
                userRoleParamEditView = new Views.Components.EditParameterView({
                    el: "#manage-main",
                    model: userRoleModel,
                    param: param,
                    navigateToSettings: function() {
                        return Backbone.history.navigate("locations/" + location_id + "/roles/" + role_id + "/users/" + user_id, {trigger: true});
                    },
                }),
                success,
                error
            ;

            // add upstream models
            userRoleModel.addUpstreamModel("locationId", location_id);
            userRoleModel.addUpstreamModel("roleId", role_id);

            self.headerView.showLocation(location_id);

            success = function(model, response, opts) {
                self.appView.showView(userRoleParamEditView);
            };

            error = function(model, response, opts) {
                $.notify({message:"User or param not found"}, {type:"danger"});
            };

            userRoleModel.fetch({success: success, error: error});
        },
        new_location: function() {
            var self = this,
                locationModel = new Models.Location(),
                timezonesCollection = new Collections.Timezones(),
                newLocationView = new Views.NewLocationView({
                    model: locationModel,
                    timezonesCollection: timezonesCollection,
                    headerView: self.headerView,
                }),
                success,
                error
            ;

            self.headerView.suppress();

            success = function(model, response, opts) {
                self.appView.showView(newLocationView);
            };

            error = function(model, response, opts) {
                $.notify({message:ERROR_MESSAGE},{type:"danger"});
            };

            timezonesCollection.fetch({
                success: success,
                error: error,
            });
        },
        new_role: function(location_id) {
            var self = this,
                roleModel = new Models.Role(),
                newRoleView = new Views.NewRoleView({
                    locationId: location_id,
                    model: roleModel,
                })
            ;

            roleModel.addUpstreamModel("locationId", location_id);

            self.headerView.showLocation(location_id);

            self.appView.showView(newRoleView);
        },
        organization_settings: function() {
            var self = this,
                adminsCollection = new Collections.Admins(),
                locationsCollection = new Collections.Locations(),
                organizationModel = new Models.Organization(),
                plansCollection = new Collections.Plans(),
                organizationSettingsView = new Views.OrganizationSettingsView({
                    model: organizationModel,
                    adminsCollection: adminsCollection,
                    locationsCollection: locationsCollection,
                    plansCollection: plansCollection,
                }),
                error,
                complete
            ;

            locationsCollection.addParam("recurse", true);
            locationsCollection.addParam("archived", false);

            self.headerView.suppress();

            error = function(model, response, opts) {
                $.notify({message:ERROR_MESSAGE},{type:"danger"});
            };

            complete = _.invoke([organizationModel, adminsCollection, locationsCollection, plansCollection], "fetch", {error: error});

            $.when.apply($, self.complete.concat(complete)).done(function() {

                // repack stuff to get around the 'data' thing
                organizationModel.set(organizationModel.get("data"));
                organizationModel.unset("data");

                locationsCollection.add(locationsCollection.models.pop().get("data"));

                self.appView.showView(organizationSettingsView);
            });
        },
        organization_settings_edit: function(param) {
            var self = this,
                organizationModel = new Models.Organization({id: ORG_ID}),
                organizationSettingsEditView = new Views.Components.EditParameterView({
                    el: "#manage-main",
                    model: organizationModel,
                    param: param,
                    editParamSuccess: function() {
                        router.messagesView.refresh();
                    },
                    navigateToSettings: function() {
                        return Backbone.history.navigate("settings", {trigger: true});
                    },
                }),
                success,
                error
            ;

            self.headerView.suppress();

            success = function(model, response, opts) {
                self.appView.showView(organizationSettingsEditView);
            };

            error = function(model, response, opts) {
                $.notify({message:"Organization or param not found"}, {type:"danger"});
            };

            organizationModel.fetch({success: success, error: error});
        },
        default: function() {
            var self = this,
                homeView = new Views.HomeView()
            ;

            self.headerView.suppress();

            // TODO - determine level of auth that role has
            //        then make path to specific route

            self.navigate("home");
            self.appView.showView(homeView);
        }
    });


    root.App.Router = Router;
})(this);
