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

            var nav = new Views.Components.Nav();

            nav.render();
        },
        routes: {
            "users" : "users",
            "users/page/:id" : "users_paginated",
            "users/:id" : "user_page",
            "users/:id/edit/:params" : "edit_user_param",
            "organizations" : "orgs",
            "organizations/page/:id" : "orgs_paginated",
            "organizations/:id" : "org_page",
            "organizations/:id/edit/:params" : "edit_org_param",
            "new-organization" : "new_organization",
            "search/:params": "search",
            "search/:params/page/:id": "search_paginated",
            "schedule-monitoring": "schedule_monitoring",
            "kpis": "kpis",
            "home" : "default",
            "*action" : "default",
        },
        users: function() {
            this.users_paginated(1);
        },
        users_paginated: function(page) {
            var self = this,
                success,
                error,
                limit = 50,
                // We one-index pages :=)
                offset = (parseInt(page) - 1) * limit,
                usersCollection = new Collections.Users(),
                usersView = new Views.UsersView({
                    collection: usersCollection,
                    page: page,
                })
            ;

            success = function(collection, response, opts) {
                var user_count = collection.toJSON()[0].data.length;

                self.appView.showView(usersView, {
                    page: page,
                    has_next: (user_count == limit),
                    has_previous: (page > 1),
                });
            };

            error = function(collection, response, opts) {
                $.notify({message:"Failed to fetch users collection"},{type:"danger"});
                this.navigate("home", {trigger: true});
            };

            usersCollection.fetch({
                success: success,
                error: error,
                data: {
                    limit: limit,
                    offset: offset,
                }
            });

        },
        user_page: function(id) {
            var self = this,
                userModel = new Models.User({
                    id: id,
                }),
                userView = new Views.UserView({
                    model: userModel,
                }),
                success,
                error
            ;

            success = function(model, response, opts) {
                self.appView.showView(userView);
            };

            error = function(model, response, opts) {
                $.notify({message:"User not found"}, {type:"danger"});
            };

            userModel.fetch({
                success: success,
                error: error,
                data: {
                    archived: false
                }
            });
        },
        edit_user_param: function(id, param) {
            var self = this,
                userModel = new Models.User({
                    id: id,
                }),
                userEditView = new Views.UserEditView({
                    model: userModel,
                    param: param,
                }),
                success,
                error
            ;

            success = function(model, response, opts) {
                self.appView.showView(userEditView);
            };

            error = function(model, response, opts) {
                $.notify({message:"User or param not found"}, {type:"danger"});
            };

            userModel.fetch({success: success, error: error});
        },
        orgs: function() {
            this.orgs_paginated(1);
        },
        orgs_paginated: function(page) {
            var self = this,
                success,
                error,
                limit = 50,

                offset = (parseInt(page) - 1) * limit,
                orgsCollection = new Collections.Organizations(),
                plansCollection = new Collections.Plans(),
                orgsView = new Views.OrganizationsView({
                    collection: orgsCollection,
                    plansCollection: plansCollection,
                    page: page,
                })
            ;

            success = function(collection, response, opts) {
                var orgs_count = collection.toJSON()[0].data.length;

                plansCollection.fetch({
                    success: function(model, response, opts) {
                        self.appView.showView(orgsView, {
                            page: page,
                            has_next: (orgs_count == limit),
                            has_previous: (page > 1),
                        });
                    },
                    error: error,
                });
            };

            error = function(collection, response, opts) {
                $.notify({message:"Failed to fetch organizations"},{type:"danger"});
                this.navigate("home", {trigger: true});
            };

            orgsCollection.fetch({
                success: success,
                error: error,
                data: {
                    limit: limit,
                    offset: offset,
                }
            });

        },
        org_page: function(id) {
            var self = this,
                orgModel = new Models.Organization({
                    id: id,
                }),
                plansCollection = new Collections.Plans(),
                orgView = new Views.OrganizationView({
                    model: orgModel,
                    plansCollection: plansCollection,
                }),
                complete,
                error
            ;

            error = function(model, response, opts) {
                $.notify({message:"Organization not found"}, {type:"danger"});
            };

            complete = _.invoke([orgModel, plansCollection], "fetch", {error:error});

            $.when.apply($, complete).done(function() {
                self.appView.showView(orgView);
            });
        },
        edit_org_param: function(id, param) {
            var self = this,
                orgModel = new Models.Organization({
                    id: id,
                }),
                orgEditView = new Views.OrganizationEditView({
                    model: orgModel,
                    param: param,
                }),
                success,
                error
            ;

            success = function(model, response, opts) {
                self.appView.showView(orgEditView);
            };

            error = function(model, response, opts) {
                $.notify({message:"Organization or param not found"}, {type:"danger"});
            };

            orgModel.fetch({success: success, error: error});
        },
        new_organization: function() {
            var self = this,
                newOrgView = new Views.OrganizationNewView()
            ;

            self.appView.showView(newOrgView);
        },
        search: function(query) {
            this.search_paginated(query, 1);
        },
        search_paginated: function(query, page) {
            var self = this,
                success,
                error,
                limit = 25,
                // We one-index pages :=)
                offset = (parseInt(page) - 1) * limit,
                usersCollection = new Collections.Users()
            ;

            // We have 3 possibilities:
            // 1) No results. Show an error.
            // 2) One result. Redirect to that user.
            // 3) Multiple results. Paginate.

            success = function(collection, response, opts) {
                var user_count = collection.toJSON()[0].data.length;
                if (user_count === 0) {
                    $.notify({message:"No results found"},{type:"danger"});
                } else if (user_count === 1) {
                    var id = collection.toJSON()[0].data[0].id;
                    Backbone.history.navigate("/users/" + id, {trigger: true});
                } else {
                    // Multiple users
                    var searchResultsView = new Views.SearchResultsView({
                        collection: usersCollection,
                        page: page,
                        query: query
                    });

                    self.appView.showView(searchResultsView, {
                        page: page,
                        has_next: (user_count == limit),
                        has_previous: (page > 1),
                    });
                }
            };

            error = function(collection, response, opts) {
                $.notify({message:"Failed to fetch users collection"},{type:"danger"});
                this.navigate("home", {trigger: true});
            };

            if (query.indexOf("@") > -1) {
                // There is an @symbol - search by email address
                usersCollection.fetch({
                    success: success,
                    error: error,
                    data: {
                        limit: limit,
                        offset: offset,
                        filterByEmail: query,
                    }
                });
            } else {
                // Filter by username
                usersCollection.fetch({
                    success: success,
                    error: error,
                    data: {
                        limit: limit,
                        offset: offset,
                        filterByUsername: query,
                    }
                });
            }

        },
        schedule_monitoring: function() {
            var self = this,
                scheduleMonitorsCollection = new Collections.ScheduleMonitors(),
                scheduleMonitoringView = new Views.ScheduleMonitoringView({
                    collection: scheduleMonitorsCollection,
                }),
                success,
                error
            ;

            success = function(collection, response, opts) {
                self.appView.showView(scheduleMonitoringView);
            };

            error = function(collection, response, opts) {
                $.notify({message:"Failed to fetch schedules in progress"},{type:"danger"});
                this.navigate("home", {trigger: true});
            };

            scheduleMonitorsCollection.fetch({
                success: success,
                error: error,
            });
        },
        kpis: function() {
            var self = this,
                kpisModel = new Models.Kpis()
            ;

            kpisModel.fetch({
                success: function() {
                    self.navigate("kpis");
                    self.appView.showView(new Views.KpisView({ model: kpisModel }));
                },
            });
        },
        default: function() {
            var self = this,
                homeView = new Views.HomeView()
            ;

            self.navigate("home");
            self.appView.showView(homeView);
        },
    });

    root.App.Router = Router;

})(this);
