// product_bundle_all js
odoo.define('bi_manual_currency_exchange_rate.reconciliation_renderer', function (require) {
"use strict";




var Widget = require('web.Widget');
var FieldManagerMixin = require('web.FieldManagerMixin');
var relational_fields = require('web.relational_fields');
var ReconciliationRenderer = require('account.ReconciliationRenderer');
var ReconciliationModel = require('account.ReconciliationModel');
var basic_fields = require('web.basic_fields');
var core = require('web.core');
var time = require('web.time');
var session = require('web.session');
var qweb = core.qweb;
var _t = core._t;
var field_utils = require('web.field_utils');
var utils = require('web.utils');






ReconciliationRenderer.LineRenderer.include({

    /**
     * create account_id, tax_ids, analytic_account_id, analytic_tag_ids, name and amount fields
     *
     * @private
     * @param {object} state - statement line
     * @returns {Promise}
     */
    _renderCreate: function (state) {
        var self = this;

        return this.model.makeRecord('account.bank.statement.line', [{
            relation: 'account.account',
            type: 'many2one',
            name: 'account_id',
            domain: [['company_id', '=', state.st_line.company_id], ['deprecated', '=', false]],
        }, {
            relation: 'account.journal',
            type: 'many2one',
            name: 'journal_id',
            domain: [['company_id', '=', state.st_line.company_id]],
        }, {
            relation: 'account.tax',
            type: 'many2many',
            name: 'tax_ids',
            domain: [['company_id', '=', state.st_line.company_id]],
        }, {
            relation: 'account.analytic.account',
            type: 'many2one',
            name: 'analytic_account_id',
        }, {
            relation: 'account.analytic.tag',
            type: 'many2many',
            name: 'analytic_tag_ids',
        }, {
            type: 'boolean',
            name: 'force_tax_included',
        }, {
            type: 'char',
            name: 'name',
        }, {
            type: 'float',
            name: 'amount',
        },{
            type: 'float',
            name: 'manual_currency_rate',
        }, {
            type: 'char', //TODO is it a bug or a feature when type date exists ?
            name: 'date',
        }, {
            type: 'boolean',
            name: 'to_check',
        }], {
            account_id: {
                string: _t("Account"),
            },
            name: {string: _t("Label")},
            amount: {string: _t("Account")},
        }).then(function (recordID) {
            self.handleCreateRecord = recordID;
            var record = self.model.get(self.handleCreateRecord);

            self.fields.account_id = new relational_fields.FieldMany2One(self,
                'account_id', record, {mode: 'edit', attrs: {can_create:false}});

            self.fields.journal_id = new relational_fields.FieldMany2One(self,
                'journal_id', record, {mode: 'edit'});

            self.fields.tax_ids = new relational_fields.FieldMany2ManyTags(self,
                'tax_ids', record, {mode: 'edit', additionalContext: {append_type_to_tax_name: true}});

            self.fields.analytic_account_id = new relational_fields.FieldMany2One(self,
                'analytic_account_id', record, {mode: 'edit'});

            self.fields.analytic_tag_ids = new relational_fields.FieldMany2ManyTags(self,
                'analytic_tag_ids', record, {mode: 'edit'});

            self.fields.force_tax_included = new basic_fields.FieldBoolean(self,
                'force_tax_included', record, {mode: 'edit'});

            self.fields.name = new basic_fields.FieldChar(self,
                'name', record, {mode: 'edit'});

            self.fields.amount = new basic_fields.FieldFloat(self,
                'amount', record, {mode: 'edit'});

            self.fields.manual_currency_rate = new basic_fields.FieldFloat(self,
                'manual_currency_rate', record, {mode: 'edit'});

            self.fields.date = new basic_fields.FieldDate(self,
                'date', record, {mode: 'edit'});

            self.fields.to_check = new basic_fields.FieldBoolean(self,
                'to_check', record, {mode: 'edit'});

            var $create = $(qweb.render("reconciliation.line.create", {'state': state, 'group_tags': self.group_tags, 'group_acc': self.group_acc}));
            self.fields.account_id.appendTo($create.find('.create_account_id .o_td_field'))
                .then(addRequiredStyle.bind(self, self.fields.account_id));
            self.fields.journal_id.appendTo($create.find('.create_journal_id .o_td_field'));
            self.fields.tax_ids.appendTo($create.find('.create_tax_id .o_td_field'));
            self.fields.analytic_account_id.appendTo($create.find('.create_analytic_account_id .o_td_field'));
            self.fields.analytic_tag_ids.appendTo($create.find('.create_analytic_tag_ids .o_td_field'));
            self.fields.force_tax_included.appendTo($create.find('.create_force_tax_included .o_td_field'));
            self.fields.name.appendTo($create.find('.create_label .o_td_field'))
                .then(addRequiredStyle.bind(self, self.fields.name));
            self.fields.amount.appendTo($create.find('.create_amount .o_td_field'))
                .then(addRequiredStyle.bind(self, self.fields.amount));
            self.fields.manual_currency_rate.appendTo($create.find('.create_manual_currency_rate .o_td_field'))
                .then(addRequiredStyle.bind(self, self.fields.manual_currency_rate));
            self.fields.date.appendTo($create.find('.create_date .o_td_field'));
            self.fields.to_check.appendTo($create.find('.create_to_check .o_td_field'));
            self.$('.create').append($create);

            function addRequiredStyle(widget) {
                widget.$el.addClass('o_required_modifier');
            }
        });
    },   


    });
    
        ReconciliationModel.StatementModel.include({

            quickCreateFields: ['account_id', 'amount', 'analytic_account_id', 'name', 'tax_ids', 'force_tax_included', 'analytic_tag_ids', 'to_check', 'manual_currency_rate'],

            init: function (parent, options) {
                var self = this;

                this._super.apply(this, arguments);
            },
        updateProposition: function (handle, values) {
            var self = this;
            var line = this.getLine(handle);
            line.manual_currency_rate = values.manual_currency_rate
            var prop = _.last(_.filter(line.reconciliation_proposition, '__focus'));
            if ('to_check' in values && values.to_check === false) {
                // check if we have another line with to_check and if yes don't change value of this proposition
                prop.to_check = line.reconciliation_proposition.some(function(rec_prop, index) {
                    return rec_prop.id !== prop.id && rec_prop.to_check;
                });
            }
            if (!prop) {
                prop = this._formatQuickCreate(line);
                line.reconciliation_proposition.push(prop);
            }
            _.each(values, function (value, fieldName) {
                if (fieldName === 'analytic_tag_ids') {
                    switch (value.operation) {
                        case "ADD_M2M":
                            // handle analytic_tag selection via drop down (single dict) and
                            // full widget (array of dict)
                            var vids = _.isArray(value.ids) ? value.ids : [value.ids];
                            _.each(vids, function (val) {
                                if (!_.findWhere(prop.analytic_tag_ids, {id: val.id})) {
                                    prop.analytic_tag_ids.push(val);
                                }
                            });
                            break;
                        case "FORGET":
                            var id = self.localData[value.ids[0]].ref;
                            prop.analytic_tag_ids = _.filter(prop.analytic_tag_ids, function (val) {
                                return val.id !== id;
                            });
                            break;
                    }
                }
                else if (fieldName === 'tax_ids') {
                    switch(value.operation) {
                        case "ADD_M2M":
                            prop.__tax_to_recompute = true;
                            var vids = _.isArray(value.ids) ? value.ids : [value.ids];
                            _.each(vids, function(val){
                                if (!_.findWhere(prop.tax_ids, {id: val.id})) {
                                    value.ids.price_include = self.taxes[val.id] ? self.taxes[val.id].price_include : false;
                                    prop.tax_ids.push(val);
                                }
                            });
                            break;
                        case "FORGET":
                            prop.__tax_to_recompute = true;
                            var id = self.localData[value.ids[0]].ref;
                            prop.tax_ids = _.filter(prop.tax_ids, function (val) {
                                return val.id !== id;
                            });
                            break;
                    }
                }
                else {
                    prop[fieldName] = values[fieldName];
                }
            });
            if ('account_id' in values) {
                prop.account_code = prop.account_id ? this.accounts[prop.account_id.id] : '';
            }
            if ('amount' in values) {
                prop.base_amount = values.amount;
            }
            if ('force_tax_included' in values || 'amount' in values || 'account_id' in values) {
                prop.__tax_to_recompute = true;
            }
            line.createForm = _.pick(prop, this.quickCreateFields);
            // If you check/uncheck the force_tax_included box, reset the createForm amount.
            if(prop.base_amount)
                line.createForm.amount = prop.base_amount;
            if (!prop.tax_ids || prop.tax_ids.length !== 1 ) {
                // When we have 0 or more than 1 taxes, reset the base_amount and force_tax_included, otherwise weird behavior can happen
                prop.amount = prop.base_amount;
                line.createForm.force_tax_included = false;
            }
            return this._computeLine(line);
        },
        /**
         * Format the value and send it to 'account.reconciliation.widget' model
         * Update the number of validated lines
         * overridden in ManualModel
         *
         * @param {(string|string[])} handle
         * @returns {Promise<Object>} resolved with an object who contains
         *   'handles' key
         */
        validate: function (handle) {
            var self = this;
            this.display_context = 'validate';
            var handles = [];
            if (handle) {
                handles = [handle];
            } else {
                _.each(this.lines, function (line, handle) {
                    if (!line.reconciled && line.balance && !line.balance.amount && line.reconciliation_proposition.length) {
                        handles.push(handle);
                    }
                });
            }
            var ids = [];
            var values = [];
            var handlesPromises = [];
            _.each(handles, function (handle) {
                var line = self.getLine(handle);
                var props = _.filter(line.reconciliation_proposition, function (prop) {return !prop.invalid;});
                var computeLinePromise;
                if (props.length === 0) {
                    
                    // Usability: if user has not chosen any lines and click validate, it has the same behavior
                    // as creating a write-off of the same amount.
                    props.push(self._formatQuickCreate(line, {
                        account_id: [line.st_line.open_balance_account_id, self.accounts[line.st_line.open_balance_account_id]],
                    }));
                    // update balance of line otherwise it won't be to zero and another line will be added
                    line.reconciliation_proposition.push(props[0]);
                    computeLinePromise = self._computeLine(line);
                }
                ids.push(line.id);
                handlesPromises.push(Promise.resolve(computeLinePromise).then(function() {
                    var move_line_values = _.map(_.filter(props, function (prop) {
                        return !isNaN(prop.id) && !prop.is_liquidity_line;
                    }), self._formatToProcessReconciliation.bind(self, line));
                    move_line_values.push(..._.map(_.filter(props, function (prop) {
                        return !isNaN(prop.id) && prop.is_liquidity_line;
                    }), self._formatToProcessReconciliation.bind(self, line)))
                    move_line_values.push(..._.map(_.filter(props, function (prop) {
                        return isNaN(prop.id) && prop.display;
                    }), self._formatToProcessReconciliation.bind(self, line)))
                    values.push({
                        partner_id: line.st_line.partner_id,
                        manual_currency_rate:line.manual_currency_rate,
                        lines_vals_list: move_line_values,
                        to_check: line.to_check,
                    });
                    line.reconciled = true;
                    self.valuenow++;
                }));

                _.each(self.lines, function(other_line) {
                    if (other_line != line) {
                        var filtered_prop = other_line.reconciliation_proposition.filter(p => !line.reconciliation_proposition.map(l => l.id).includes(p.id));
                        if (filtered_prop.length != other_line.reconciliation_proposition.length) {
                            other_line.need_update = true;
                            other_line.reconciliation_proposition = filtered_prop;
                        }
                        self._computeLine(line);
                    }
                })
            });

            return Promise.all(handlesPromises).then(function() {
                return self._rpc({
                        model: 'account.reconciliation.widget',
                        method: 'process_bank_statement_line',
                        args: [ids, values],
                        context: self.context,
                    })
                    .then(self._validatePostProcess.bind(self))
                    .then(function () {
                        return {handles: handles};
                    });
            });
        },


        _formatToProcessReconciliation: function (line, prop) {
            var amount = -prop.amount;
            if (prop.partial_amount) {
                amount = -prop.partial_amount;
            }

            var result = {
                name : prop.name,
                balance : amount,
                tax_exigible: prop.tax_exigible,
                manual_currency_rate :prop.manual_currency_rate,
                analytic_tag_ids: [[6, null, _.pluck(prop.analytic_tag_ids, 'id')]]
            };
            if (!isNaN(prop.id)) {
                result.id = prop.id;
            } else {
                result.account_id = prop.account_id.id;
                if (prop.journal_id) {
                    result.journal_id = prop.journal_id.id;
                }
            }
            if (prop.analytic_account_id) result.analytic_account_id = prop.analytic_account_id.id;
            if (prop.tax_ids && prop.tax_ids.length) result.tax_ids = [[6, null, _.pluck(prop.tax_ids, 'id')]];
            if (prop.tax_tag_ids && prop.tax_tag_ids.length) result.tax_tag_ids = [[6, null, _.pluck(prop.tax_tag_ids, 'id')]];
            if (prop.tax_repartition_line_id) result.tax_repartition_line_id = prop.tax_repartition_line_id;
            if (prop.reconcile_model_id) result.reconcile_model_id = prop.reconcile_model_id
            if (prop.currency_id) result.currency_id = prop.currency_id;
            return result;
        },
        _computeLine: function (line) {
            //balance_type
            var self = this;

            // compute taxes
            var tax_defs = [];
            var reconciliation_proposition = [];
            var formatOptions = {
                currency_id: line.st_line.currency_id,
            };
            line.to_check = false;
            _.each(line.reconciliation_proposition, function (prop) {
                if (prop.to_check) {
                    // If one of the proposition is to_check, set the global to_check flag to true
                    line.to_check = true;
                }
                if (prop.tax_repartition_line_id) {
                    if (!_.find(line.reconciliation_proposition, {'id': prop.link}).__tax_to_recompute) {
                        reconciliation_proposition.push(prop);
                    }
                    prop.amount_str = field_utils.format.monetary(Math.abs(prop.amount), {}, formatOptions);
                    return;
                }
                if (!prop.is_liquidity_line && parseInt(prop.id)) {
                    prop.is_move_line = true;
                }
                reconciliation_proposition.push(prop);

                if (prop.tax_ids && prop.tax_ids.length && prop.__tax_to_recompute && prop.base_amount) {
                    var args = [prop.tax_ids.map(function(el){return el.id;}), prop.base_amount, formatOptions.currency_id];
                    var add_context = {'round': true};
                    if(prop.tax_ids.length === 1 && line.createForm.force_tax_included)
                        add_context.force_price_include = true;
                    tax_defs.push(self._rpc({
                            model: 'account.tax',
                            method: 'json_friendly_compute_all',
                            args: args,
                            context: $.extend({}, self.context || {}, add_context),
                        })
                        .then(function (result) {
                            _.each(result.taxes, function(tax){
                                var tax_prop = self._formatQuickCreate(line, {
                                    'link': prop.id,
                                    'tax_ids': tax.tax_ids,
                                    'tax_repartition_line_id': tax.tax_repartition_line_id,
                                    'tax_tag_ids': tax.tag_ids,
                                    'amount': tax.amount,
                                    'manual_currency_rate':prop.manual_currency_rate,
                                    'name': prop.name ? prop.name + " " + tax.name : tax.name,
                                    'date': prop.date,
                                    'account_id': tax.account_id ? [tax.account_id, null] : prop.account_id,
                                    'analytic': tax.analytic,
                                    '__focus': false
                                });

                                prop.tax_exigible = tax.tax_exigibility === 'on_payment' ? true : undefined;
                                prop.amount = tax.base;
                                prop.amount_str = field_utils.format.monetary(Math.abs(prop.amount), {}, formatOptions);
                                prop.invalid = !self._isValid(prop);

                                tax_prop.amount_str = field_utils.format.monetary(Math.abs(tax_prop.amount), {}, formatOptions);
                                tax_prop.invalid = prop.invalid;

                                reconciliation_proposition.push(tax_prop);
                            });

                            prop.tax_tag_ids = self._formatMany2ManyTagsTax(result.base_tags || []);
                        }));
                } else {
                    prop.amount_str = field_utils.format.monetary(Math.abs(prop.amount), {}, formatOptions);
                    prop.display = self._isDisplayedProposition(prop);
                    prop.invalid = !self._isValid(prop);
                }
            });

            return Promise.all(tax_defs).then(function () {
                _.each(reconciliation_proposition, function (prop) {
                    prop.__tax_to_recompute = false;
                });
                line.reconciliation_proposition = reconciliation_proposition;

                var amount_currency = 0;
                var total = line.st_line.amount || 0;
                var isOtherCurrencyId = _.uniq(_.pluck(_.reject(reconciliation_proposition, 'invalid'), 'currency_id'));
                isOtherCurrencyId = isOtherCurrencyId.length === 1 && !total && isOtherCurrencyId[0] !== formatOptions.currency_id ? isOtherCurrencyId[0] : false;

                _.each(reconciliation_proposition, function (prop) {
                    if (!prop.invalid) {
                        total -= prop.partial_amount || prop.amount;
                        if (isOtherCurrencyId) {
                            amount_currency -= (prop.amount < 0 ? -1 : 1) * Math.abs(prop.amount_currency);
                        }
                    }
                });
                var company_currency = session.get_currency(line.st_line.currency_id);
                var company_precision = company_currency && company_currency.digits[1] || 2;
                total = utils.round_decimals(total, company_precision) || 0;
                if(isOtherCurrencyId){
                    var other_currency = session.get_currency(isOtherCurrencyId);
                    var other_precision = other_currency && other_currency.digits[1] || 2;
                    amount_currency = utils.round_decimals(amount_currency, other_precision);
                }
                line.balance = {
                    amount: total,
                    amount_str: field_utils.format.monetary(Math.abs(total), {}, formatOptions),
                    currency_id: isOtherCurrencyId,
                    amount_currency: isOtherCurrencyId ? amount_currency : total,
                    amount_currency_str: isOtherCurrencyId ? field_utils.format.monetary(Math.abs(amount_currency), {}, {
                        currency_id: isOtherCurrencyId
                    }) : false,
                    account_code: self.accounts[line.st_line.open_balance_account_id],
                };
                line.balance.show_balance = line.balance.amount_currency != 0;
                line.balance.type = line.balance.amount_currency ? (line.st_line.partner_id ? 0 : -1) : 1;
            });
        },


    });
    
});



        