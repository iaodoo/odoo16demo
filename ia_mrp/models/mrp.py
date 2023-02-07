from odoo import models, api, fields, _
from odoo.tools.misc import format_date

# ====================================================================================
# Description

# Product – Select a service product (overheads or Labour).
# This will give the flexibility to add more labour/service components as standard costs to the BoM.
# Only Service Products will be allowed to be selected here.

# Standard Cost – By default, the Cost of the product selected will be picked up, with the option to override.
# ====================================================================================


class IaMrpCost(models.Model):
    _name = 'ia.mrp.cost'
    _description = "Capture Costs in BoM"

    product_id = fields.Many2one(
        'product.product', string='Product', domain="[('type','=','service')]")
    standard_cost = fields.Float(string='Standard Cost', digits=(12, 4))
    name = fields.Char(string='Description')
    bom_id = fields.Many2one('mrp.bom', string='BOM')

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.name
            self.standard_cost = self.product_id.standard_price


class IaMrpBom(models.Model):
    _inherit = 'mrp.bom'

    #@api.depends('cost_line_ids.standard_cost','bom_line_ids.labour_cost')
    def _compute_amount(self):
        for bom in self:
            labour_cost = 0.0
            for cost in bom.cost_line_ids:
                labour_cost = labour_cost + (cost.standard_cost)
            for cost in bom.bom_line_ids:
                labour_cost = labour_cost + (cost.labour_cost)
            bom.labour_cost = labour_cost
            bom.total_cost = labour_cost + bom.product_id.standard_price

    labour_cost = fields.Float(
        string='Total Labour Cost', store=False, compute='_compute_amount')
    total_cost = fields.Float(
        string='Total Cost', store=False,  compute='_compute_amount')
    cost_line_ids = fields.One2many(
        'ia.mrp.cost', 'bom_id', 'Cost Lines', copy=True)


class IaMrpBomLine(models.Model):
    _inherit = 'mrp.bom.line'

    labour_cost = fields.Float(
        string='Total Labour Cost', store=False, compute='_compute_amount')

    # @api.depends('product_id.bom_ids.labour_cost', 'product_qty', 'bom_id.cost_line_ids.standard_cost')
    def _compute_amount(self):
        for bomline in self:
            labour_cost = 0.0
            if len(bomline.product_id.bom_ids) > 1:
                labour_cost = bomline.product_id.bom_ids[0].labour_cost * bomline.product_qty 
            else:
                labour_cost = bomline.product_id.bom_ids.labour_cost * bomline.product_qty            
            bomline.labour_cost = labour_cost
            
# 2. Analytic Account in MO
# Introduce a new field Analytic Account in Manufacturing Order under the Miscellaneous tab.


class IaMrpProd(models.Model):
    _inherit = 'mrp.production'
    cost_line_ids = fields.One2many(
        'ia.mrp.prod.cost', 'production_id', 'Cost Lines', copy=True)
    cost_move_id = fields.Many2one(
        'account.move', string='Journal Entry', readonly=True, copy=False)
    account_analytic_id = fields.Many2one(
        'account.analytic.account', string='Analytic Account', readonly=False, states={'done': [('readonly', True)]})
    analytic_tag_ids = fields.Many2many(
        'account.analytic.tag', string='Tags', readonly=False, states={'done': [('readonly', True)]})

    @api.onchange('bom_id')
    def _onchange_bomid(self):
        if self.bom_id:
            cost_values = []
            self.cost_line_ids.unlink()
            for line in self.bom_id.cost_line_ids:
                vals = {
                    'product_id': line.product_id.id,
                    'name': line.name,
                    'standard_cost': line.standard_cost,
                    'actual_cost': line.standard_cost,
                }
                cost_values.append((0, 0, vals))
            if cost_values:
                self.cost_line_ids = cost_values

    def cost_journal(self):
        for ord in self:
            if ord.cost_line_ids.ids:
                cost_values = []
                for line in ord.cost_line_ids:
                    invoice_line_vals = {}
                    invoice_line_vals['debit'] = line.actual_cost
                    invoice_line_vals['credit'] = 0
                    invoice_line_vals['analytic_account_id'] = ord.account_analytic_id and ord.account_analytic_id.id or False
                    # and  [(6, 0,[ord.analytic_tag_id.id])]  or False
                    invoice_line_vals['analytic_tag_ids'] = ord.analytic_tag_ids
                    invoice_line_vals['name'] = ord.name + " - " + line.name
                    invoice_line_vals['account_id'] = line.product_id.categ_id.property_stock_account_output_categ_id.id
                    cost_values.append((0, 0, invoice_line_vals))

                    invoice_line_vals = {}
                    invoice_line_vals['credit'] = line.actual_cost
                    invoice_line_vals['debit'] = 0
                    invoice_line_vals['analytic_account_id'] = ord.account_analytic_id and ord.account_analytic_id.id or False
                    # and  [(6, 0,[ord.analytic_tag_id.id])]  or False
                    invoice_line_vals['analytic_tag_ids'] = ord.analytic_tag_ids
                    invoice_line_vals['name'] = ord.name + " - " + line.name
                    invoice_line_vals['account_id'] = line.product_id.categ_id.property_stock_account_input_categ_id.id
                    cost_values.append((0, 0, invoice_line_vals))

                if cost_values:
                    invoice = {}
                    invoice = {'date': ord.date_planned_start,
                               'journal_id': ord.product_id.categ_id.property_stock_journal.id,
                               'ref':  str(ord.name) + "- Labour and Overheads",
                               'line_ids': cost_values}
                    invoice_id = self.env['account.move'].create(invoice)
                    ord.write({'cost_move_id': invoice_id.id})
                    invoice_id.action_post()

    # The costs will automatically be updated based on the quantity of finished goods being produced.

    @api.onchange('qty_producing')
    def _onchange_qty_producing(self):
        if self.qty_producing:
            if self.cost_line_ids.ids:
                for line in self.cost_line_ids:
                    line.actual_cost = line.standard_cost * self.qty_producing

    def _button_mark_done_sanity_checks(self):
        super(IaMrpProd, self)._button_mark_done_sanity_checks
        if not self.cost_move_id:
            self.cost_journal()

    @api.model
    def create(self, values):
        production = super(IaMrpProd, self).create(values)
        if values.get('bom_id', False):
            production._onchange_bomid()            
        return production
        

# 2. Automate Costs in Manufacturing Order
# When a new manufacturing order is created and confirmed, the costs are automatically calculated based on the costs defined in the BoM.


class IaMrpProdCost(models.Model):
    _name = 'ia.mrp.prod.cost'
    _description = "Capture Costs in Production"

    product_id = fields.Many2one(
        'product.product', string='Product', domain="[('type','=','service')]")
    standard_cost = fields.Float(string='Standard Cost1', digits=(12, 4))
    name = fields.Char(string='Description')
    production_id = fields.Many2one('mrp.production', string='MRP')
    actual_cost = fields.Float(string='Standard Cost', digits=(12, 4))

    @api.onchange('product_id')
    def _onchange_product_id(self):
        if self.product_id:
            self.name = self.product_id.name
            self.standard_cost = self.product_id.standard_price


# Once the MO is completed, there are 2 impacts occurring – Stock Movements and Accounting Journals. The Analytic Account,
#  if selected in the MO, will be populated into the accounting journals.
class IaStockMove(models.Model):
    _inherit = 'stock.move'

    def _generate_valuation_lines_data(self, partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description):
        res = super(IaStockMove, self)._generate_valuation_lines_data(
            partner_id, qty, debit_value, credit_value, debit_account_id, credit_account_id, description)
        if res and self.production_id:
            res['debit_line_vals']['analytic_account_id'] = self.production_id.account_analytic_id and self.production_id.account_analytic_id.id or False
            res['credit_line_vals']['analytic_account_id'] = self.production_id.account_analytic_id and self.production_id.account_analytic_id.id or False
            # and  [(6, 0,[self.production_id.analytic_tag_id.id])]  or False
            res['debit_line_vals']['analytic_tag_ids'] = self.production_id.analytic_tag_ids
            # and  [(6, 0,[self.production_id.analytic_tag_id.id])]  or False
            res['credit_line_vals']['analytic_tag_ids'] = self.production_id.analytic_tag_ids

        if res and self.raw_material_production_id:
            res['debit_line_vals']['analytic_account_id'] = self.raw_material_production_id.account_analytic_id and self.raw_material_production_id.account_analytic_id.id or False
            res['credit_line_vals']['analytic_account_id'] = self.raw_material_production_id.account_analytic_id and self.raw_material_production_id.account_analytic_id.id or False
            # and  [(6, 0,[self.production_id.analytic_tag_id.id])]  or False
            res['debit_line_vals']['analytic_tag_ids'] = self.raw_material_production_id.analytic_tag_ids
            # and  [(6, 0,[self.production_id.analytic_tag_id.id])]  or False
            res['credit_line_vals']['analytic_tag_ids'] = self.raw_material_production_id.analytic_tag_ids

        return res
