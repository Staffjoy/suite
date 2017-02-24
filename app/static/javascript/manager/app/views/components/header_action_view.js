(function(root) {

    "use strict";

    var Views = root.App.Views;

    var HeaderActionView = Views.Base.extend({
        el: "#manager-header-action",
        events: {
            'click .header-action': 'headerActionClicked',
        },
        initialize: function(opts) {
            HeaderActionView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.action)) {
                    this.action = opts.action;
                }
            }
        },
        render: function() {
            var self = this,
                data = {
                    label: self.action.label,
                    multipleActions: _.isArray(self.action.data),
                    data: self.action.data,
                }
            ;

            self.$el.html(ich.header_action_view(data));

            return this;
        },
        headerActionClicked: function(event) {
            event.preventDefault();
            event.stopPropagation();

            var self = this;

            self.action.callback(event);
        },
    });

    root.App.Views.Components.HeaderActionView = HeaderActionView;
})(this);
