(function(root) {

    "use strict";

    var Views = root.App.Views;

    var HomeView = Views.Base.extend({
        el: "#manage-main",
        initialize: function(options) {
            HomeView.__super__.initialize.apply(this);

            this.topNavVisible = "home";
        },
        render: function() {
            var self = this;

            self.$el.html(ich.home());

            return this;
        }
    });

    root.App.Views.HomeView = HomeView;

})(this);
