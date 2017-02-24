(function(root) {

    "use strict";

    var Base = Backbone.Model.extend({
        endpoint: "",
        initialize: function() {
            this.upstreamModels = {};
        },
        urlRoot: function() {
            var self = this,
                endpointResult = ""
            ;
            if (_.isFunction(this.endpoint)) {
                endpointResult = self.endpoint();
            } else {
                if (!_.isEmpty(self.endpoint)) {
                    endpointResult = self.endpoint;
                }
            }

            return "/api/v2/" + endpointResult;
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
    });

    root.App.Models.Base = Base;
})(this);
