(function(root) {

    "use strict";

    var Util = root.App.Util,
        Views = root.App.Views
    ;

    var UsersView = Views.Base.extend({
        el: "#euler-container",
        events: {
            "click tr.user-row": "showUser",
            "click .pagination .previous": "previousPage",
            "click .pagination .next": "nextPage",
        },
        initialize: function(opts) {
            UsersView.__super__.initialize.apply(this);
            this.page = parseInt(opts.page);
        },
        render: function(opts) {
            var self = this,
                endpoint = {endpoint: self.collection.endpoint},
                data = _.extend({}, self.collection.toJSON()[0], endpoint, opts);

            self.$el.html(ich.users(data));
            return this;
        },
        showUser: function(e) {
            var $target = $(e.target).parent("tr.user-row"),
                id = $target.attr("data-id")
            ;

            e.preventDefault();
            e.stopPropagation();

            Backbone.history.navigate("users/" + id, {trigger:true});
        },
        previousPage: function(e) {
            var self = this;

            e.preventDefault();
            e.stopPropagation();

            Backbone.history.navigate("users/page/" + (self.page-1), {trigger:true});
        },
        nextPage: function(e) {
            var self = this;

            e.preventDefault();
            e.stopPropagation();

            Backbone.history.navigate("users/page/" + (self.page+1), {trigger:true});
        },
    });

    root.App.Views.UsersView = UsersView;

})(this);
