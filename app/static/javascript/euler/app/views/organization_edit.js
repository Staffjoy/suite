(function(root) {

    "use strict";

    var Util = root.App.Util,
        Views = root.App.Views,
        Models = root.App.Models
    ;

    var OrganizationEditView = Views.Base.extend({
        el: "#euler-container",
        events: {
            "click .panel-footer": "return_to_organization",
            "click .panel-heading": "return_to_organization",
            "submit form.organization-edit-form": "edit_attribute",
        },
        initialize: function(options) {
            OrganizationEditView.__super__.initialize.apply(this);
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
                    self.$el.html(ich.organization_edit_str(data));
                    break;
                case "bool":
                    self.$el.html(ich.organization_edit_bool(data));
                    break;
                case "int":
                    self.$el.html(ich.organization_edit_int(data));
                    break;
                case "date":
                    var date = self.model.get('data')[self.param];
                    self.$el.html(ich.organization_edit_date(data));
                    self.datetimepicker = $('#organization-edit-date').datetimepicker({
                        date: !!date ? date : moment.utc(),
                        format: 'hh:mm:ss A  MM-DD-YYYY',
                    });
                    break;
                default:
                    console.log("Template error type " + properties.type);
            }
            return this;
        },
        return_to_organization: function(e) {
            var self = this;

            e.preventDefault();
            e.stopPropagation();
            this.undelegateEvents();

            return self.navigate_to_organization();
        },
        navigate_to_organization: function() {
            var id = this.model.get("id");
            return Backbone.history.navigate("organizations/" + id, {trigger: true});
        },
        edit_attribute: function(e) {
            var newVal,
                currentVal,
                propertyName,
                propertyType,
                success,
                error,
                updateObj = {},
                self = this
            ;

            e.preventDefault();
            e.stopPropagation();

            success = function(collection, response, opts) {
                $.notify({message: propertyName + " successfully updated"}, {type:"success"});
                return self.navigate_to_organization();
            };
            error = function(collection, response, opts) {
                $.notify({message:"Error setting " + propertyName},{type: "danger"});
                return self.navigate_to_organization();
            };

            propertyName = self.model.editableProperties[self.param].name;
            propertyType = self.model.editableProperties[self.param].type;
            currentVal = self.model.toJSON().data[self.param];

            if (propertyType === "bool") {
                newVal = !currentVal;
            } else if (propertyType === "date") {
                newVal = moment.utc($("#organization-edit-date").val()).format();
            } else {
                newVal = $("#organization-edit-str").val();
            }
            if (newVal === currentVal) {
                $.notify(propertyName + " not updated");
                return self.return_to_organization();
            }
            // update the model
            updateObj[self.param] = newVal;
            self.model.save(
                updateObj,
                {success: success, error: error, patch: true}
            );

        },
    });

    root.App.Views.OrganizationEditView = OrganizationEditView;

})(this);
