(function (root) {

    'use strict';

    var App = {
        Collections: {},
        Events: _.extend({}, Backbone.Events),
        Models: {},
        Router: {},
        Views: {
            Components: {},
        },
        Util: {},
    };

    root.App = App;
})(this);
