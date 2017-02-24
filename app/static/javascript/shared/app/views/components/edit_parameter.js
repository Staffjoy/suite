(function(root) {

    "use strict";

    var Util = root.App.Util,
        Views = root.App.Views,
        Models = root.App.Models
    ;

    var EditParameterView = Views.Base.extend({
        el: "#manage-main",
        sideNavVisible: "inherit",
        topNavVisible: "inherit",
        events: {
            "click .panel-heading": "return_to_settings",
            "click .btn-cancel": "return_to_settings",
            "submit form.param-edit-form": "edit_attribute",
        },
        initialize: function(options) {
            EditParameterView.__super__.initialize.apply(this);

            this.topNavVisible = "inherit";
            this.sideNavVisible = "inherit";

            if (!_.isUndefined(options)) {
                if (!_.isUndefined(options.param)) {
                    this.param = options.param;
                } else {
                    Backbone.history.navigate("default", {replace: true});
                }

                if (_.isFunction(options.navigateToSettings)) {
                    this.navigateToSettings = options.navigateToSettings;
                }

                if (_.isFunction(options.editParamSuccess)) {
                    this.editParamSuccess = options.editParamSuccess;
                }
            }
        },
        render: function() {
            var self = this,
                data,
                currentVal,
                properties
            ;

            if (!_.contains(_.keys(self.model.editableProperties), self.param)) {
                $.notify({message:"This parameter is not editable"},{type:"danger"});
                // Don't want to create a history entry - back button should work
                Backbone.history.navigate("default", {replace: true});
                return;
            }

            currentVal = self.model.toJSON().data[self.param];
            properties = self.model.editableProperties[self.param];

            data = _.extend({},
                self.model.toJSON(),
                {
                    param: self.param,
                    propertyName: properties.name,
                    currentVal: currentVal,
                }
            );

            switch (properties.type) {
                case "str":
                    self.$el.html(ich.param_edit_str(data));
                    break;
                case "bool":
                    self.$el.html(ich.param_edit_bool(data));
                    break;
                default:
                    console.log("Template error type " + properties.type);
            }
            return this;
        },
        return_to_settings: function(e) {
            var self = this;

            e.preventDefault();
            e.stopPropagation();

            return self.navigate_to_settings();
        },
        navigate_to_settings: function(e) {
            var self = this;

            if (_.isFunction(self.navigateToSettings)) {
                self.navigateToSettings();
            } else {
                return Backbone.history.navigate("home", {trigger: true});
            }
        },
        edit_attribute: function(e) {
            var self = this,
                newVal,
                currentVal,
                propertyName,
                propertyType,
                success,
                error,
                updateObj
            ;

            e.preventDefault();
            e.stopPropagation();

            success = function(collection, response, opts) {
                $.notify({message: propertyName + " successfully updated"}, {type:"success"});

                if (_.isFunction(self.editParamSuccess)) {
                    self.editParamSuccess();
                }

                return self.navigate_to_settings();
            };
            error = function(collection, response, opts) {
                $.notify({message:"Error setting " + propertyName},{type: "danger"});
                return self.navigate_to_settings();
            };

            propertyName = self.model.editableProperties[self.param].name;
            propertyType = self.model.editableProperties[self.param].type;
            currentVal = self.model.toJSON().data[self.param];

            if (propertyType === "bool") {
                newVal = !currentVal;
            } else {
                newVal = $("#param-edit-str").val();
            }
            if (newVal === currentVal) {
                $.notify(propertyName + " not updated");
                return self.navigate_to_settings();
            }
            // update the model
            updateObj = {};
            updateObj[self.param] = newVal;

            self.model.save(
                updateObj,
                {success: success, error: error, patch: true}
            );

        },
    });

    root.App.Views.Components.EditParameterView = EditParameterView;

})(this);
