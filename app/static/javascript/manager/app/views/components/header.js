(function(root) {

    "use strict";

    var Views = root.App.Views;

    var HeaderView = Views.Base.extend({
        el: "#main-header-content",
        events: {
            'click .nav-button': 'navigate',
            'click .header-action': 'headerActionClicked',
        },
        initialize: function(opts) {
            HeaderView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.rootModel)) {
                    this.rootModel = opts.rootModel;
                }

                if (!_.isUndefined(opts.loaded)) {
                    this.loaded = opts.loaded;
                }
            }

            this.suppressed = true;
        },
        render: function() {
            var self = this,
                access = self.rootModel.get('access'),
                locationManager = access.location_manager,
                locations = self.rootModel.isOrgAdmin() ? self.collection.models : _.chain(locationManager).where({
                    organization_id: parseInt(ORG_ID)
                }).map(function(data) {
                    return self.collection.get(data.location_id);
                }).valueOf(),
                data = {
                    orgId: self.model.get('data').id,
                    orgName: self.model.get('data').name,
                    singleLocation: locations.length === 1 ? _.first(locations).attributes : false,
                    isOrgAdmin: self.rootModel.isOrgAdmin(),
                    isEarlyAccess: self.model.isEarlyAccess(),
                }
            ;

            self.$el.html(ich.manager_header(data));

            if (locations.length > 1) {
                $('.header-location-select').select2({
                    data: locations.map(function(model) {
                        return {
                            id: model.id,
                            text: model.get('name'),
                        };
                    }),
                });
            }

            if (self.suppressed) {
                self.suppress();
            }

            $('.header-location-select').on("select2:select", function (e) {
                var self = this,
                    locationId = e.params.data.id
                ;

                self.locationId = locationId;
                Backbone.history.navigate('#locations/' + self.locationId, {trigger: true});
            });

            self.$el.addClass('has-content');

            return this;
        },
        close: function() {
            self.$el.removeClass('has-content');
            $('.header-location-select').off();
            HeaderView.__super__.close.call(this);
        },
        readerHeaderActionButton: function(view) {
            var self = this;

            if (!!self.delegateViews['header-action']) {
                self.delegateViews['header-action'].close();
            }

            if (!!self.delegateViews['header-action-mobile']) {
                self.delegateViews['header-action-mobile'].close();
            }

            if (!!view && _.isFunction(view.getAction) && !!view.getAction()) {
                self.addDelegateView(
                    'header-action',
                    new Views.Components.HeaderActionView({
                        action: view.getAction(),
                    })
                );
                self.addDelegateView(
                    'header-action-mobile',
                    new Views.Components.HeaderActionMobileView({
                        action: view.getAction(),
                    })
                );
            }
        },
        setCurrentView: function(view) {
            // Can be:
            //  - (bool) false (clear menu)
            //  - "inherit" (do nothing - show last state)
            //  - (str) route (clear menu and set that menu route to active)
            var activeRouteState = view.mainHeaderContentVisible;

            this.readerHeaderActionButton(view);

            if (activeRouteState === "inherit") {
                // Special case - don't change anything
                return;
            }

            this.clearActive();

            if (activeRouteState === false) {
                return;
            }

            $("#manager-header-nav .nav-button-" + activeRouteState).addClass('active');
        },
        clearActive: function() {
            var self = this;

            $("#manager-header-nav .nav-button").removeClass("active");
        },
        showLocation: function(locationId) {
            var self = this;

            self.suppressed = false;
            self.locationId = locationId;

            $.when.apply($, self.loaded).done(function() {
                $('body').addClass('manager-full-header');
                $('body').removeClass('manager-partial-header');
                $('#manager-header-nav').show();
                $('.header-location-select').val(locationId).trigger('change');
                $('#manager-header-action').addClass('expanded');
            })
        },
        suppress: function() {
            var self = this;

            self.suppressed = true;

            $.when.apply($, self.loaded).done(function() {
                $('body').removeClass('manager-full-header');
                $('body').addClass('manager-partial-header');
                $('#manager-header-nav').hide();
                $('#manager-header-action').removeClass('expanded');
            });
        },
        navigate: function(event) {
            var self = this,
                $target = $(event.target),
                $button = $target.closest('.nav-button'),
                route = $button.data('route')
            ;

            switch (route) {
                case 'settings':
                    Backbone.history.navigate('#settings', {trigger: true});
                    break;
                case 'dashboard':
                    Backbone.history.navigate('#locations/' + self.locationId, {trigger: true});
                    break;
                case 'locations':
                    Backbone.history.navigate('#locations/' + self.locationId, {trigger: true});
                    break;
                case 'scheduling':
                    Backbone.history.navigate('#locations/' + self.locationId + '/scheduling', {trigger: true});
                    break;
                case 'attendance':
                    Backbone.history.navigate('#locations/' + self.locationId + '/attendance', {trigger: true});
                    break;
                case 'roles':
                    Backbone.history.navigate('#locations/' + self.locationId + '/roles', {trigger: true});
                    break;
                case 'preferences':
                    Backbone.history.navigate('#locations/' + self.locationId + '/preferences', {trigger: true});
                    break;
            }
        },
        refresh: function() {
            var self = this,
                complete,
                error
            ;

            error = function(model, response, opts) {
                $.notify({message:"There was an error loading the header - please contact support if the problem persists"},{type:"danger"});
            };

            self.loaded = _.invoke([self.model, self.collection], "fetch", {error: error});

            $.when.apply($, self.loaded).done(function() {
                var data = _.first(self.collection.models),
                    activeLocations = _.where(data.get('data'), { archived: false })
                ;

                self.collection.remove(data);
                self.collection.add(activeLocations);

                $('.header-location-select').off();
                self.render();
            });
        },
    });

    root.App.Views.Components.HeaderView = HeaderView;

})(this);
