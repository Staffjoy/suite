(function(root) {

    "use strict";

    var Views = root.App.Views;

    var HeaderActionMobileView = Views.Base.extend({
        el: "#mobile-header-action",
        events: {
            'click .header-action': 'headerActionClicked',
        },
        initialize: function(opts) {
            HeaderActionMobileView.__super__.initialize.apply(this);

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

            self.$el.html(ich.header_action_mobile_view(data));

            self.$el.on('show.bs.dropdown', function(event) {
                event.stopPropagation();

                var $body = $(document.body);

                $body.toggleClass('modal-open');
                $body.append('<div class="slider-open modal-backdrop fade in"></div>');
            });

            self.$el.on('hide.bs.dropdown', function(event) {
                var $body = $(document.body),
                    $backdrop = $('.modal-backdrop')
                ;

                $backdrop.remove();
                $body.toggleClass('modal-open');
            });

            return this;
        },
        close: function() {
            this.$el.off;
            $('.modal-backdrop').remove();
            HeaderActionMobileView.__super__.close.call(this);
        },
        headerActionClicked: function(event) {
            event.preventDefault();
            event.stopPropagation();

            var self = this;

            self.action.callback(event);
        },
    });

    root.App.Views.Components.HeaderActionMobileView = HeaderActionMobileView;
})(this);
