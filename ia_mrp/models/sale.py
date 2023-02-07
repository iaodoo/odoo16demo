from odoo import models, api, fields, _
from odoo.tools.misc import format_date

class SaleOrder(models.Model):
    _inherit= "sale.order"

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()  
        if self.analytic_account_id:     
            procurement_groups = self.env['procurement.group'].search([('sale_id', 'in', self.ids)])
            if procurement_groups:
                self.procurement_group_id.stock_move_ids.created_production_id.procurement_group_id.mrp_production_ids.write({'account_analytic_id' : self.analytic_account_id.id})
