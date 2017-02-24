(function(root) {

    "use strict";

    var Views = root.App.Views;

    var LocationRoleCardView = Views.Base.extend({
        el: "#manage-main .role-cards",
        events: {},
        initialize: function(opts) {
            LocationRoleCardView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {
                if (!_.isUndefined(opts.locationId)) {
                    this.locationId = opts.locationId;
                }

                if (!_.isUndefined(opts.roleId)) {
                    this.roleId = opts.roleId;
                }
            }
        },
        render: function(opts) {
            var self = this,
                data
            ;

            _.map(self.model.get("users"), function(user) {
                if (_.isNull(user.name) || _.isEmpty(user.name) || _.isUndefined(user.name)) {
                    user.name = user.email;
                }
            });

            data = _.extend({}, self.model.toJSON(), opts);

            self.$el.append(ich.location_role(data));

            return this;
        },
    });

    root.App.Views.LocationRoleCardView = LocationRoleCardView;

})(this);
