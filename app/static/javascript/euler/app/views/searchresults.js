(function(root) {

    "use strict";

    var Util = root.App.Util,
        Views = root.App.Views
    ;

    var SearchResultsView = Views.Base.extend({
        el: "#euler-container",
        events: {
            "click tr.user-row": "showUser",
            "click .pagination .previous": "previousPage",
            "click .pagination .next": "nextPage",
        },
        initialize: function(opts) {
            SearchResultsView.__super__.initialize.apply(this);
            this.query = opts.query;
            this.page = opts.page;
        },
        render: function(opts) {
            var self = this,
                data = _.extend({}, self.collection.toJSON()[0], opts);

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
            e.preventDefault();
            e.stopPropagation();

            Backbone.history.navigate("/search/" + encodeURIComponent(this.query) + "/page/" + (this.page-1), {trigger:true});
        },
        nextPage: function(e) {
            e.preventDefault();
            e.stopPropagation();

            Backbone.history.navigate("/search/" + encodeURIComponent(this.query) + "/page/" + (this.page+1), {trigger:true});
        },
    });

    root.App.Views.SearchResultsView = SearchResultsView;

})(this);
