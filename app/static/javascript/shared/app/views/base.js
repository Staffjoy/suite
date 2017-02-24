(function(root) {

    "use strict";

    var Base = Backbone.View.extend({
        initialize: function(){
            this.delegateViews = {};
            this.sideNavVisible = false;
            this.topNavVisible = false;
        },
    });

    root.App.Views.Base = Base;

})(this);

