(function(root) {

    "use strict";

    var Models = root.App.Models,
        Organization = Models.Base.extend({
            editableProperties: {
                name: {type: "str", name: "Name"},
                active: {type: "bool", name: "Active"},
            },
            endpoint: "",
            url: function() {
                var self = this;
                return self.urlRoot();
            },
            isBoss: function() {
                return _.indexOf(["per-seat-v1", "boss-v2"], this.get("plan")) >= 0;
            },
            isFlex: function() {
                return _.indexOf(["flex-v1", "flex-v2"], this.get("plan")) >= 0;
            },
            isEarlyAccess: function() {
                return this.get('data')['early_access'];
            },
        })
    ;

    root.App.Models.Organization = Organization;
})(this);
