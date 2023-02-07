from odoo import models, api, fields, _
from odoo.tools.misc import format_date

# ====================================================================================
# Description

# Product – Select a service product (overheads or Labour).
# This will give the flexibility to add more labour/service components as standard costs to the BoM.
# Only Service Products will be allowed to be selected here.

# Standard Cost – By default, the Cost of the product selected will be picked up, with the option to override.
# ====================================================================================
class IaProductTemplate(models.Model):
    _inherit = 'product.template'
    @api.depends('bom_ids.labour_cost')
    def _compute_labour_cost(self):
        for product in self:
            labour_cost = 0.0
            product_bom_ids = product.bom_ids.filtered(lambda bom: bom.type == 'normal')
            for bom in product_bom_ids:                
                labour_cost = labour_cost + bom.labour_cost             
            product.labour_cost = labour_cost 
            product.total_product_cost =  labour_cost + product.standard_price


    labour_cost = fields.Float(string = 'Labour + Overhead + Freight', compute = "_compute_labour_cost", digits=(12,4))

    # freight_cost = fields.Float(string = 'Freight Cost', digits=(12,4))

    total_product_cost = fields.Float(string = 'Total Product Cost', compute = "_compute_labour_cost", digits=(12,4))

class StockQuant(models.Model):
    _inherit = 'stock.quant'

    @api.depends('company_id', 'location_id', 'owner_id', 'product_id', 'quantity')
    def _compute_product_value(self):       
        for quant in self:           
            quant.product_value = quant.quantity * quant.product_id.with_company(quant.company_id).total_product_cost

    product_value = fields.Monetary('Total Product Cost', compute='_compute_product_value', groups='stock.group_stock_manager')
# class IaProductProduct(models.Model):
#     _inherit = 'product.product'

#     def _compute_labour_cost(self):
#         for product in self:
#             labour_cost = 0.0

#             for bom in product.bom_ids.filtered(lambda bom: bom.type == 'normal'):
#                 for cost in bom.cost_line_ids:
#                     labour_cost = labour_cost + cost.standard_cost
#                 for bom_line in bom.bom_line_ids:
#                     for product in bom_line.bom_ids.filtered(lambda bom: bom.type == 'normal'):
#                          labour_cost = labour_cost + cost.standard_cost
#             product.labour_cost = labour_cost 
#             product.total_product_cost = product.freight_cost + labour_cost + product.standard_price


#     labour_cost = fields.Float(string = 'Labour Cost', compute = "_compute_labour_cost", digits=(12,4))

#     freight_cost = fields.Float(string = 'Freight Cost', digits=(12,4))

#     total_product_cost = fields.Float(string = 'Total Product Cost', compute = "_compute_labour_cost", digits=(12,4))



