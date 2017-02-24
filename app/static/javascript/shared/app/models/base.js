(function(root) {

    "use strict";

    var Base = Backbone.Model.extend({
        endpoint: "",
        initialize: function() {
            this.upstreamModels = {};
            this.params = {};
        },
        urlRoot: function() {
            var self = this,
                endpointResult = ""
            ;
            if (_.isFunction(this.endpoint)) {
                endpointResult = "/" + self.endpoint();
            } else {
                if (!_.isEmpty(self.endpoint)) {
                    endpointResult = "/" + self.endpoint;
                }
            }

            return "/api/v2/organizations/" + ORG_ID + endpointResult;
        },
        url: function() {
            var self = this;

            if (_.isEmpty(self.params)) {
                return Base.__super__.url.call(self);
            } else {
                return Base.__super__.url.call(self) + self.getParams();
            }
        },
        credentials: function() {
            return {
                username: API_KEY,
                password: "",
            };
        },
        createRequest: function() {
            var self = this,
                endpointResult
            ;

            if (_.isFunction(self.endpoint)) {
                endpointResult = self.endpoint();
            } else {
                endpointResult = self.endpoint;
            }

            self.endpoint = endpointResult + "/";
        },
        addProperty: function(name, value) {
            this[name] = value;
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
    });

    root.App.Models.Base = Base;
})(this);
