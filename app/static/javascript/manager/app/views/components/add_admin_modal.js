(function(root) {

    "use strict";

    var Models = root.App.Models,
        Views = root.App.Views,
        Util = root.App.Util
    ;

    var AddAdminModalView = Views.Base.extend({
        el: ".add-admin-modal-placeholder",
        events: {
            'click .add-admin-button': 'addAdmin',
        },
        initialize: function(opts) {
            AddAdminModalView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.adminCardView)) {
                    this.adminCardView = opts.adminCardView;
                }
            }
        },
        render: function(opts) {
            var self = this,
                data = {},
                $modal
            ;

            self.$el.html(ich.add_admin_modal(data));

            $modal = $("#add-admin-modal");

            $modal.modal();

            $modal.on("hidden.bs.modal", function(e) {
                $('body').removeClass('modal-open');
                self.close();
            });

            self.$modal = $modal;
        },
        close: function() {
            var self = this;

            self.$modal.off("hidden.bs.modal");
            AddAdminModalView.__super__.close.call(this);
        },
        addAdmin: function(event) {
            event.stopPropagation();

            var self = this,
                emailAddress = $("#admin-email").val(),
                name = $("#admin-name").val(),
                adminModel = new Models.Admin(),
                success,
                error
            ;

            // disable the feature
            $(".add-admin-button").attr("disabled", "disabled");

            $("#add-admin-modal").modal('hide');

            adminModel.createRequest();

            success = function(model, responde, opts) {
                $.notify({message: "Successfully added " + model.get("email")}, {type:"success"});

                // add the model to the collection
                self.adminCardView.collection.add(model);

                // re render the collection
                $(self.adminCardView.el).empty();
                self.adminCardView.render();
                $("#admin-email").focus();
                $("#add-admin-modal").modal('hide');
            };

            error = function(model, response, opts) {
                $(".add-admin-button").removeAttr("disabled");
                $.notify({message:"Unable to add " + emailAddress},{type: "danger"});
                $("#add-admin-modal").modal('hide');
            };

            adminModel.save(
                {
                    email: emailAddress,
                    name: name,
                },
                {
                    success: success,
                    error: error,
                }
            );
        },
    });

    root.App.Views.Components.AddAdminModalView = AddAdminModalView;

})(this);
