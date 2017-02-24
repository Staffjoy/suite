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
                locationModel = new Models.Location({
                    id: LOCATION_ID,
                }),
                roleModel = new Models.Role({
                    id: ROLE_ID,
                }),
                userModel = new Models.UserRole({
                    id: USER_ID,
                }),
                timeclockCollection = new Collections.Timeclocks(),
                headerView = new Views.Components.HeaderView({
                    models: {
                        organization: orgModel,
                        location: locationModel,
                        role: roleModel,
                        user: userModel,
                        timeclocks: timeclockCollection,
                    },
                }),
                complete,
                error
            ;

            // add upstream models where necessary
            roleModel.addUpstreamModel("locationId", LOCATION_ID);
            userModel.addUpstreamModel("locationId", LOCATION_ID);
            userModel.addUpstreamModel("roleId", ROLE_ID);

            timeclockCollection.addUpstreamModel("locationId", LOCATION_ID);
            timeclockCollection.addUpstreamModel("roleId", ROLE_ID);
            timeclockCollection.addUpstreamModel("userId", USER_ID);
            timeclockCollection.addParam('active', true);

            self.headerView = headerView;
            self.headerView.render();

            self.orgModel = orgModel;
            self.userModel = userModel;
            self.timeclockCollection = timeclockCollection;
            self.roleModel = roleModel;
            self.locationModel = locationModel;

            error = function(collection, response, opts) {
                $.notify({message:"There was an error loading the page - please contact support if the problem persists"},{type:"danger"});
            };

            complete = _.invoke([orgModel, locationModel, roleModel, userModel, timeclockCollection], "fetch", {error: error});

            $.when.apply($, complete).done(function() {
                self.headerView.populateName();
            });
        },
        routes: {
            "week" : "planner",
            "week/:date" : "planner",
            "home" : "planner",
            "timeclock": "timeclock",
            "*action" : "planner",
        },
        planner: function(date) {
            var self = this,
                weekStartsOn,
                orgModel = self.orgModel,
                locationModel = self.locationModel,
                roleModel = self.roleModel,
                userModel = self.userModel,
                currentTimezone,
                displayTimezone = false,
                plannerControllerView,
                error,
                complete
            ;

            error = function(model, response, opts) {
                $.notify({message:"There was an error loading the page - please contact support if the problem persists"},{type:"danger"});
            };

            // add upstream model ids
            roleModel.addUpstreamModel("locationId", LOCATION_ID);
            userModel.addUpstreamModel("locationId", LOCATION_ID);
            userModel.addUpstreamModel("roleId", ROLE_ID);

            complete = _.invoke([orgModel, locationModel, roleModel, userModel, self.timeclockCollection], "fetch", {error: error});

            $.when.apply($, complete).done(function() {

                weekStartsOn = orgModel.get("data")["day_week_starts"];

                // extract model properties
                userModel.set(userModel.get("data"));
                userModel.unset("data");

                locationModel.set(locationModel.get("data"));
                locationModel.unset("data");

                orgModel.set(orgModel.get("data"));
                orgModel.unset("data");

                currentTimezone = jstz.determine().name();

                if (currentTimezone !== locationModel.get("timezone")) {
                    displayTimezone = true;
                }

                plannerControllerView = new Views.PlannerControllerView({
                    currentDate: date,
                    weekStartsOn: weekStartsOn,
                    orgModel: orgModel,
                    locationModel: locationModel,
                    roleModel: roleModel,
                    userModel: userModel,
                    displayTimezone: displayTimezone,
                    timezone: currentTimezone,  // everything is shown in the local/system time
                });

                self.appView.showView(plannerControllerView);
                self.headerView.showTimeclockButton(roleModel.get("data").enable_timeclock);
            });
        },
        timeclock: function() {
            var self = this,
                error,
                complete
            ;

            error = function(collection, response, opts) {
                $.notify({message:"There was an error loading the page - please contact support if the problem persists"},{type:"danger"});
            };

            complete = _.invoke([self.roleModel, self.timeclockCollection, self.locationModel], "fetch", {error: error});

            $.when.apply($, complete).done(function() {
                if (self.roleModel.get('data').enable_timeclock) {
                    self.appView.showView(
                        new Views.TimeclockView({
                            collection: self.timeclockCollection,
                            locationModel: self.locationModel,
                        })
                    );
                    self.headerView.showMySchedulesButton();
                } else {
                    self.planner();
                }
            });
        },
        default: function() {
            var self = this;

            self.navigate("week");
        },
    });

    root.App.Router = Router;
})(this);
