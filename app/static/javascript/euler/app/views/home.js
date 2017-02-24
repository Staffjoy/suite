(function(root) {

    "use strict";

    var Util = root.App.Util,
        Views = root.App.Views
    ;

    var HomeView = Views.Base.extend({
        el: "#euler-container",
        initialize: function() {
            HomeView.__super__.initialize.apply(this);
        },
        render: function() {
            var self = this,
                opts = {
                    STRINGS: {
                        welcome: "Welcome to Euler, the gateway to all things internal!",
                        warning: "With great power comes great responsibility. Be careful and treat all customer information as confidential.",
                    },
                    links: [
                        {name: "Users", link: "#users"},
                        {name: "Organizations", link: "#organizations"},
                        {name: "KPI Dashboard", link: "#kpis"},
                        {name: "API V2 Schedule Monitoring", link: "#schedule-monitoring"},
                    ]
                }
            ;

            self.$el.html(ich.home(opts));

            return this;
        }
    });

    root.App.Views.HomeView = HomeView;

})(this);
