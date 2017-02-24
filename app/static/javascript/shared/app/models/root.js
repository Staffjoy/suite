(function(root) {

    "use strict";

    var Models = root.App.Models,
        Root = Models.Base.extend({
            endpoint:  "",
            urlRoot: "/api/v2/",
            isOrgAdmin: function() {
                var self = this,
                    access = self.get('access'),
                    orgs = access.organization_admin,
                    org = _.findWhere(orgs, { organization_id: parseInt(ORG_ID) })
                ;

                return self.get('access').sudo || !!org;
            },
        })
    ;

    root.App.Models.Root = Root;
})(this);
