(function(root) {

    "use strict";

    var Util = root.App.Util,
        Views = root.App.Views,
        Models = root.App.Models
    ;

    var UserEditView = Views.Base.extend({
        el: "#euler-container",
        events: {
            "click .panel-footer": "return_to_user",
            "click .panel-heading": "return_to_user",
            "submit form.user-edit-form": "edit_attribute",
        },
        initialize: function(options) {
            UserEditView.__super__.initialize.apply(this);
            this.param = options.param;
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
                Backbone.history.navigate("home", {replace: true});
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
                    self.$el.html(ich.user_edit_str(data));
                    break;
                case "bool":
                    self.$el.html(ich.user_edit_bool(data));
                    break;
                default:
                    console.log("Template error type " + properties.type);
            }
            return this;
        },
        return_to_user: function(e) {
            var self = this;

            e.preventDefault();
            e.stopPropagation();
            this.undelegateEvents();

            return self.navigate_to_user();
        },
        navigate_to_user: function() {
            var id = this.model.get("id");
            return Backbone.history.navigate("users/" + id, {trigger: true});
        },
        edit_attribute: function(e) {
            var newVal,
                currentVal,
                propertyName,
                propertyType,
                success,
                error,
                updateObj,
                self = this
            ;

            e.preventDefault();
            e.stopPropagation();

            success = function(collection, response, opts) {
                $.notify({message: propertyName + " successfully updated"}, {type:"success"});
                return self.navigate_to_user();
            };
            error = function(collection, response, opts) {
                $.notify({message:"Error setting " + propertyName},{type: "danger"});
                return self.navigate_to_user();
            };

            propertyName = self.model.editableProperties[self.param].name;
            propertyType = self.model.editableProperties[self.param].type;
            currentVal = self.model.toJSON().data[self.param];

            if (propertyType === "bool") {
                newVal = !currentVal;
            } else {
                newVal = $("#user-edit-str").val();
            }
            if (newVal === currentVal) {
                $.notify(propertyName + " not updated");
                return self.return_to_user();
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

    root.App.Views.UserEditView = UserEditView;

})(this);
