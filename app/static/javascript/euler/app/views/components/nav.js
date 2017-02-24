(function(root) {

    "use strict";

    var Util = root.App.Util,
        Views = root.App.Views
    ;

    var Nav = Views.Base.extend({
        el: "#euler-nav",
        events: {
            "click .euler-nav-title": "homeClick",
            "submit form.euler-search": "search",
        },
        initialize: function() {
            Nav.__super__.initialize.apply(this);
        },
        render: function() {
            var self = this,
                opts = {
                    title: "Euler",
                }
            ;

            self.$el.html(ich.nav(opts));

            return this;
        },
        homeClick: function(e) {
            Backbone.history.navigate("home", {trigger: true});
        },
        search: function(e) {
            e.preventDefault();
            var query = $("#euler-search-box").val();
            if (query) {
                Backbone.history.navigate("search/" + encodeURIComponent(query), {trigger: true});
            }
        }
    });

    root.App.Views.Components.Nav = Nav;
})(this);
