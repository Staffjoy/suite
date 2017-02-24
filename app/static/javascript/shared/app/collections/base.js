(function(root) {

    "use strict";

    var Models = root.App.Models,
        Base = Backbone.Collection.extend({
            model: Models.Base,
            endpoint: "",
            initialize: function() {
                this.upstreamModels = {};
                this.params = {};
            },
            url: function() {
                var self = this,
                    endpointResult = ""
                ;

                if (_.isFunction(self.endpoint)) {
                    endpointResult = self.endpoint();
                } else {
                    endpointResult = self.endpoint;
                }

                return "/api/v2/organizations/" + ORG_ID + "/" + endpointResult;
            },
            credentials: function() {
                return {
                    username: API_KEY,
                    password: "",
                };
            },
            addUpstreamModel: function(name, id) {
                this.upstreamModels[name] = id;
            },
            getUpstreamModelId: function(name) {
                var self = this;

                if (!_.isUndefined(self.upstreamModels)) {
                    return _.property(name)(self.upstreamModels);
                }
            },
            addProperty: function(name, value) {
                this[name] = value;
            },
            addParam: function(name, value) {
                this.params[name] = value;
            },
            clearParams: function() {
                this.params = {};
            },
            getParams: function() {
                var self = this,
                    result = "",
                    pairs = [],
                    paramKeys = _.keys(self.params)
                ;

                if (paramKeys.length > 0) {
                    _.each(paramKeys, function(param, index, list) {
                        pairs.push(param + "=" + self.params[param]);
                    });

                    result = "?" + pairs.join("&");
                }

                return result;
            },
        })
    ;

    root.App.Collections.Base = Base;
})(this);
