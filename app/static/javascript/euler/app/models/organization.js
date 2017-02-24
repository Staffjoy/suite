(function(root) {

    "use strict";

    var Models = root.App.Models,
        Organization = Models.Base.extend({
            endpoint: "organizations",
            editableProperties: {
                name: {type: "str", name: "Name"},
                active: {type: "bool", name: "Active"},
                enable_shiftplanning_export: {type: "bool", name: "Show ShiftPlanning CSV Download Button in Manage App"},
                enable_timeclock_default: {type: "bool", name: "Enable Timeclock"},
                early_access: {type: "bool", name: "Early Access"},
                trial_days: {type: "int", name: "Trial Days"},
                paid_until: {type: "date", name: "Paid Until"},
                enterprise_access: {type: "bool", name: "Enterprise Access"},
            },
        })
    ;

    root.App.Models.Organization = Organization;
})(this);
