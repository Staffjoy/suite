(function(root) {

    "use strict";

    var Views = root.App.Views;

    var SpreadsheetView = Views.Base.extend({
        el: ".spreadsheet-placeholder",
        events: {
            "change .spreadsheet-cell": "applySelectiveColoring",
        },
        initialize: function(opts) {
            SpreadsheetView.__super__.initialize.apply(this);

            if (!_.isUndefined(opts)) {

                if (!_.isUndefined(opts.el)) {
                    this.el = opts.el;
                }

                if (!_.isUndefined(opts.roleId)) {
                    this.roleId = opts.roleId;
                }

                if (!_.isUndefined(opts.graphLabel)) {
                    this.graphLabel = opts.graphLabel;
                }

                if (!_.isUndefined(opts.disabled)) {
                    this.disabled = opts.disabled;
                } else {
                    this.disabled = false;
                }

                if (!_.isUndefined(opts.data)) {
                    this.data = opts.data;
                    this.width = opts.data.length;
                    this.height = opts.data[0].demand.length;
                }
            }
        },
        render: function(opts) {
            var self = this,
                data = {
                    roleId: self.roleId,
                },
                labelData = {
                    labels: self.graphLabel,
                },
                appendEl = ".spreadsheet-" + self.roleId,
                container,
                hot
            ;

            self.$el.append(ich.spreadsheet(data));

            self.maxValue = _.chain(self.data).pluck('demand').flatten().max().valueOf();

            container = _.first($(appendEl));
            hot = new Handsontable(container, {
                afterSelection: function(r, c, r2, c2) {
                    hot.render();
                },
                allowEmpty: false,
                allowInvalid: false,
                allowRemoveColumn: false,
                allowRemoveRow: false,
                beforeChangeRender: function(changes, source) {
                    self.maxValue = _.chain(hot.getData()).flatten().max().valueOf();
                },
                colHeaders: _.map(self.data, function(data) {
                    return data.name + '<br/>' + data.day;
                }),
                columns: _.map(_.range(7), function(value) {
                    var that = this;
                    return {
                        editor: (function() {
                            var editor = Handsontable.editors.NumericEditor.prototype.extend();

                            editor.prototype.prepare = function(row, col, prop, td, cellProperties) {
                                Handsontable.editors.NumericEditor.prototype.prepare.apply(this, arguments);

                                td.style.background = '';
                            };

                            return editor;
                        })(),
                        renderer: function(hotInstance, TD, row, col, prop, value, cellProperties) {
                            Handsontable.renderers.NumericRenderer.apply(this, arguments);
                            var opacity = self.maxValue === 0 ? 0 : value / self.maxValue;

                            TD.className += ' htNumeric';
                            TD.style.background = "rgba(163, 219, 213, " + opacity + " )";
                            TD.innerHTML = Handsontable.helper.stringify(value);
                        },
                        type: 'numeric',
                        validator: function(value, callback) {
                            if (Number.isInteger(value) && value >= 0) {
                                callback(true);
                            } else {
                                callback(false);
                            }
                        },
                    };
                }),
                colWidths: 100,
                data: _.zip.apply(_, _.map(self.data, function(data) {
                    return data.demand;
                })),
                maxCols: 7,
                maxRows: 24,
                rowHeaders: function(index) {
                    return self.graphLabel[index];
                },
                rowHeaderWidth: 100,
            });

            window.hot = hot;

            self.hot = hot;

            return this;
        },
        getSpreadsheetData: function() {
            var self = this;

            return _.object(
                _.map(self.data, function(data) {
                    return data.name.toLowerCase();
                }),
                _.zip.apply(_, self.hot.getData())
            );
        },
        setSpreadsheetData: function(data) {
            var self = this,
                header = _.map(self.data, function(data) { return data.name.toLowerCase(); })
            ;

            _.each(data, function(values, key) {
                var col = header.indexOf(key);
                _.each(values, function(value, row) {
                    self.hot.setDataAtCell(row, col, value);
                });
            });
        },
    });

    root.App.Views.Components.SpreadsheetView = SpreadsheetView;

})(this);
