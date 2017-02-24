(function(root) {

    "use strict";

    var Collections = root.App.Collections,
        Models = root.App.Models,
        Views = root.App.Views,
        Util = root.App.Util
    ;

    var MessageModalView = Views.Base.extend({
        events: {
            "click .modal-message-action": "modalAction",
        },
        initialize: function(opts) {
            MessageModalView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.el)) {
                    this.el = opts.el;
                    this.$el = $(opts.el);
                }

                if (!_.isUndefined(opts.params)) {
                    this.params = opts.params;
                }

                if (!_.isUndefined(opts.callback) && _.isFunction(opts.callback)) {
                    this.callback = opts.callback;
                }
            }

            this.modal;
        },
        render: function(opts) {
            var self = this;

            self.$el.html(ich.modal_message(self.params));

            self.modal = $("#message-modal");
            self.modal.modal();

            self.modal.on("hidden.bs.modal", function(e) {
                self.close();
            });
        },
        modalAction: function(e) {
            e.preventDefault();
            e.stopPropagation();

            var self = this;
            self.callback();
            self.modal.modal("hide");
        },
    });

    root.App.Views.Components.MessageModalView = MessageModalView;

})(this);
